
from __future__ import annotations
import os, time, argparse, hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.neighbors import NearestNeighbors

import folium
from folium.plugins import HeatMap
from branca.colormap import LinearColormap

from data_loader import carregar_e_preparar_dados, normalize_header
from config import (
    PLACES_TYPES_BY_NICHE,
    SEARCH_RADII as RADII,
    CLASS_ORDINAL as CLASSE_ORD,
    CACHE_CONFIG,
    PLACES_API_CONFIG,
)

# =========================
# CONFIG
# =========================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("⚠️  GOOGLE_API_KEY não encontrada no .env - funcionalidades de POI desabilitadas")

# Fallback genérico (usado se nicho não especificado)
PLACES_TYPES: Dict[str, List[str]] = PLACES_TYPES_BY_NICHE["Outro"]

# Cache local das consultas à API (para economizar cota)
CACHE_PATH = Path(CACHE_CONFIG["cache_file"])
CACHE_MAX_AGE_SECONDS = int(CACHE_CONFIG.get("max_age_days", 30)) * 86400

# =========================
# UTIL
# =========================
def hkey(lat: float, lon: float, place_type: str, radius: int) -> str:
    s = f"{round(float(lat),6)}|{round(float(lon),6)}|{place_type}|{radius}"
    return hashlib.md5(s.encode()).hexdigest()

def load_cache() -> pd.DataFrame:
    """Carrega cache de POIs aplicando TTL configurado em CACHE_CONFIG."""
    if not CACHE_PATH.exists():
        return pd.DataFrame(columns=["h", "lat", "lon", "type", "radius", "count", "ts"])
    df = pd.read_parquet(CACHE_PATH)
    if "ts" in df.columns and CACHE_MAX_AGE_SECONDS > 0:
        agora = int(time.time())
        antes = len(df)
        df = df[(agora - df["ts"].astype("int64")) <= CACHE_MAX_AGE_SECONDS].copy()
        descartados = antes - len(df)
        if descartados > 0:
            print(f"♻️  Cache: {descartados} entradas expiradas removidas (TTL={CACHE_MAX_AGE_SECONDS // 86400}d)")
    return df

def save_cache(df: pd.DataFrame) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CACHE_PATH, index=False)

def create_session_with_retry() -> requests.Session:
    """Cria sessão HTTP com retry automático."""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# =========================
# GOOGLE PLACES (API v1 — POST /v1/places:searchNearby)
# =========================
# Migração Legacy → v1:
# - Endpoint: POST https://places.googleapis.com/v1/places:searchNearby
# - Headers: X-Goog-Api-Key + X-Goog-FieldMask
# - Body JSON: includedTypes, maxResultCount (max 20), locationRestriction.circle
# - Filtro pós-resposta: businessStatus == OPERATIONAL
# Validado em docs/RESPOSTA_GEMINI.md (deep search Gemini)

_PLACES_V1_URL = "https://places.googleapis.com/v1/places:searchNearby"
_PLACES_V1_FIELD_MASK_COUNT = "places.id,places.businessStatus"
_PLACES_V1_FIELD_MASK_NAMES = (
    "places.id,places.displayName,places.businessStatus,"
    "places.userRatingCount,places.rating"
)
_GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json"

# Cache em memória de reverse geocoding (por sessão — evita chamadas repetidas)
_geocode_cache: dict[str, str] = {}


def reverse_geocode_bairro(lat: float, lon: float, session: requests.Session) -> str:
    """
    Usa a Google Geocoding API para obter o nome do bairro (sublocality_level_1
    ou neighborhood) a partir de coordenadas.

    Retorna o nome do bairro em pt-BR, ou 'Fortaleza' como fallback.
    Usa cache em memória para evitar chamadas duplicadas na mesma sessão.
    """
    if not API_KEY:
        return "Fortaleza"

    cache_key = f"{round(lat, 4)}|{round(lon, 4)}"
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    try:
        r = session.get(
            _GEOCODING_URL,
            params={
                "latlng": f"{lat},{lon}",
                "key": API_KEY,
                "language": "pt-BR",
                "result_type": "sublocality|neighborhood",
            },
            timeout=4,
        )
        r.raise_for_status()
        data = r.json()

        bairro = "Fortaleza"
        if data.get("status") == "OK" and data.get("results"):
            # Percorre componentes do primeiro resultado buscando bairro
            for component in data["results"][0].get("address_components", []):
                types = component.get("types", [])
                if "sublocality_level_1" in types or "neighborhood" in types:
                    bairro = component["long_name"]
                    break
            # Fallback: usa locality (cidade) se não achou bairro
            if bairro == "Fortaleza":
                for component in data["results"][0].get("address_components", []):
                    if "administrative_area_level_4" in component.get("types", []):
                        bairro = component["long_name"]
                        break

        _geocode_cache[cache_key] = bairro
        return bairro

    except Exception as e:
        print(f"⚠️  Reverse geocoding falhou ({lat:.4f},{lon:.4f}): {e}")
        return "Fortaleza"


