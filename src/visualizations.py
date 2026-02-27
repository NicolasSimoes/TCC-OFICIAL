"""
Módulo de visualizações avançadas para análise de clustering.
Inclui gráficos de silhouette, elbow method e outras métricas.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.cluster import KMeans
from typing import Tuple, Optional
import io
import base64

# Configura estilo
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10


def plot_elbow_method(X: np.ndarray, max_k: int = 10) -> plt.Figure:
    """
    Gera gráfico do método Elbow para determinar número ideal de clusters.
    
    Args:
        X: Dados transformados
        max_k: Número máximo de clusters a testar
        
    Returns:
        Figura matplotlib
    """
    inertias = []
    K_range = range(2, min(max_k + 1, len(X) // 2))
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
        kmeans.fit(X)
        inertias.append(kmeans.inertia_)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(K_range, inertias, 'bo-', linewidth=2, markersize=8)
    ax.set_xlabel('Número de Clusters (k)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Inércia (Within-Cluster Sum of Squares)', fontsize=12, fontweight='bold')
    ax.set_title('Método Elbow - Determinação do K Ideal', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Adiciona anotações
    for i, (k, inertia) in enumerate(zip(K_range, inertias)):
        ax.annotate(f'{inertia:.0f}', 
                   xy=(k, inertia), 
                   xytext=(5, 5), 
                   textcoords='offset points',
                   fontsize=8,
                   alpha=0.7)
    
    plt.tight_layout()
    return fig


def plot_silhouette_scores(X: np.ndarray, max_k: int = 10) -> plt.Figure:
    """
    Gera gráfico de Silhouette Score para diferentes valores de k.
    
    Args:
        X: Dados transformados
        max_k: Número máximo de clusters a testar
        
    Returns:
        Figura matplotlib
    """
    silhouette_scores = []
    K_range = range(2, min(max_k + 1, len(X) // 2))
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = kmeans.fit_predict(X)
        score = silhouette_score(X, labels)
        silhouette_scores.append(score)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(K_range, silhouette_scores, 'go-', linewidth=2, markersize=8)
    ax.set_xlabel('Número de Clusters (k)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Silhouette Score', fontsize=12, fontweight='bold')
    ax.set_title('Silhouette Score por Número de Clusters', fontsize=14, fontweight='bold')
    ax.axhline(y=0.5, color='r', linestyle='--', alpha=0.5, label='Threshold (0.5)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Marca o melhor k
    best_k = K_range[np.argmax(silhouette_scores)]
    best_score = max(silhouette_scores)
    ax.plot(best_k, best_score, 'r*', markersize=20, label=f'Melhor k={best_k}')
    
    # Adiciona anotações
    for k, score in zip(K_range, silhouette_scores):
        ax.annotate(f'{score:.3f}', 
                   xy=(k, score), 
                   xytext=(5, -5), 
                   textcoords='offset points',
                   fontsize=8,
                   alpha=0.7)
    
    plt.tight_layout()
    return fig


def plot_silhouette_analysis(X: np.ndarray, labels: np.ndarray, n_clusters: int) -> plt.Figure:
    """
    Gera análise detalhada de silhouette para um clustering específico.
    
    Args:
        X: Dados transformados
        labels: Labels dos clusters
        n_clusters: Número de clusters
        
    Returns:
        Figura matplotlib
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Calcula silhouette score geral
    silhouette_avg = silhouette_score(X, labels)
    
    # Calcula silhouette para cada amostra
    sample_silhouette_values = silhouette_samples(X, labels)
    
    y_lower = 10
    for i in range(n_clusters):
        # Agrega valores de silhouette para amostras do cluster i
        ith_cluster_silhouette_values = sample_silhouette_values[labels == i]
        ith_cluster_silhouette_values.sort()
        
        size_cluster_i = ith_cluster_silhouette_values.shape[0]
        y_upper = y_lower + size_cluster_i
        
        color = plt.cm.nipy_spectral(float(i) / n_clusters)
        ax.fill_betweenx(np.arange(y_lower, y_upper),
                        0, ith_cluster_silhouette_values,
                        facecolor=color, edgecolor=color, alpha=0.7)
        
        # Label dos clusters
        ax.text(-0.05, y_lower + 0.5 * size_cluster_i, f'C{i}')
        
        y_lower = y_upper + 10
    
    ax.set_xlabel('Silhouette Coefficient', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cluster', fontsize=12, fontweight='bold')
    ax.set_title(f'Análise de Silhouette (k={n_clusters})\nScore Médio: {silhouette_avg:.3f}',
                fontsize=14, fontweight='bold')
    
    # Linha vertical para score médio
    ax.axvline(x=silhouette_avg, color="red", linestyle="--", linewidth=2,
              label=f'Score Médio: {silhouette_avg:.3f}')
    ax.axvline(x=0, color="black", linestyle="-", linewidth=0.5)
    
    ax.set_yticks([])
    ax.set_xlim([-0.1, 1])
    ax.legend()
    
    plt.tight_layout()
    return fig


def plot_cluster_distribution(df: pd.DataFrame, cluster_col: str = 'cluster') -> plt.Figure:
    """
    Gera gráfico de distribuição de clusters.
    
    Args:
        df: DataFrame com coluna de cluster
        cluster_col: Nome da coluna de cluster
        
    Returns:
        Figura matplotlib
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Gráfico de barras
    cluster_counts = df[cluster_col].value_counts().sort_index()
    axes[0].bar(cluster_counts.index, cluster_counts.values, color='steelblue', alpha=0.7)
    axes[0].set_xlabel('Cluster', fontsize=12, fontweight='bold')
    axes[0].set_ylabel('Número de Pontos', fontsize=12, fontweight='bold')
    axes[0].set_title('Distribuição de Pontos por Cluster', fontsize=13, fontweight='bold')
    axes[0].grid(axis='y', alpha=0.3)
    
    # Adiciona valores nas barras
    for i, v in enumerate(cluster_counts.values):
        axes[0].text(cluster_counts.index[i], v + 0.5, str(v), 
                    ha='center', va='bottom', fontweight='bold')
    
    # Gráfico de pizza
    axes[1].pie(cluster_counts.values, labels=[f'C{i}' for i in cluster_counts.index],
               autopct='%1.1f%%', startangle=90, colors=plt.cm.Set3.colors)
    axes[1].set_title('Proporção de Pontos por Cluster', fontsize=13, fontweight='bold')
    
    plt.tight_layout()
    return fig


def plot_cluster_characteristics(df: pd.DataFrame, ranking: pd.DataFrame) -> plt.Figure:
    """
    Gera visualização das características dos clusters.
    
    Args:
        df: DataFrame com dados e clusters
        ranking: DataFrame com ranking dos clusters
        
    Returns:
        Figura matplotlib
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. Score de Potencial
    ax = axes[0, 0]
    colors = ['#2ecc71' if i == 0 else '#3498db' if i == 1 else '#95a5a6' 
              for i in range(len(ranking))]
    ax.barh(ranking['cluster'].astype(str), ranking['score_potencial'], color=colors, alpha=0.7)
    ax.set_xlabel('Score de Potencial', fontsize=11, fontweight='bold')
    ax.set_ylabel('Cluster', fontsize=11, fontweight='bold')
    ax.set_title('Score de Potencial por Cluster', fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # 2. Classe Média
    ax = axes[0, 1]
    ax.bar(ranking['cluster'].astype(str), ranking['classe_med'], 
           color='coral', alpha=0.7)
    ax.set_xlabel('Cluster', fontsize=11, fontweight='bold')
    ax.set_ylabel('Classe Média (1-5)', fontsize=11, fontweight='bold')
    ax.set_title('Classe Socioeconômica Média', fontsize=12, fontweight='bold')
    ax.axhline(y=3, color='r', linestyle='--', alpha=0.5, label='Classe C')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # 3. POI Média
    ax = axes[1, 0]
    ax.bar(ranking['cluster'].astype(str), ranking['poi_med'], 
           color='lightseagreen', alpha=0.7)
    ax.set_xlabel('Cluster', fontsize=11, fontweight='bold')
    ax.set_ylabel('POI Média (normalizado)', fontsize=11, fontweight='bold')
    ax.set_title('Densidade Média de POIs', fontsize=12, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    
    # 4. Ranking Visual
    ax = axes[1, 1]
    ranking_sorted = ranking.sort_values('ordem')
    colors_rank = ['#f39c12', '#c0392b', '#8e44ad', '#2980b9', '#16a085']
    ax.barh(ranking_sorted['cluster'].astype(str), 
           ranking_sorted['ordem'].max() - ranking_sorted['ordem'] + 1,
           color=colors_rank[:len(ranking_sorted)], alpha=0.7)
    ax.set_xlabel('Prioridade (maior = melhor)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Cluster', fontsize=11, fontweight='bold')
    ax.set_title('Ranking de Prioridade', fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    return fig


def fig_to_base64(fig: plt.Figure) -> str:
    """
    Converte figura matplotlib para string base64 (para Streamlit).
    
    Args:
        fig: Figura matplotlib
        
    Returns:
        String base64 da imagem
    """
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return img_str
