
from __future__ import annotations
import os, time, argparse, hashlib
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
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

import folium
from folium.plugins import HeatMap
from branca.colormap import LinearColormap

from data_loader import carregar_e_preparar_dados, normalize_header

# =========================
# CONFIG
# =========================
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("⚠️  GOOGLE_API_KEY não encontrada no .env - funcionalidades de POI desabilitadas")

# Tipos de lugar por nicho (REDUZIDO para otimização)
PLACES_TYPES: Dict[str, List[str]] = {
    # Apenas os tipos mais relevantes
    "gym": ["gym"],
    "supermarket": ["supermarket"],
}

# Raios em metros para Nearby Search (REDUZIDO de 3 para 1 raio)
RADII = [800]  # Apenas raio médio para otimizar

# Classe socioeconômica -> ordinal
CLASSE_ORD = {"A":5, "B":4, "C":3, "D":2, "E":1}

# Cache local das consultas à API (para economizar cota)
CACHE_PATH = Path("cache_places.parquet")

# =========================
# UTIL
# =========================
def hkey(lat: float, lon: float, place_type: str, radius: int) -> str:
    s = f"{round(float(lat),6)}|{round(float(lon),6)}|{place_type}|{radius}"
    return hashlib.md5(s.encode()).hexdigest()

def load_cache() -> pd.DataFrame:
    if CACHE_PATH.exists():
        return pd.read_parquet(CACHE_PATH)
    return pd.DataFrame(columns=["h","lat","lon","type","radius","count","ts"])