def _places_v1_request(
    lat: float,
    lon: float,
    place_type: str | list,
    radius: int,
    session: requests.Session,
    field_mask: str,
    max_results: int = 20,
) -> list:
    """
    Faz POST /v1/places:searchNearby e retorna lista de places (já filtrada
    para businessStatus == OPERATIONAL). Em caso de erro, retorna [].

    place_type pode ser str (tipo único) ou list (batch de tipos — a API v1
    aceita includedTypes como array, reduzindo o número de requisições).
    """
    if not API_KEY:
        return []

    included_types = [place_type] if isinstance(place_type, str) else list(place_type)

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": field_mask,
    }
    body = {
        "includedTypes": included_types,
        "maxResultCount": min(max(max_results, 1), 20),  # v1: hard limit 20
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lon},
                "radius": float(radius),
            }
        },
    }

    try:
        r = session.post(_PLACES_V1_URL, headers=headers, json=body, timeout=3)

        if r.status_code in (429, 500, 502, 503):
            print(f"⚠️  Places v1 status {r.status_code} para types={included_types}")
            return []
        if r.status_code == 403:
            print("❌ Places v1 403 — verifique se a Places API (New) está habilitada")
            return []
        r.raise_for_status()

        data = r.json()
        places = data.get("places", []) or []
        # Filtra apenas estabelecimentos operacionais (Gemini Q9)
        return [
            p for p in places
            if p.get("businessStatus", "OPERATIONAL") == "OPERATIONAL"
        ]
    except requests.exceptions.Timeout:
        print(f"⚠️  Timeout Places v1 (types={included_types}, r={radius}m)")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro Places v1: {str(e)}")
        return []
    except Exception as e:
        print(f"❌ Erro inesperado Places v1: {str(e)}")
        return []


def nearby_count(lat: float, lon: float, place_type: str | list, radius: int, session: requests.Session) -> int:
    """
    Conta POIs via Google Places API v1 (POST searchNearby).
    place_type pode ser str ou list (batch) — v1 suporta includedTypes como array.
    Retorna nº de estabelecimentos OPERATIONAL no raio. Limite v1: 20/chamada.
    """
    if not API_KEY:
        return 0
    places = _places_v1_request(
        lat, lon, place_type, radius, session,
        field_mask=_PLACES_V1_FIELD_MASK_COUNT,
        max_results=20,
    )
    return len(places)


def nearby_names(lat: float, lon: float, place_type: str | list, radius: int, session: requests.Session, max_results: int = 5) -> list:
    """Retorna nomes de estabelecimentos próximos via Google Places API v1."""
    if not API_KEY:
        return []
    places = _places_v1_request(
        lat, lon, place_type, radius, session,
        field_mask=_PLACES_V1_FIELD_MASK_NAMES,
        max_results=max_results,
    )
    names = []
    for p in places[:max_results]:
        # v1: displayName é objeto { text, languageCode }
        dn = p.get("displayName") or {}
        name = dn.get("text") if isinstance(dn, dict) else dn
        if name:
            names.append(name)
    return names


def enrich_row_with_pois(row: pd.Series, cache_df: pd.DataFrame, session: requests.Session, nicho: str = "Outro") -> Tuple[Dict[str,int], List[dict]]:
    """Enriquece uma linha com POIs específicos do nicho, usando cache quando disponível.

    Otimizações aplicadas:
    - Batching: todos os tipos de um rótulo são enviados em UMA única requisição
      (includedTypes aceita array na API v1), reduzindo 3-5x o nº de chamadas.
    - Paralelização: as chamadas (label × radius) que não estão em cache são
      executadas em paralelo via ThreadPoolExecutor(max_workers=8).
    """
    try:
        lat, lon = float(row["lat"]), float(row["lon"])
        places_types = PLACES_TYPES_BY_NICHE.get(nicho, PLACES_TYPES_BY_NICHE["Outro"])

        # ── 1. Separa hits de cache dos misses ─────────────────────────────
        # Chave de cache: hash do conjunto de tipos (ordenado) + raio
        def _hkey_batch(types_list: list, radius: int) -> str:
            key = f"{round(lat,6)}|{round(lon,6)}|{'_'.join(sorted(types_list))}|{radius}"
            return hashlib.md5(key.encode()).hexdigest()

        tasks: list[tuple] = []   # (label, radius, types, hk)
        results: Dict[str, int] = {}
        new_records: List[dict] = []

        for label, types in places_types.items():
            for radius in RADII:
                col = f"poi_{label}_{radius}m"
                hk = _hkey_batch(types, radius)
                cached = cache_df.loc[cache_df["h"] == hk]
                if not cached.empty:
                    results[col] = int(cached.iloc[0]["count"])
                else:
                    tasks.append((label, radius, types, hk, col))

        if not tasks:
            return results, new_records

        # ── 2. Chamadas em paralelo para os misses ──────────────────────────
        def _fetch(label: str, radius: int, types: list, hk: str, col: str):
            cnt = nearby_count(lat, lon, types, radius, session)
            return label, radius, types, hk, col, cnt

        max_workers = min(8, len(tasks))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_fetch, *task): task for task in tasks}
            for future in as_completed(futures):
                try:
                    label, radius, types, hk, col, cnt = future.result()
                    results[col] = cnt
                    new_records.append({
                        "h": hk,
                        "lat": lat,
                        "lon": lon,
                        "type": "_".join(sorted(types)),
                        "radius": radius,
                        "count": cnt,
                        "ts": int(time.time()),
                    })
                except Exception as e:
                    task = futures[future]
                    col = task[4]
                    print(f"  ⚠️ Erro na task {col}: {e}")
                    results[col] = 0

        return results, new_records

    except Exception as e:
        print(f"❌ Erro ao enriquecer linha: {str(e)}")
        results = {}
        for label in PLACES_TYPES_BY_NICHE.get(nicho, PLACES_TYPES_BY_NICHE["Outro"]):
            for radius in RADII:
                results[f"poi_{label}_{radius}m"] = 0
        return results, []

