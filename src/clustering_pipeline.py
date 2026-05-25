
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
    Gera regiões ideais para venda com base no produto e filtros.
    Retorna lista de dicts: [{lat, lon, nome, motivo, cluster, score, classe_med, poi_med}]

    Para acessar as métricas de clustering junto com o resultado,
    use gerar_regioes_ideais_com_metricas() em vez desta função.
    """
    try:
        # Inicializa métricas (populado mais adiante após clustering)
        _metricas_finais: Dict = {}

        from nlp import identificar_nicho
        if nicho is None:
            nicho = identificar_nicho(produto)

        usar_api = filtros.get("usar_api", False)
        
        # ...código de carregamento e filtro igual...
        base_dir = Path(__file__).parent.parent
        data_dir = base_dir / "data"
        data_path = data_dir / "Projeto.xlsx"
        if not data_path.exists():
            data_path = data_dir / "clientes_enriquecidos.csv"
            if not data_path.exists():
                data_path = data_dir / "clientes.csv"
        if not data_path.exists():
            print(f"❌ Nenhum arquivo de dados encontrado em: {data_dir}")
            print(f"   Procurei por: Projeto.xlsx, clientes_enriquecidos.csv, clientes.csv")
            return []
        print(f"📂 Carregando dados de: {data_path}")
        
        # OTIMIZAÇÃO: Limita leitura inicial para acelerar
        if data_path.suffix == '.xlsx':
            df = carregar_e_preparar_dados(str(data_path), sheet_name="BASE")
        else:
            df = carregar_e_preparar_dados(str(data_path), sheet_name=None)
        
        # OTIMIZAÇÃO CRÍTICA: Se dataset muito grande, amostra inicialmente
        if len(df) > 5000:
            print(f"⚡ Dataset grande ({len(df)} registros), amostrando 5000 para performance")
            # Amostra estratificada por classe para manter distribuição
            if 'classe' in df.columns:
                df = df.groupby('classe', group_keys=False).apply(
                    lambda x: x.sample(min(len(x), 1000), random_state=42)
                )
            else:
                df = df.sample(5000, random_state=42)
        
        # Enriquece com POIs se solicitado
        if usar_api and API_KEY:
            print(f"🔍 Enriquecendo dados com Google Places API...")
            
            # OTIMIZAÇÃO AGRESSIVA: Limita a apenas 10 locais representativos
            # Agrupa por coordenadas próximas (arredonda para 2 casas decimais = ~1km)
            df['lat_round'] = df['lat'].round(2)
            df['lon_round'] = df['lon'].round(2)
            locais_unicos = df.drop_duplicates(subset=['lat_round', 'lon_round'])
            
            # Limita a no máximo 10 locais (suficiente para análise, mais rápido)
            max_locais = min(10, len(locais_unicos))
            locais_amostra = locais_unicos.head(max_locais)
            
            print(f"📊 Enriquecendo {max_locais} localizações para nicho '{nicho}'")
            print(f"🔍 POIs buscados: {list(PLACES_TYPES_BY_NICHE.get(nicho, PLACES_TYPES_BY_NICHE['Outro']).keys())}")
            print(f"⏱️  Tempo estimado: ~{max_locais * 2} segundos")
            
            cache = load_cache()
            sess = create_session_with_retry()
            all_new = []
            pois_por_local = {}
            
            import time as time_module
            inicio = time_module.time()
            
            # ── Paraleliza o enriquecimento por local ──────────────────────
            def _enrich_local(row_tuple):
                idx, row = row_tuple
                try:
                    feats, new_recs = enrich_row_with_pois(row, cache, sess, nicho=nicho)
                    return (row['lat_round'], row['lon_round']), feats, new_recs
                except Exception as e:
                    print(f"  ⚠️ Erro no local {idx}: {str(e)}")
                    return (row['lat_round'], row['lon_round']), {}, []

            rows_list = list(locais_amostra.iterrows())
            with ThreadPoolExecutor(max_workers=min(4, len(rows_list))) as pool:
                futures_loc = [pool.submit(_enrich_local, r) for r in rows_list]
                for i, future in enumerate(as_completed(futures_loc)):
                    key, feats, new_recs = future.result()
                    pois_por_local[key] = feats
                    all_new.extend(new_recs)
                    print(f"  ✓ {len(pois_por_local)}/{max_locais} locais")
            
            tempo_total = time_module.time() - inicio
            print(f"⏱️  Tempo de enriquecimento: {tempo_total:.1f}s")
            
            # Propaga POIs para todos os registros próximos
            for idx, row in df.iterrows():
                key = (row['lat_round'], row['lon_round'])
                if key in pois_por_local:
                    for k, v in pois_por_local[key].items():
                        df.at[idx, k] = v
            
            # Remove colunas temporárias
            df.drop(['lat_round', 'lon_round'], axis=1, inplace=True)
            
            if all_new:
                cache = pd.concat([cache, pd.DataFrame(all_new)], ignore_index=True)
                save_cache(cache)
            print(f"✓ Enriquecimento completo! {len(pois_por_local)} locais únicos com POIs")
        elif usar_api and not API_KEY:
            print("⚠️ API solicitada mas GOOGLE_API_KEY não configurada no .env")
        
        # Se não tem POIs, cria colunas zeradas ESPECÍFICAS DO NICHO
        poi_cols_existentes = [c for c in df.columns if c.startswith("poi_") and c.endswith("m")]
        if not poi_cols_existentes:
            # Usa POIs do nicho específico!
            places_types = PLACES_TYPES_BY_NICHE.get(nicho, PLACES_TYPES_BY_NICHE["Outro"])
            for label in places_types:
                for r in RADII:
                    df[f"poi_{label}_{r}m"] = 0
            print(f"📍 POIs zerados criados para nicho '{nicho}': {list(places_types.keys())}")

        df_filtrado = df.copy()
        if filtros.get("classe") and len(filtros["classe"]) > 0:
            df_filtrado = df_filtrado[df_filtrado["classe"].isin(filtros["classe"])]
            print(f"  ✓ Filtro classe: {filtros['classe']} -> {len(df_filtrado)} registros")
        if filtros.get("tipo") and filtros["tipo"]:
            df_filtrado = df_filtrado[df_filtrado["tipo_comercial"].str.upper() == filtros["tipo"].upper()]
            print(f"  ✓ Filtro tipo: {filtros['tipo']} -> {len(df_filtrado)} registros")
        if filtros.get("bairro") and len(filtros["bairro"]) > 0:
            df_filtrado = df_filtrado[df_filtrado["bairro"].str.upper().isin([b.upper() for b in filtros["bairro"]])]
            print(f"  ✓ Filtro bairro: {filtros['bairro']} -> {len(df_filtrado)} registros")
        if len(df_filtrado) == 0:
            print("⚠️  Nenhum registro após aplicar filtros")
            return []

        df_feat, num_cols, cat_cols = build_features(df_filtrado)
        ct = ColumnTransformer([
            ("num", StandardScaler(), num_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)
        ], remainder="drop")
        # OTIMIZADO: fit_transform e clustering com parâmetros mais rápidos
        X = ct.fit_transform(df_feat[num_cols + cat_cols])

        # Elbow Method — calcula ANTES de escolher k para usar o knee point
        n_clusters_max = min(4, max(2, len(df_feat) // 30))
        elbow_data = calcular_elbow(X, k_range=range(2, n_clusters_max + 2))

        # Usa a máxima curvatura (knee) como k ótimo, limitado ao máximo calculado
        n_clusters = min(_knee_point(elbow_data), n_clusters_max)
        print(f"  ✓ Elbow knee point: k={n_clusters} (base max={n_clusters_max})")

        # Comparação KMeans vs DBSCAN — escolhe o melhor automaticamente
        comparacao = comparar_kmeans_dbscan(X, n_clusters=n_clusters)
        labels = comparacao["labels_escolhidos"]

        # Métricas do algoritmo vencedor
        _metricas_finais = {
            "algoritmo": comparacao["melhor_algoritmo"],
            "justificativa": comparacao["justificativa"],
            "silhouette": comparacao["kmeans" if comparacao["melhor_algoritmo"] == "KMeans" else "dbscan"].get("silhouette"),
            "davies_bouldin": comparacao["kmeans" if comparacao["melhor_algoritmo"] == "KMeans" else "dbscan"].get("davies_bouldin"),
            "kmeans": comparacao["kmeans"],
            "dbscan": comparacao["dbscan"],
            "elbow": elbow_data,
        }

        # Se DBSCAN foi escolhido, pode ter mais ou menos clusters
        n_clusters_final = len(set(labels)) - (1 if -1 in labels else 0)

        ranking = rank_clusters(df_feat, labels, nicho)
        print(f"\n📊 Ranking de clusters (top 3):")
        print(ranking.head(3).to_string(index=False))
        top_clusters = ranking["cluster"].tolist()
        n_total_clusters = len(top_clusters)
        regioes = []
        pontos_por_cluster = 10

        # Verifica se existem dados de POI reais
        poi_norm_check = [c for c in df_feat.columns if c.startswith("poi_") and c.endswith("_norm")]
        tem_poi_real = any(float(df_feat[c].sum()) > 0 for c in poi_norm_check) if poi_norm_check else False
        peso_poi, peso_classe = get_pesos_score_por_nicho(nicho)

        for cluster_id in top_clusters:
            subset = df_feat[labels == cluster_id]
            cluster_info = ranking[ranking["cluster"] == cluster_id].iloc[0]
            for _, row in subset.head(pontos_por_cluster).iterrows():
                # Motivo: POIs relevantes e classe média
                poi_cols = [c for c in row.index if c.startswith("poi_") and c.endswith("m") and not c.endswith("_norm")]
                pois_relevantes = {}
                
                for c in poi_cols:
                    try:
                        valor = int(float(row[c]))
                        if valor > 0:
                            # Remove prefixo 'poi_' e sufixo com raio, deixa só o tipo
                            nome_limpo = c.replace("poi_", "").rsplit("_", 1)[0]
                            # Traduz nomes técnicos para nomes amigáveis
                            traducoes = {
                                "gym": "Academias",
                                "office": "Escritórios",
                                "university": "Universidades",
                                "supermarket": "Supermercados",
                                "school": "Escolas",
                                "park": "Parques",
                                "health": "Saúde",
                                "beauty": "Beleza",
                                "pet": "Pet shops",
                                "electronics": "Eletrônicos"
                            }
                            nome_exibir = traducoes.get(nome_limpo, nome_limpo.title())
                            if nome_exibir not in pois_relevantes:
                                pois_relevantes[nome_exibir] = 0
                            pois_relevantes[nome_exibir] += valor
                    except (ValueError, TypeError):
                        continue
                
                # Monta o motivo
                motivo_parts = []
                motivo_parts.append(f"🏆 Cluster rank #{int(cluster_info['ordem'])}")
                motivo_parts.append(f"👥 Classe média: {cluster_info['classe_med']:.1f}/5.0")
                motivo_parts.append(f"⭐ Score potencial: {cluster_info['score_potencial']:.2f}")
                
                if pois_relevantes:
                    top_pois = sorted(pois_relevantes.items(), key=lambda x: x[1], reverse=True)[:3]
                    pois_str = ", ".join([f"{nome} ({qtd})" for nome, qtd in top_pois])
                    motivo_parts.append(f"📍 POIs próximos: {pois_str}")
                else:
                    motivo_parts.append("📍 POIs: Dados não disponíveis (API não consultada)")
                
                motivo = " | ".join(motivo_parts)

                # --------------------------------------------------------
                # Score por linha: usa classe e POI REAIS do registro,
                # não a média do cluster. Normalizado para [0, 100].
                # --------------------------------------------------------
                row_classe = float(row.get("classe_ord", 3))
                poi_norm_row_cols = [c for c in row.index if c.startswith("poi_") and c.endswith("_norm")]
                row_poi = float(np.mean([row[c] for c in poi_norm_row_cols])) if poi_norm_row_cols else 0.0

                if tem_poi_real and row_poi > 0.001:
                    row_score_raw = peso_poi * row_poi + peso_classe * (row_classe / 5.0)
                else:
                    # Sem POIs: classe (70%) + rank do cluster (30%)
                    rank_bonus = (n_total_clusters - int(cluster_info["ordem"]) + 1) / n_total_clusters
                    row_score_raw = 0.70 * (row_classe / 5.0) + 0.30 * rank_bonus

                row_score_100 = round(min(max(row_score_raw * 100, 0.0), 100.0), 1)

                regioes.append({
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "nome": f"{row.get('bairro', 'Desconhecido')} - {row.get('nome', 'Cliente')} (Cluster {cluster_id+1})",
                    "motivo": motivo,
                    "cluster": int(cluster_id),
                    "score": row_score_100,
                    "classe_med": float(cluster_info["classe_med"]),
                    "poi_med": float(cluster_info["poi_med"]),
                    "tipo_comercial": row.get("tipo_comercial", "N/A"),
                    "classe_social": row.get("classe", "N/A"),
                })
        print(f"\n✓ {len(regioes)} regiões ideais identificadas")

        # Análise de mercado nas top-N regiões (apenas se API ativa)
        if usar_api and API_KEY and regioes:
            try:
                from market_analysis import analyze_top_regions
                cache_market = load_cache()
                sess_market = create_session_with_retry()
                regioes = analyze_top_regions(
                    regioes,
                    nicho=nicho,
                    cache_df=cache_market,
                    session=sess_market,
                    nearby_count_fn=nearby_count,
                    hkey_fn=hkey,
                    save_cache_fn=save_cache,
                    nearby_names_fn=nearby_names,
                )
                analisadas = sum(1 for r in regioes if r.get("analise_mercado"))
                print(f"📊 Análise de mercado aplicada em {analisadas} regiões top")
            except Exception as exc:
                print(f"⚠️ Falha na análise de mercado: {exc}")

        # Armazena métricas para acesso pela API via gerar_regioes_ideais_com_metricas()
        _last_clustering_metrics.update(_metricas_finais)

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