def save_cache(df: pd.DataFrame) -> None:
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
# GOOGLE PLACES
# =========================
def nearby_count(lat: float, lon: float, place_type: str, radius: int, session: requests.Session) -> int:
    """
    Conta resultados via Nearby Search com até 3 páginas.
    Inclui tratamento de erros e retry automático.
    """
    if not API_KEY:
        return 0
    
    base = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {"location": f"{lat},{lon}", "radius": radius, "type": place_type, "key": API_KEY}
    total, page = 0, 0
    max_retries = 1  # Reduzido de 3 para 1
    
    while True:
        try:
            r = session.get(base, params=params, timeout=5)  # Reduzido de 30 para 5
            
            # Retry em erros temporários
            if r.status_code in (429, 500, 503):
                if page < max_retries:
                    wait_time = min(2**page, 10)
                    print(f"⚠️  Status {r.status_code}, aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    page += 1
                    continue
                else:
                    print(f"❌ Falha após {max_retries} tentativas")
                    return 0
            
            r.raise_for_status()
            data = r.json()
            
            # Verifica status da API
            if data.get("status") == "OVER_QUERY_LIMIT":
                print("❌ Limite de cota da API atingido")
                return 0
            elif data.get("status") not in ["OK", "ZERO_RESULTS"]:
                print(f"⚠️  API retornou status: {data.get('status')}")
                return 0
            
            total += len(data.get("results", []))
            
            # NÃO busca próximas páginas para otimizar tempo
            # Apenas primeira página (até 20 resultados) é suficiente
            break
            
        except requests.exceptions.Timeout:
            print(f"⚠️  Timeout na requisição (tentativa {page+1}/{max_retries})")
            if page < max_retries:
                page += 1
                time.sleep(2)
                continue
            return 0
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {str(e)}")
            return 0
        except Exception as e:
            print(f"❌ Erro inesperado: {str(e)}")
            return 0
    
    return total

def enrich_row_with_pois(row: pd.Series, cache_df: pd.DataFrame, session: requests.Session) -> Tuple[Dict[str,int], List[dict]]:
    """Enriquece uma linha com POIs, usando cache quando disponível."""
    try:
        lat, lon = float(row["lat"]), float(row["lon"])
        new_records = []
        results: Dict[str,int] = {}
        
        for label, types in PLACES_TYPES.items():
            for radius in RADII:
                subtotal = 0
                for tp in types:
                    hk = hkey(lat, lon, tp, radius)
                    cached = cache_df.loc[cache_df["h"] == hk]
                    
                    if not cached.empty:
                        cnt = int(cached.iloc[0]["count"])
                    else:
                        cnt = nearby_count(lat, lon, tp, radius, session)
                        new_records.append({
                            "h": hk,
                            "lat": lat,
                            "lon": lon,
                            "type": tp,
                            "radius": radius,
                            "count": cnt,
                            "ts": int(time.time())
                        })
                    subtotal += cnt
                    
                results[f"poi_{label}_{radius}m"] = subtotal
                
        return results, new_records
        
    except Exception as e:
        print(f"❌ Erro ao enriquecer linha: {str(e)}")
        # Retorna valores zerados em caso de erro
        results = {}
        for label in PLACES_TYPES:
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
    return df, num_cols, cat_cols

# =========================
# CLUSTERING
# =========================
def fit_kmeans(X: np.ndarray, n_clusters: int, random_state: int = 42) -> KMeans:
    # OTIMIZADO: n_init reduzido de 20 para 5 (4x mais rápido)
    km = KMeans(n_clusters=n_clusters, n_init=5, max_iter=100, random_state=random_state)
    km.fit(X)
    return km

def get_pesos_score_por_nicho(nicho: str):
    # Pesos dinâmicos por nicho
    pesos = {
        "Infantil": (0.8, 0.2),
        "Fitness": (0.7, 0.3),
        "Escolar": (0.7, 0.3),
        "Alimentação": (0.6, 0.4),
        "Farmácia": (0.6, 0.4),
        "Beleza": (0.5, 0.5),
        "Pet": (0.7, 0.3),
        "Eletrônicos": (0.6, 0.4),
        "Outro": (0.6, 0.4)
    }
    return pesos.get(nicho, (0.6, 0.4))

def rank_clusters(df_feat: pd.DataFrame, labels: np.ndarray, nicho: str = "Outro") -> pd.DataFrame:
    """Ranking por potencial com pesos dinâmicos por nicho."""
    tmp = df_feat.copy()
    tmp["cluster"] = labels
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

def gerar_regioes_ideais(produto: str, filtros: dict, nicho: str = None) -> list:
    """
    Gera regiões ideais para venda com base no produto e filtros.
    Retorna lista de dicts: [{lat, lon, nome, motivo, cluster, score, classe_med, poi_med}]
    """
    try:
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
            
            print(f"📊 Enriquecendo {max_locais} localizações representativas (de {len(df)} registros)")
            print(f"⏱️  Tempo estimado: ~{max_locais * 2} segundos")
            
            cache = load_cache()
            sess = create_session_with_retry()
            all_new = []
            pois_por_local = {}
            
            import time as time_module
            inicio = time_module.time()
            
            for idx, row in locais_amostra.iterrows():
                try:
                    feats, new_records = enrich_row_with_pois(row, cache, sess)
                    pois_por_local[(row['lat_round'], row['lon_round'])] = feats
                    
                    if new_records:
                        all_new.extend(new_records)
                    
                    # Progress
                    print(f"  ✓ {len(pois_por_local)}/{max_locais} locais")
                    
                except Exception as e:
                    print(f"  ⚠️ Erro no local {idx}: {str(e)}")
                    # Continua mesmo com erro
                    pois_por_local[(row['lat_round'], row['lon_round'])] = {}
            
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
        
        # Se não tem POIs, cria colunas zeradas
        poi_cols_existentes = [c for c in df.columns if c.startswith("poi_") and c.endswith("m")]
        if not poi_cols_existentes:
            for label in PLACES_TYPES:
                for r in RADII:
                    df[f"poi_{label}_{r}m"] = 0

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
        # Reduz número de clusters para acelerar (menos é mais rápido)
        n_clusters = min(4, max(2, len(df_feat) // 30))
        if len(df_feat) < n_clusters:
            print(f"⚠️  Poucos dados ({len(df_feat)}), retornando todos os pontos")
            regioes = []
            for _, row in df_feat.head(10).iterrows():
                regioes.append({
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "nome": row.get("bairro", "Desconhecido"),
                    "motivo": "Poucos dados após filtro. Mostrando pontos brutos.",
                    "cluster": None,
                    "score": None,
                    "classe_med": None,
                    "poi_med": None
                })
            return regioes
        km = fit_kmeans(X, n_clusters=n_clusters)
        labels = km.labels_
        ranking = rank_clusters(df_feat, labels, nicho)
        print(f"\n📊 Ranking de clusters (top 3):")
        print(ranking.head(3).to_string(index=False))
        top_clusters = ranking["cluster"].tolist()
        regioes = []
        pontos_por_cluster = 10
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
                
                regioes.append({
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "nome": f"{row.get('bairro', 'Desconhecido')} - {row.get('nome', 'Cliente')} (Cluster {cluster_id+1})",
                    "motivo": motivo,
                    "cluster": int(cluster_id),
                    "score": float(cluster_info['score_potencial']),
                    "classe_med": float(cluster_info['classe_med']),
                    "poi_med": float(cluster_info['poi_med']),
                    "tipo_comercial": row.get('tipo_comercial', 'N/A'),
                    "classe_social": row.get('classe', 'N/A')
                })
        print(f"\n✓ {len(regioes)} regiões ideais identificadas")
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

