"""
Módulo de geração de mapas interativos avançados.
Inclui HeatMaps, clusters coloridos, filtros e popups informativos.
"""

import pandas as pd
import folium
from folium.plugins import HeatMap, MiniMap, Fullscreen, LocateControl
from folium import LayerControl
import numpy as np
from pathlib import Path
from branca.element import Template, MacroElement


# Cores por cluster (gradiente de verde a vermelho por potencial)
CLUSTER_COLORS = {
    0: '#2ecc71',  # Verde - melhor
    1: '#3498db',  # Azul
    2: '#f39c12',  # Laranja
    3: '#e74c3c',  # Vermelho
    4: '#9b59b6',  # Roxo
}

# Ícones por nicho
NICHE_ICONS = {
    "Fitness": "dumbbell",
    "Infantil": "baby",
    "Escolar": "book",
    "Alimentação": "utensils",
    "Farmácia": "medkit",
    "Beleza": "spa",
    "Pet": "paw",
    "Eletrônicos": "laptop",
    "Outro": "shopping-cart"
}


def gerar_mapa(regioes: list, nicho: str = "Outro", produto: str = ""):
    """
    Gera mapa interativo avançado com HeatMap, clusters e filtros.
    
    Args:
        regioes: Lista de dicts com lat, lon, nome, cluster, score, etc.
                 OU lista de tuplas (lat, lon, nome) para compatibilidade
        nicho: Nicho do produto para personalização visual
        produto: Nome do produto para título
        
    Returns:
        folium.Map com todas as camadas interativas
    """
    # Compatibilidade: converte lista de tuplas para lista de dicts
    if regioes and isinstance(regioes[0], tuple):
        regioes = [{"lat": r[0], "lon": r[1], "nome": r[2]} for r in regioes]
    
    if not regioes or len(regioes) == 0:
        # Mapa vazio centralizado em Fortaleza
        mapa = folium.Map(location=[-3.7319, -38.5267], zoom_start=12, tiles='CartoDB positron')
        folium.Marker(
            [-3.7319, -38.5267],
            popup="Nenhuma região encontrada. Ajuste os filtros.",
            icon=folium.Icon(color="gray", icon="info-sign")
        ).add_to(mapa)
        return mapa

    # Calcula centro baseado nas regiões
    lats = [r['lat'] if isinstance(r, dict) else r[0] for r in regioes]
    lons = [r['lon'] if isinstance(r, dict) else r[1] for r in regioes]
    center = [np.mean(lats), np.mean(lons)]
    
    # Cria mapa base com estilo moderno
    mapa = folium.Map(
        location=center,
        zoom_start=13,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )
    
    # Adiciona múltiplas opções de tiles
    folium.TileLayer('CartoDB positron', name='🗺️ Claro').add_to(mapa)
    folium.TileLayer('CartoDB dark_matter', name='🌙 Escuro').add_to(mapa)
    folium.TileLayer('OpenStreetMap', name='📍 Detalhado').add_to(mapa)
    
    # Adiciona controles extras
    Fullscreen(position='topleft').add_to(mapa)
    MiniMap(toggle_display=True, position='bottomright').add_to(mapa)
    
    # Agrupa regiões por cluster
    clusters_data = {}
    for r in regioes:
        if isinstance(r, dict):
            cluster_id = r.get('cluster', 0) or 0
            if cluster_id not in clusters_data:
                clusters_data[cluster_id] = []
            clusters_data[cluster_id].append(r)
        else:
            if 0 not in clusters_data:
                clusters_data[0] = []
            clusters_data[0].append({"lat": r[0], "lon": r[1], "nome": r[2]})
    
    # === CAMADA 1: HEATMAP DE POTENCIAL ===
    heat_data = []
    for r in regioes:
        if isinstance(r, dict):
            lat, lon = r['lat'], r['lon']
            weight = r.get('score', 0.5) or 0.5
            heat_data.append([lat, lon, weight])
        else:
            heat_data.append([r[0], r[1], 0.5])
    
    if heat_data:
        heat_group = folium.FeatureGroup(name='🔥 Mapa de Calor', show=True)
        HeatMap(
            heat_data,
            min_opacity=0.3,
            max_zoom=15,
            radius=25,
            blur=20,
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}
        ).add_to(heat_group)
        heat_group.add_to(mapa)
    
    # === CAMADA 2: MARCADORES POR CLUSTER ===
    for cluster_id, pontos in sorted(clusters_data.items()):
        color = CLUSTER_COLORS.get(cluster_id, '#95a5a6')
        
        if len(clusters_data) > 1:
            grupo_nome = f'📍 Cluster {cluster_id + 1} ({len(pontos)} pontos)'
        else:
            grupo_nome = f'📍 Localizações ({len(pontos)} pontos)'
        
        cluster_group = folium.FeatureGroup(name=grupo_nome, show=True)
        
        for r in pontos:
            lat = r['lat'] if isinstance(r, dict) else r[0]
            lon = r['lon'] if isinstance(r, dict) else r[1]
            nome = r.get('nome', 'Local') if isinstance(r, dict) else r[2]
            
            popup_html = _criar_popup_html(r, nicho, produto)
            tooltip = nome
            
            score = r.get('score', 0.5) if isinstance(r, dict) else 0.5
            radius = 8 + (score * 10)
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=350),
                tooltip=tooltip,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=2
            ).add_to(cluster_group)
        
        cluster_group.add_to(mapa)
    
    # === CAMADA 3: TOP 3 REGIÕES DESTACADAS ===
    top_regioes = sorted(
        [r for r in regioes if isinstance(r, dict) and r.get('score')],
        key=lambda x: x.get('score', 0),
        reverse=True
    )[:3]
    
    if top_regioes:
        top_group = folium.FeatureGroup(name='⭐ TOP 3 Regiões', show=True)
        
        for i, r in enumerate(top_regioes):
            lat, lon = r['lat'], r['lon']
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(_criar_popup_html(r, nicho, produto, destaque=True), max_width=350),
                tooltip=f"#{i+1} - {r.get('nome', 'Top região')[:30]}",
                icon=folium.Icon(
                    color='green' if i == 0 else 'blue' if i == 1 else 'orange',
                    icon='star',
                    prefix='fa'
                )
            ).add_to(top_group)
            
            folium.Circle(
                location=[lat, lon],
                radius=300,
                color='gold' if i == 0 else 'silver',
                fill=True,
                fill_opacity=0.1,
                weight=3,
                dash_array='5, 10'
            ).add_to(top_group)
        
        top_group.add_to(mapa)
    
    LayerControl(collapsed=False, position='topright').add_to(mapa)
    _adicionar_legenda(mapa, nicho, produto, len(regioes))
    
    return mapa