# =========================
# FEATURE ENGINEERING
# =========================
def ensure_columns(df: pd.DataFrame, cols: List[str]):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {missing}")

def build_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """Cria features para clustering:
       - classe_ord (A=5..E=1)
       - tipo_comercial (one-hot)
       - poi_* normalizados 0–1
    """
    df = df.copy()
    
    # OTIMIZADO: Processamento vetorizado
    df["classe_ord"] = df["classe"].astype(str).str.upper().map(CLASSE_ORD).fillna(0).astype(int)
    df["tipo_comercial"] = df["tipo_comercial"].astype(str).str.upper().fillna("OUTROS")

    # Normalização vetorizada de POIs (muito mais rápido)
    poi_cols = [c for c in df.columns if c.startswith("poi_") and c.endswith("m")]
    if poi_cols:
        # Converte para numérico de uma vez
        df[poi_cols] = df[poi_cols].fillna(0).astype(float)
        # Normaliza todos de uma vez (muito mais rápido que loop)
        poi_values = df[poi_cols].values
        mins = poi_values.min(axis=0)
        maxs = poi_values.max(axis=0)
        ranges = maxs - mins
        # Evita divisão por zero
        ranges[ranges == 0] = 1
        normalized = (poi_values - mins) / ranges
        # Cria colunas normalizadas
        for i, c in enumerate(poi_cols):
            df[c + "_norm"] = normalized[:, i]

    poi_norm_cols = [c for c in df.columns if c.startswith("poi_") and c.endswith("_norm")]
    num_cols = ["classe_ord"] + poi_norm_cols
    cat_cols = ["tipo_comercial"]

    # Adiciona coordenadas geográficas quando POIs não têm dados reais.
    # Isso garante que o KMeans crie clusters espacialmente distintos (por bairro)
    # mesmo sem a Google Places API, em vez de agrupar só por classe social.
    if "lat" in df.columns and "lon" in df.columns:
        poi_raw_cols = [c for c in df.columns if c.startswith("poi_") and c.endswith("m") and not c.endswith("_norm")]
        poi_data_sum = float(df[poi_raw_cols].sum().sum()) if poi_raw_cols else 0.0
        if poi_data_sum == 0.0:
            for coord in ["lat", "lon"]:
                vmin, vmax = float(df[coord].min()), float(df[coord].max())
                denom = vmax - vmin
                df[f"{coord}_feat"] = ((df[coord] - vmin) / denom) if denom > 1e-8 else 0.0
            # Cria cópia das features com nome diferente para simular peso 2×
            # (ColumnTransformer exige nomes de coluna únicos)
            df["lat_feat2"] = df["lat_feat"]
            df["lon_feat2"] = df["lon_feat"]
            num_cols = num_cols + ["lat_feat", "lon_feat", "lat_feat2", "lon_feat2"]

    num_cols = [c for c in num_cols if c in df.columns]
    cat_cols  = [c for c in cat_cols  if c in df.columns]
    return df, num_cols, cat_cols

# =========================
# CLUSTERING
# =========================
def fit_kmeans(X: np.ndarray, n_clusters: int, random_state: int = 42) -> KMeans:
    # OTIMIZADO: n_init reduzido de 20 para 5 (4x mais rápido)
    km = KMeans(n_clusters=n_clusters, n_init=5, max_iter=100, random_state=random_state)
    km.fit(X)
    return km


# =========================
# MÉTRICAS DE AVALIAÇÃO
# =========================
def calcular_metricas_clustering(X: np.ndarray, labels: np.ndarray) -> Dict:
    """
    Calcula métricas de qualidade do clustering para avaliação acadêmica.

    - Silhouette Score  : [-1, 1]. Quanto mais próximo de 1, melhor a separação.
    - Davies-Bouldin    : [0, ∞). Quanto menor, mais compactos e separados os clusters.
    - Inertia (SSE)     : soma dos quadrados intra-cluster (base do Elbow Method).

    Returns:
        dict com as métricas calculadas
    """
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    resultado = {"n_clusters": int(n_clusters)}

    if n_clusters < 2 or X.shape[0] <= n_clusters:
        resultado.update({"silhouette": None, "davies_bouldin": None, "inertia": None})
        return resultado

    # Ignora pontos de ruído do DBSCAN (label == -1)
    mascara = labels != -1
    if mascara.sum() <= n_clusters:
        resultado.update({"silhouette": None, "davies_bouldin": None, "inertia": None})
        return resultado

    X_limpo = X[mascara]
    labels_limpo = labels[mascara]

    try:
        sil = float(silhouette_score(X_limpo, labels_limpo, sample_size=min(500, len(X_limpo))))
        resultado["silhouette"] = round(sil, 4)
    except Exception:
        resultado["silhouette"] = None

    try:
        db = float(davies_bouldin_score(X_limpo, labels_limpo))
        resultado["davies_bouldin"] = round(db, 4)
    except Exception:
        resultado["davies_bouldin"] = None

    resultado["inertia"] = None
    return resultado


def calcular_elbow(X: np.ndarray, k_range: range = range(2, 7)) -> Dict:
    """
    Executa o Elbow Method calculando inércia para diferentes valores de k.
    Usado para justificar academicamente a escolha do número de clusters.

    Returns:
        dict {k: inertia} para cada k testado
    """
    elbow = {}
    for k in k_range:
        if X.shape[0] <= k:
            break
        km = KMeans(n_clusters=k, n_init=5, max_iter=100, random_state=42)
        km.fit(X)
        elbow[int(k)] = round(float(km.inertia_), 2)
    return elbow


