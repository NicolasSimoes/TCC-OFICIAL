import os, time, argparse, sys
from pathlib import Path
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import folium
from folium.plugins import HeatMap
from branca.colormap import LinearColormap

def log(msg):
    print(f"[LOG] {msg}")
    sys.stdout.flush()

def process_with_retry(df, api_key, max_retries=3):
    log("Iniciando processamento dos POIs...")
    session = requests.Session()
    retry = Retry(total=max_retries, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    results = []
    for idx, row in df.iterrows():
        try:
            log(f"Processando registro {idx+1}/{len(df)}")
            base = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{row['LATITUDE']},{row['LONGITUDE']}",
                "radius": 1000,
                "type": "restaurant",  # pode ser modificado conforme necessário
                "key": api_key
            }
            
            r = session.get(base, params=params, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if data['status'] == 'OK':
                    results.append({
                        'idx': idx,
                        'num_pois': len(data['results'])
                    })
                    log(f"  ✓ Encontrados {len(data['results'])} POIs")
                else:
                    log(f"  ⚠️ Status da API: {data['status']}")
            else:
                log(f"  ❌ Erro HTTP: {r.status_code}")
            
            time.sleep(0.2)  # rate limiting
            
        except Exception as e:
            log(f"  ❌ Erro no registro {idx}: {str(e)}")
            continue
    
    return results

def prepare_features(df, poi_results):
    log("Preparando features para clustering...")
    
    # Adiciona contagem de POIs ao dataframe
    df['num_pois'] = 0
    for result in poi_results:
        df.loc[result['idx'], 'num_pois'] = result['num_pois']
    
    # Define features numéricas e categóricas
    num_features = ['LATITUDE', 'LONGITUDE', 'num_pois']
    cat_features = ['CLASSE SOCIAL', 'TIPO COMERCIAL']
    
    # Prepara o pipeline de transformação
    preprocessor = ColumnTransformer([
        ('num', StandardScaler(), num_features),
        ('cat', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), cat_features)
    ])
    
    # Fit e transform
    X = preprocessor.fit_transform(df)
    log(f"✓ Features preparadas: {X.shape[1]} dimensões")
    
    return X, preprocessor

def cluster_data(X, n_clusters=5):
    log(f"Aplicando KMeans com {n_clusters} clusters...")
    
    # Fit KMeans
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(X)
    
    # Calcula silhouette score
    sil_score = silhouette_score(X, labels)
    log(f"✓ Clustering concluído. Silhouette score: {sil_score:.3f}")
    
    return labels, kmeans

def generate_maps(df, labels, n_clusters=5):
    log("Gerando mapas...")
    
    # Define cores para os clusters
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'darkblue']
    
    # 1. Mapa de Clusters
    m_clusters = folium.Map(
        location=[df['LATITUDE'].mean(), df['LONGITUDE'].mean()],
        zoom_start=12
    )
    
    # Adiciona pontos coloridos por cluster
    for idx, row in df.iterrows():
        folium.CircleMarker(
            location=[row['LATITUDE'], row['LONGITUDE']],
            radius=8,
            popup=f"Cluster: {row['cluster']}<br>POIs: {row['num_pois']}<br>Classe: {row['CLASSE SOCIAL']}",
            color=colors[int(row['cluster'])],
            fill=True
        ).add_to(m_clusters)
    
    # 2. Mapa de Calor
    m_heat = folium.Map(
        location=[df['LATITUDE'].mean(), df['LONGITUDE'].mean()],
        zoom_start=12
    )
    
    # Prepara dados para o heatmap
    heat_data = [[row['LATITUDE'], row['LONGITUDE'], row['num_pois']] for idx, row in df.iterrows()]
    HeatMap(heat_data).add_to(m_heat)
    
    # Salva mapas
    m_clusters.save('data/mapa_clusters.html')
    m_heat.save('data/mapa_calor.html')
    log("✓ Mapas gerados:")
    log("  - data/mapa_clusters.html")
    log("  - data/mapa_calor.html")

def main():
    log("Iniciando pipeline...")
    
    # Carrega variáveis de ambiente
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        log("❌ GOOGLE_API_KEY não encontrada no arquivo .env")
        return
    
    try:
        # 1. Carrega e processa dados
        df = pd.read_csv('data/clientes.csv', sep=';')
        log(f"✓ Dados carregados: {len(df)} registros")
        
        # 2. Enriquece com POIs
        results = process_with_retry(df, api_key)
        log(f"✓ POIs processados: {len(results)} registros")
        
        # 3. Prepara features
        X, preprocessor = prepare_features(df, results)
        
        # 4. Aplica clustering
        labels, kmeans = cluster_data(X, n_clusters=5)
        
        # 5. Adiciona labels ao dataframe
        df['cluster'] = labels
        
        # 6. Salva resultados
        output_file = 'data/clientes_processados.csv'
        df.to_csv(output_file, index=False)
        log(f"✓ Resultados salvos em: {output_file}")
        
        # Mostra distribuição dos clusters
        for i in range(5):
            count = (labels == i).sum()
            log(f"  Cluster {i}: {count} pontos")
        
        # 7. Gera mapas
        generate_maps(df, labels)
        
    except Exception as e:
        log(f"❌ Erro fatal: {str(e)}")
        raise  # Para ver o traceback completo em caso de erro

if __name__ == "__main__":
    main()