def _criar_popup_html(regiao: dict, nicho: str, produto: str, destaque: bool = False) -> str:
    """Cria HTML rico para popup do marcador."""
    
    if not isinstance(regiao, dict):
        return f"<b>{regiao}</b>"
    
    nome = regiao.get('nome', 'Local')
    score = regiao.get('score', 0)
    classe_med = regiao.get('classe_med', 0)
    poi_med = regiao.get('poi_med', 0)
    motivo = regiao.get('motivo', '')
    tipo_comercial = regiao.get('tipo_comercial', 'N/A')
    classe_social = regiao.get('classe_social', 'N/A')
    cluster = regiao.get('cluster', 0)
    
    score_percent = min(score * 100, 100) if score else 50
    score_color = '#2ecc71' if score_percent > 70 else '#f39c12' if score_percent > 40 else '#e74c3c'
    classe_display = f"{classe_med:.1f}/5.0" if classe_med else "N/A"
    poi_display = f"{poi_med:.2f}" if poi_med else "N/A"
    
    header_bg = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' if destaque else '#2c3e50'
    
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 280px;">
        <div style="background: {header_bg}; color: white; padding: 12px; margin: -13px -13px 10px -13px; border-radius: 4px 4px 0 0;">
            <h4 style="margin: 0; font-size: 14px;">{'⭐ ' if destaque else ''}{nome[:35]}{'...' if len(str(nome)) > 35 else ''}</h4>
            <small style="opacity: 0.8;">Cluster {cluster + 1 if cluster is not None else 'N/A'} | {nicho}</small>
        </div>
        
        <div style="padding: 0 5px;">
            <div style="margin-bottom: 10px;">
                <strong>📊 Score de Potencial</strong>
                <div style="background: #ecf0f1; border-radius: 10px; height: 20px; margin-top: 5px; overflow: hidden;">
                    <div style="background: {score_color}; height: 100%; width: {score_percent}%; 
                                display: flex; align-items: center; justify-content: center; color: white; font-size: 11px;">
                        {score_percent:.0f}%
                    </div>
                </div>
            </div>
            
            <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                <tr><td style="padding: 4px 0;"><strong>👥 Classe Média:</strong></td><td style="text-align: right;">{classe_display}</td></tr>
                <tr><td style="padding: 4px 0;"><strong>🏪 Tipo:</strong></td><td style="text-align: right;">{tipo_comercial}</td></tr>
                <tr><td style="padding: 4px 0;"><strong>💰 Classe Social:</strong></td><td style="text-align: right;">{classe_social}</td></tr>
                <tr><td style="padding: 4px 0;"><strong>📍 POIs:</strong></td><td style="text-align: right;">{poi_display}</td></tr>
            </table>
        </div>
    </div>
    """
    return html


def _adicionar_legenda(mapa: folium.Map, nicho: str, produto: str, total_pontos: int):
    """Adiciona legenda personalizada ao mapa."""
    
    produto_display = produto[:18] + '...' if len(str(produto)) > 18 else produto
    
    legenda_html = f"""
    {{% macro html(this, kwargs) %}}
    <div style="
        position: fixed;
        bottom: 50px;
        left: 10px;
        width: 200px;
        background-color: white;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        padding: 12px;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        z-index: 1000;
    ">
        <h4 style="margin: 0 0 8px 0; color: #2c3e50; font-size: 13px;">
            🎯 {produto_display if produto else 'Análise'}
        </h4>
        <div style="color: #7f8c8d; margin-bottom: 8px; font-size: 11px;">
            <strong>Nicho:</strong> {nicho}<br>
            <strong>Pontos:</strong> {total_pontos}
        </div>
        <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 6px 0;">
        <div style="font-size: 10px;">
            <div style="margin: 3px 0;">
                <span style="display: inline-block; width: 10px; height: 10px; background: #2ecc71; border-radius: 50%; margin-right: 5px;"></span>
                Cluster 1 (Melhor)
            </div>
            <div style="margin: 3px 0;">
                <span style="display: inline-block; width: 10px; height: 10px; background: #3498db; border-radius: 50%; margin-right: 5px;"></span>
                Cluster 2
            </div>
            <div style="margin: 3px 0;">
                <span style="display: inline-block; width: 10px; height: 10px; background: #f39c12; border-radius: 50%; margin-right: 5px;"></span>
                Cluster 3
            </div>
        </div>
        <hr style="border: none; border-top: 1px solid #ecf0f1; margin: 6px 0;">
        <div style="font-size: 9px; color: #95a5a6;">
            🔥 Calor = Potencial<br>
            ⭐ Estrelas = TOP 3
        </div>
    </div>
    {{% endmacro %}}
    """
    
    macro = MacroElement()
    macro._template = Template(legenda_html)
    mapa.get_root().add_child(macro)