def _knee_point(elbow: Dict[int, float]) -> int:
    """
    Detecta o cotovelo ótimo da curva de inércia pelo método de máxima distância.

    Para cada k, calcula a distância perpendicular entre o ponto e a linha
    que une o primeiro e o último ponto da curva. O k com maior distância
    é o cotovelo ideal (máxima variação de curvatura).

    Referência: Satopää, 1984 — "Finding a 'Kneedle' in a Haystack"
    """
    if len(elbow) < 3:
        return min(elbow.keys())
    ks = sorted(elbow.keys())
    inertias = [elbow[k] for k in ks]
    # Normaliza para [0, 1]
    i_min, i_max = min(inertias), max(inertias)
    if i_max == i_min:
        return ks[0]
    norm_y = [(v - i_min) / (i_max - i_min) for v in inertias]
    norm_x = [(k - ks[0]) / (ks[-1] - ks[0]) for k in ks]
    # Distância de cada ponto à reta entre primeiro e último ponto
    x0, y0 = norm_x[0], norm_y[0]
    x1, y1 = norm_x[-1], norm_y[-1]
    dx, dy = x1 - x0, y1 - y0
    dists = [
        abs(dy * (norm_x[i] - x0) - dx * (norm_y[i] - y0))
        for i in range(len(ks))
    ]
    return ks[dists.index(max(dists))]


def estimar_eps_dbscan(X: np.ndarray, min_samples: int = 5) -> float:
    """
    Estima o parâmetro eps do DBSCAN pelo método k-NN (cotovelo da curva
    de distâncias ao k-ésimo vizinho mais próximo).

    Referência: Ester et al. (1996) — artigo original do DBSCAN.
    """
    k = min(min_samples, X.shape[0] - 1)
    nbrs = NearestNeighbors(n_neighbors=k).fit(X)
    distancias, _ = nbrs.kneighbors(X)
    distancias_sorted = np.sort(distancias[:, -1])
    # Retorna o valor no "cotovelo" (~85º percentil)
    eps = float(np.percentile(distancias_sorted, 85))
    return max(eps, 0.05)   # mínimo 0.05 para evitar eps=0


