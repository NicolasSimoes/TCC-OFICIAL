import pandas as pd
import folium
from folium.plugins import HeatMap
import numpy as np
from pathlib import Path


def gerar_mapa(regioes: list):
    """
    Recebe lista [(lat, lon, nome)] e retorna um folium.Map.
    
    Args:
        regioes: Lista de tuplas (lat, lon, nome)
        
    Returns:
        folium.Map com marcadores das regiões
    """
    if not regioes or len(regioes) == 0:
        # Centro de Fortaleza se não houver regiões
        return folium.Map(location=[-3.7319, -38.5267], zoom_start=12)

    # Calcula centro baseado nas regiões
    lats = [r[0] for r in regioes]
    lons = [r[1] for r in regioes]
    center = [np.mean(lats), np.mean(lons)]
    
    # Cria mapa com estilo mais moderno
    mapa = folium.Map(
        location=center,
        zoom_start=13,
        tiles='CartoDB positron',
        control_scale=True
    )

    # Define cores para diferentes clusters (até 10 cores diferentes)
    colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'darkblue', 'darkgreen', 'cadetblue']

    # Adiciona marcadores com cores diferentes por cluster
    for i, (lat, lon, nome) in enumerate(regioes):
        # Extrai o número do cluster do nome (assumindo formato "... (Cluster X)")
        try:
            cluster_num = int(nome.split("Cluster ")[-1].strip(")")) - 1
            color = colors[cluster_num % len(colors)]
        except:
            color = 'gray'
            
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            popup=nome,
            color=color,
            fill=True,
            fill_opacity=0.7
        ).add_to(mapa)
    for lat, lon, nome in regioes:
        folium.Marker(
            [lat, lon], 
            popup=folium.Popup(f"<b>{nome}</b>", max_width=200),
            tooltip=nome,
            icon=folium.Icon(color="green", icon="star", prefix="fa")
        ).add_to(mapa)

    return mapa