def comparar_kmeans_dbscan(X: np.ndarray, n_clusters: int) -> Dict:
    """
    Compara KMeans vs DBSCAN e retorna o melhor algoritmo com justificativa.

    Critério: Silhouette Score (maior = melhor separação de clusters).
    Em caso de empate ou DBSCAN sem clusters válidos, KMeans é preferido
    por ser mais determinístico e interpretável.

    Returns:
        {
          "melhor_algoritmo": str,
          "justificativa": str,
          "kmeans": {silhouette, davies_bouldin, n_clusters},
          "dbscan": {silhouette, davies_bouldin, n_clusters, eps, min_samples},
          "labels_escolhidos": np.ndarray
        }
    """
    # --- KMeans ---
    km = fit_kmeans(X, n_clusters)
    labels_km = km.labels_
    metricas_km = calcular_metricas_clustering(X, labels_km)
    metricas_km["inertia"] = round(float(km.inertia_), 2)

    # --- DBSCAN ---
    min_samples = max(3, X.shape[0] // 20)
    eps = estimar_eps_dbscan(X, min_samples)
    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels_db = db.fit_predict(X)
    n_clusters_db = len(set(labels_db)) - (1 if -1 in labels_db else 0)
    metricas_db = calcular_metricas_clustering(X, labels_db)
    metricas_db.update({"eps": round(eps, 4), "min_samples": int(min_samples)})

    # --- Decisão ---
    sil_km = metricas_km.get("silhouette") or -1
    sil_db = metricas_db.get("silhouette") or -1

    # Detecta clusters triviais do DBSCAN (clusters com 1 ponto têm silhouette=1 automaticamente)
    labels_db_validos = labels_db[labels_db != -1]
    n_noise = int(np.sum(labels_db == -1))
    cobertura = len(labels_db_validos) / len(labels_db) if len(labels_db) > 0 else 0
    if len(labels_db_validos) > 0:
        _, contagens = np.unique(labels_db_validos, return_counts=True)
        media_cluster = float(np.mean(contagens))
        cluster_trivial = media_cluster < 3 or cobertura < 0.60  # < 60% cobertura = muito ruído
    else:
        cluster_trivial = True

    if n_clusters_db < 2 or cluster_trivial:
        melhor = "KMeans"
        if cluster_trivial:
            justificativa = (
                f"DBSCAN cobriu apenas {cobertura*100:.0f}% dos dados como clusters "
                f"(eps={eps:.3f}, {n_noise} pontos de ruído). "
                f"KMeans selecionado por melhor cobertura geográfica."
            )
        else:
            justificativa = (
                f"DBSCAN não formou clusters válidos (eps={eps:.3f}, "
                f"min_samples={min_samples}). KMeans selecionado."
            )
        labels_finais = labels_km
    elif sil_db > sil_km + 0.05:
        melhor = "DBSCAN"
        justificativa = (
            f"DBSCAN obteve Silhouette={sil_db:.3f} vs KMeans={sil_km:.3f} "
            f"(+{sil_db - sil_km:.3f}). DBSCAN selecionado."
        )
        labels_finais = labels_db
    else:
        melhor = "KMeans"
        justificativa = (
            f"KMeans (Silhouette={sil_km:.3f}) equivalente ou superior a "
            f"DBSCAN (Silhouette={sil_db:.3f}). KMeans preferido por "
            f"interpretabilidade e clusters balanceados."
        )
        labels_finais = labels_km

    print(f"\n📊 Comparação de algoritmos:")
    print(f"   KMeans  → Silhouette={sil_km:.3f}, Davies-Bouldin={metricas_km.get('davies_bouldin', '?')}")
    print(f"   DBSCAN  → Silhouette={sil_db:.3f}, clusters={n_clusters_db}, eps={eps:.3f}")
    print(f"   ✓ Selecionado: {melhor} — {justificativa}")

    return {
        "melhor_algoritmo": melhor,
        "justificativa": justificativa,
        "kmeans": metricas_km,
        "dbscan": metricas_db,
        "labels_escolhidos": labels_finais,
    }

def get_pesos_score_por_nicho(nicho: str):
    # Pesos dinâmicos por nicho — (peso_poi, peso_classe)
    pesos = {
        "Infantil":    (0.8, 0.2),
        "Fitness":     (0.7, 0.3),
        "Escolar":     (0.7, 0.3),
        "Alimentação": (0.6, 0.4),
        "Farmácia":    (0.6, 0.4),
        "Beleza":      (0.5, 0.5),
        "Pet":         (0.7, 0.3),
        "Eletrônicos": (0.6, 0.4),
        "Saúde":       (0.6, 0.4),  # Serviços de saúde: POI relevante + classe social
        "Outro":       (0.6, 0.4),
    }
    return pesos.get(nicho, (0.6, 0.4))

def rank_clusters(df_feat: pd.DataFrame, labels: np.ndarray, nicho: str = "Outro") -> pd.DataFrame:
    """Ranking por potencial com pesos dinâmicos por nicho."""
    tmp = df_feat.copy()
    tmp["cluster"] = labels
    # Exclui pontos de ruído do DBSCAN (label == -1)
    tmp = tmp[tmp["cluster"] != -1]
    if tmp.empty:
        return pd.DataFrame(columns=["cluster","classe_med","poi_med","score_potencial","ordem"])
    poi_norm_cols = [c for c in tmp.columns if c.startswith("poi_") and c.endswith("_norm")]
    
    # Agrega classe média
    agg = tmp.groupby("cluster").agg(
        classe_med=("classe_ord", "mean")
    )
    
    # Calcula média de POIs se existirem
    if poi_norm_cols:
        agg["poi_med"] = tmp.groupby("cluster")[poi_norm_cols].mean().mean(axis=1)
    else:
        agg["poi_med"] = 0.0
    peso_poi, peso_classe = get_pesos_score_por_nicho(nicho)
    agg["score_potencial"] = peso_poi*agg["poi_med"] + peso_classe*(agg["classe_med"]/5.0)
    agg = agg.sort_values("score_potencial", ascending=False).reset_index()
    agg["ordem"] = np.arange(1, len(agg)+1)
    return agg[["cluster","classe_med","poi_med","score_potencial","ordem"]]


# Armazena métricas da última execução para acesso pela API
_last_clustering_metrics: Dict = {}

# =========================
# GRID FORTALEZA (Places API)
# =========================
# 30 pontos estratégicos cobrindo os principais bairros de Fortaleza.
# Grid fixo (passo ~3 km) garante resposta em <15s com 20 workers paralelos.
# Os pontos foram escolhidos para cobrir tanto o litoral (bairros nobres)
# quanto o interior (bairros populares com alto volume comercial).
_FTZ_GRID_PONTOS = [
    # Litoral Leste / Zona Nobre
    (-3.7200, -38.5010),  # Meireles / Iracema
    (-3.7240, -38.4850),  # Mucuripe / Coco
    (-3.7400, -38.5020),  # Aldeota
    (-3.7440, -38.4860),  # Papicu
    (-3.7560, -38.4750),  # Edson Queiroz
    (-3.7680, -38.4730),  # Salinas
    # Centro Expandido
    (-3.7200, -38.5430),  # Centro
    (-3.7350, -38.5300),  # Benfica / São Gerardo
    (-3.7550, -38.5450),  # Fátima / Damas
    (-3.7680, -38.5300),  # Jóquei Clube / Montese
    (-3.7450, -38.5600),  # Antônio Bezerra / Otávio Bonfim
    (-3.7300, -38.5700),  # Barra do Ceará / Cristo Redentor
    # Zona Sul / Interior
    (-3.7850, -38.5100),  # Maraponga / Canindezinho
    (-3.7900, -38.5400),  # Parangaba / Mondubim
    (-3.8050, -38.5600),  # Conjunto Ceará
    (-3.8150, -38.4950),  # Messejana
    (-3.7960, -38.4850),  # Alagadiço / Dendê
    (-3.8000, -38.5200),  # José Walter
    # Zona Oeste
    (-3.7500, -38.5900),  # Autran Nunes / Henrique Jorge
    (-3.7700, -38.5700),  # Granja Lisboa / Granja Portugal
    (-3.7600, -38.6100),  # Bom Jardim / Siqueira
    (-3.7850, -38.5950),  # Araturi / Novo Mondubim
    # Zona Leste / Praia do Futuro
    (-3.7550, -38.4550),  # Praia do Futuro
    (-3.7800, -38.4700),  # Sabiaguaba
    # Pontos extras para melhor cobertura
    (-3.7650, -38.5150),  # Amadeu Furtado / Joaquim Távora
    (-3.7300, -38.5150),  # Varjota / Dionísio Torres
    (-3.7100, -38.5250),  # Pirambu / Moura Brasil
    (-3.7950, -38.5750),  # Bom Sucesso / Prefeito José Walter
    (-3.7600, -38.5350),  # Parreão / João XXIII
    (-3.8100, -38.5350),  # Guajeru / Planalto Ayrton Senna
]


def buscar_grid_fortaleza(nicho: str, session: requests.Session) -> pd.DataFrame:
    """
    Mapeia os principais bairros de Fortaleza via Google Places API v1.

    Para cada um dos 30 pontos estratégicos da grade, conta quantos POIs do
    nicho existem num raio de 800 m (Calthorpe 1993 — ~10 min a pé).

    A densidade de POIs funciona como proxy da demanda/fluxo local:
    onde há muitos estabelecimentos congêneres, há público-alvo.

    Retorna DataFrame com colunas [lat, lon, poi_count], apenas pontos com
    poi_count > 0 (pontos "ativos" para o nicho).
    """
    if not API_KEY:
        print("❌ GOOGLE_API_KEY não configurada — busca em grade requer a API")
        return pd.DataFrame(columns=["lat", "lon", "poi_count"])

    places_types = PLACES_TYPES_BY_NICHE.get(nicho, PLACES_TYPES_BY_NICHE["Outro"])
    all_types = list({t for types_list in places_types.values() for t in types_list})

    print(f"🗺️  Grade Fortaleza: {len(_FTZ_GRID_PONTOS)} pontos | "
          f"nicho='{nicho}' | tipos: {all_types}")

    def _fetch(lat_lon: tuple) -> dict:
        lat, lon = lat_lon
        try:
            places = _places_v1_request(
                lat, lon, all_types, 800, session,
                field_mask=_PLACES_V1_FIELD_MASK_COUNT,
                max_results=20,
            )
            cnt = len(places)
            if cnt > 0:
                print(f"  ✓ ({lat:.4f},{lon:.4f}) → {cnt} POIs")
            return {"lat": lat, "lon": lon, "poi_count": cnt}
        except Exception as exc:
            print(f"  ⚠ ({lat:.4f},{lon:.4f}) erro: {exc}")
            return {"lat": lat, "lon": lon, "poi_count": 0}

    # 20 workers para 30 pontos → ~2 rodadas de chamadas paralelas (~6–10s)
    with ThreadPoolExecutor(max_workers=20) as pool:
        resultados = list(pool.map(_fetch, _FTZ_GRID_PONTOS))

    df = pd.DataFrame(resultados)
    n_ativos = int((df["poi_count"] > 0).sum())
    poi_max = int(df["poi_count"].max()) if not df.empty else 0
    print(f"✓ {n_ativos} pontos ativos (de {len(_FTZ_GRID_PONTOS)}) | "
          f"máx POIs/ponto: {poi_max}")
    return df[df["poi_count"] > 0].copy().reset_index(drop=True)


def gerar_regioes_ideais_com_metricas(produto: str, filtros: dict, nicho: str = None) -> Tuple[list, Dict]:
    """
    Versão estendida de gerar_regioes_ideais() que também retorna
    as métricas de clustering (Silhouette, Davies-Bouldin, Elbow, comparação).

    Returns:
        (regioes, metricas)
    """
    regioes = gerar_regioes_ideais(produto, filtros, nicho)
    metricas = dict(_last_clustering_metrics)
    return regioes, metricas


def gerar_regioes_ideais(produto: str, filtros: dict, nicho: str = None) -> list:
    """
    Gera regiões ideais para abertura de negócio via Google Places API.

    Abordagem: busca em grade uniforme sobre Fortaleza — para cada ponto da
    grade, conta POIs relevantes ao nicho num raio de 800 m. Os pontos com
    maior densidade de POIs são clusterizados e os candidatos de cada zona
    têm o bairro obtido por reverse geocoding (sem dependência de Excel).

    Retorna lista de dicts: [{lat, lon, nome, motivo, cluster, score, poi_med}]
    """
    try:
        global _last_clustering_metrics
        _metricas_finais: Dict = {}

        from nlp import identificar_nicho
        if nicho is None:
            nicho = identificar_nicho(produto)

        if not API_KEY:
            print("❌ GOOGLE_API_KEY não configurada — análise requer a API")
            return []

        sess = create_session_with_retry()

        # ── 1. Busca POIs em grade sobre Fortaleza ──────────────────────────
        df_grid = buscar_grid_fortaleza(nicho, sess)

        if len(df_grid) < 6:
            print(f"⚠️  Apenas {len(df_grid)} pontos com POIs retornados.")
            print("   Causas prováveis: chave da API sem 'Places API (New)' habilitada,")
            print("   quota esgotada, ou todos os tipos de POI sem resultados na cidade.")
            print("   Verifique GOOGLE_API_KEY no Railway e habilite 'Places API (New)'.")
            return []

        # ── 2. Features para clustering (coordenadas + densidade de POIs) ──
        poi_max = float(df_grid["poi_count"].max())
        df_grid["poi_norm"] = df_grid["poi_count"] / poi_max

        # Coordenadas com peso duplo para clustering espacialmente coerente
        X_raw = np.column_stack([
            df_grid["lat"].values,
            df_grid["lon"].values,
            df_grid["lat"].values,
            df_grid["lon"].values,
            df_grid["poi_norm"].values,
        ])
        X = StandardScaler().fit_transform(X_raw)

        # ── 3. Clustering ───────────────────────────────────────────────────
        n_clusters_max = min(6, max(3, len(df_grid) // 10))
        elbow_data = calcular_elbow(X, k_range=range(2, n_clusters_max + 2))
        n_clusters = min(_knee_point(elbow_data), n_clusters_max)
        print(f"  ✓ Elbow: k={n_clusters} (max={n_clusters_max})")

        comparacao = comparar_kmeans_dbscan(X, n_clusters=n_clusters)
        labels = comparacao["labels_escolhidos"]

        _metricas_finais = {
            "algoritmo": comparacao["melhor_algoritmo"],
            "justificativa": comparacao["justificativa"],
            "silhouette": comparacao[
                "kmeans" if comparacao["melhor_algoritmo"] == "KMeans" else "dbscan"
            ].get("silhouette"),
            "davies_bouldin": comparacao[
                "kmeans" if comparacao["melhor_algoritmo"] == "KMeans" else "dbscan"
            ].get("davies_bouldin"),
            "kmeans": comparacao["kmeans"],
            "dbscan": comparacao["dbscan"],
            "elbow": elbow_data,
        }

        df_grid["cluster"] = labels
        df_grid = df_grid[df_grid["cluster"] != -1].copy()   # remove ruído DBSCAN

        # ── 4. Ranking de clusters por densidade média de POIs ──────────────
        cluster_scores = (
            df_grid.groupby("cluster")["poi_count"]
            .mean()
            .sort_values(ascending=False)
        )
        n_total_clusters = len(cluster_scores)
        print(f"\n📊 {n_total_clusters} zonas | score (POI médio): "
              f"{cluster_scores.round(1).to_dict()}")

        # ── 5. Top 3 candidatos por cluster (pontos com mais POIs) ──────────
        CANDIDATOS_POR_CLUSTER = 3
        todos_candidatos: list = []

        for rank_zona, (cluster_id, score_medio) in enumerate(cluster_scores.items(), 1):
            subset = (
                df_grid[df_grid["cluster"] == cluster_id]
                .drop_duplicates(subset=["lat", "lon"])
                .sort_values("poi_count", ascending=False)
            )
            candidatos = subset.head(CANDIDATOS_POR_CLUSTER)
            score_100 = round(min(score_medio / poi_max * 100, 100.0), 1)

            for rank_local, (_, row) in enumerate(candidatos.iterrows(), 1):
                todos_candidatos.append({
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "cluster_id": int(cluster_id),
                    "rank_zona": rank_zona,
                    "rank_local": rank_local,
                    "poi_count": int(row["poi_count"]),
                    "score_100": score_100,
                    "n_membros": len(subset),
                })

        # ── 6. Reverse geocoding de todos os candidatos em paralelo ─────────
        def _geocode_cand(cand: dict) -> dict:
            bairro = reverse_geocode_bairro(cand["lat"], cand["lon"], sess)
            return {**cand, "bairro": bairro}

        with ThreadPoolExecutor(max_workers=min(8, max(1, len(todos_candidatos)))) as pool:
            candidatos_geo = list(pool.map(_geocode_cand, todos_candidatos))

        # ── 7. Monta lista de regiões ────────────────────────────────────────
        regioes: list = []
        for cand in candidatos_geo:
            motivo_parts = [
                f"🏆 Zona #{cand['rank_zona']} de {n_total_clusters} · "
                f"Ponto {cand['rank_local']} de {CANDIDATOS_POR_CLUSTER}",
                f"📍 {cand['poi_count']} estabelecimentos relevantes num raio de 800 m",
                f"⭐ Score potencial: {cand['score_100']:.1f}/100",
            ]
            regioes.append({
                "lat": cand["lat"],
                "lon": cand["lon"],
                "nome": f"{cand['bairro']} — Zona {cand['rank_zona']}, opção {cand['rank_local']}",
                "motivo": " | ".join(motivo_parts),
                "cluster": cand["cluster_id"],
                "score": cand["score_100"],
                "classe_med": 0.0,
                "poi_med": float(cand["poi_count"]),
                "tipo_comercial": nicho,
                "classe_social": "N/A",
            })

        _last_clustering_metrics.update(_metricas_finais)
        print(f"\n✓ {len(regioes)} pontos candidatos em {n_total_clusters} zonas "
              f"({CANDIDATOS_POR_CLUSTER} por zona)")
        return regioes

    except Exception as e:
        print(f"❌ Erro em gerar_regioes_ideais: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

# =========================
# MAPA
# =========================
def cluster_colors(n: int) -> List[str]:
    base = ["#d73027", "#fc8d59", "#fee090", "#91bfdb", "#4575b4", "#1a9850", "#66bd63", "#f46d43"]
    if n <= len(base):
        return base[:n]
    return [base[i % len(base)] for i in range(n)]

def make_map(df_full: pd.DataFrame, cluster_rank: pd.DataFrame, out_html: str) -> str:
    center = (df_full["lat"].median(), df_full["lon"].median())
    m = folium.Map(location=center, zoom_start=12, tiles="cartodbpositron")

    dfm = df_full.merge(cluster_rank[["cluster","score_potencial","ordem"]], on="cluster", how="left")
    heat_vals = dfm[["lat","lon","score_potencial"]].dropna().values.tolist()
    if heat_vals:
        HeatMap(heat_vals, name="Heatmap (potencial por cluster)", min_opacity=0.3, radius=16, blur=14).add_to(m)

    colors = cluster_colors(dfm["cluster"].nunique())
    color_map = {c_idx: colors[i] for i, c_idx in enumerate(cluster_rank.sort_values("ordem")["cluster"])}

    for _, row in cluster_rank.sort_values("ordem").iterrows():
        c = int(row["cluster"])
        fg = folium.FeatureGroup(name=f"Cluster {c} (rank {int(row['ordem'])})", show=True)
        m.add_child(fg)
        sub = dfm[dfm["cluster"] == c]
        for _, r in sub.iterrows():
            popup = folium.Popup(
                f"""<b>{r['nome']}</b><br>
                Classe: {r['classe']} (ord={int(r['classe_ord'])})<br>
                Tipo: {r['tipo_comercial']}<br>
                Cluster: {c} (rank {int(row['ordem'])})<br>
                Score cluster: {row['score_potencial']:.2f}""",
                max_width=360
            )
            folium.CircleMarker(
                location=(r["lat"], r["lon"]),
                radius=6,
                fill=True,
                fill_opacity=0.9,
                color=color_map[c],
                fill_color=color_map[c],
                popup=popup,
                tooltip=f"{r['nome']} — C{c} (rank {int(row['ordem'])})"
            ).add_to(fg)

    cmap = LinearColormap(["#4575b4","#fee090","#d73027"],
                          vmin=float(cluster_rank["score_potencial"].min()),
                          vmax=float(cluster_rank["score_potencial"].max()))
    cmap.caption = "Potencial do cluster"
    cmap.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    m.save(out_html)
    return out_html

# =========================
# MAIN
# =========================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV de entrada (aceita ; ou ,)")
    parser.add_argument("--usar_api", default="false", choices=["true","false"], help="Usar Google Places? (default=false)")
    parser.add_argument("--n_clusters", type=int, default=3, help="Número de clusters KMeans")
    parser.add_argument("--out_prefix", default="clientes", help="Prefixo de arquivos de saída")
    args = parser.parse_args()

    usar_api = args.usar_api.lower() == "true"

    # 1) Leitura robusta (auto-detecção de separador + normalização de cabeçalhos)
    df = pd.read_csv(args.input, sep=None, engine="python", encoding="utf-8-sig")
    df.columns = [normalize_header(c) for c in df.columns]

    # Alias map de cabeçalhos reais -> nomes do pipeline
    alias_map = {
        "CLIENTE": "nome",
        "NOME": "nome",
        "REDE": "rede",
        "LAT": "lat",
        "LATITUDE": "lat",
        "LON": "lon",
        "LONGITUDE": "lon",
        "CLASSE SOCIAL": "classe",
        "CLASSE_SOCIAL": "classe",
        "CLASSE": "classe",
        "TIPO COMERCIAL": "tipo_comercial",
        "TIPO_COMERCIAL": "tipo_comercial",
        "TIPO": "tipo_comercial",
        "BAIRRO": "bairro",
        "CIDADE": "cidade",
    }

    # Converte colunas conhecidas
    rename_dict = {col: alias_map[col] for col in df.columns if col in alias_map}
    df = df.rename(columns=rename_dict)

    # Exige o núcleo mínimo
    ensure_columns(df, ["nome", "lat", "lon", "classe", "tipo_comercial"])

    # 2) Enriquecimento de POIs (opcional)
    cache = load_cache()
    if usar_api:
        if not API_KEY:
            raise SystemExit("Defina GOOGLE_API_KEY no .env para usar a API.")
        sess = requests.Session()
        all_new = []
        for i, row in df.iterrows():
            feats, new_records = enrich_row_with_pois(row, cache, sess)
            for k, v in feats.items():
                df.at[i, k] = v
            if new_records:
                all_new.extend(new_records)
            time.sleep(0.15)  # respeitar cota
        if all_new:
            cache = pd.concat([cache, pd.DataFrame(all_new)], ignore_index=True)
            save_cache(cache)
    else:
        # cria colunas zeradas p/ manter pipeline
        for label in PLACES_TYPES:
            for r in RADII:
                df[f"poi_{label}_{r}m"] = 0

    # 3) Salva base enriquecida
    enr_csv = f"{args.out_prefix}_enriquecidos.csv"
    df.to_csv(enr_csv, index=False)

    # 4) Features
    df_feat, num_cols, cat_cols = build_features(df)

    # 5) Pré-processamento + KMeans
    pre = ColumnTransformer([
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols),
    ], remainder="drop")

    X = pre.fit_transform(df_feat[num_cols + cat_cols])

    km = fit_kmeans(X, n_clusters=args.n_clusters, random_state=42)
    labels = km.labels_
    sil = silhouette_score(X, labels) if args.n_clusters > 1 and X.shape[0] > args.n_clusters else np.nan
    print(f"KMeans n={args.n_clusters} | silhouette={sil:.3f}")

    # 6) Ranking de clusters
    rank_df = rank_clusters(df_feat, labels)
    print("\nRanking de clusters (1 = maior potencial):\n", rank_df)

    # 7) Salva clusterização
    out_df = df_feat.copy()
    out_df["cluster"] = labels
    out_csv = f"{args.out_prefix}_clusterizados.csv"
    out_df.to_csv(out_csv, index=False)

    # 8) Mapa
    out_html = make_map(out_df, rank_df, out_html=f"{args.out_prefix}_mapa_clusters.html")

    print("\nArquivos gerados:")
    print(" - Enriquecidos:", enr_csv)
    print(" - Clusterizados:", out_csv)
    print(" - Mapa:", out_html)

if __name__ == "__main__":
    main()

