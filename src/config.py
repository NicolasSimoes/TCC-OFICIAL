"""
Configurações centralizadas do Smart Sale Fortaleza.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Diretórios
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
CACHE_DIR = BASE_DIR / "cache"

# Cria diretórios se não existirem
CACHE_DIR.mkdir(exist_ok=True)

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Google Places API
PLACES_API_CONFIG = {
    "base_url": "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
    "timeout": 30,
    "max_retries": 3,
    "backoff_factor": 1,
    "retry_status_codes": [429, 500, 502, 503, 504],
}

# Raios de busca de POIs (em metros)
# Valores enxutos (2 raios) para reduzir consumo de quota Google Places.
SEARCH_RADII = [500, 1000]

# Tipos de POIs por nicho (single source of truth para todo o pipeline)
PLACES_TYPES_BY_NICHE = {
    "Fitness": {
        "gym": ["gym", "health"],
        "park": ["park"],
        "sports": ["stadium", "sports_complex"],
    },
    "Infantil": {
        "school": ["school", "primary_school"],
        "park": ["park", "playground"],
        "childcare": ["day_care"],
    },
    "Escolar": {
        "school": ["school", "university"],
        "library": ["library", "book_store"],
        "stationery": ["stationery_store"],
    },
    "Alimentação": {
        "supermarket": ["supermarket", "grocery_or_supermarket"],
        "restaurant": ["restaurant", "cafe", "bakery"],
    },
    "Farmácia": {
        "pharmacy": ["pharmacy", "drugstore"],
        "health": ["hospital", "doctor"],
    },
    "Beleza": {
        "beauty": ["beauty_salon", "hair_care", "spa"],
        "shopping": ["shopping_mall", "clothing_store"],
    },
    "Pet": {
        "pet": ["pet_store", "veterinary_care"],
        "park": ["park"],
    },
    "Eletrônicos": {
        "electronics": ["electronics_store"],
        "shopping": ["shopping_mall", "department_store"],
    },
    "Outro": {
        "supermarket": ["supermarket"],
        "shopping": ["shopping_mall"],
    },
    "Saúde": {
        "health": ["hospital", "doctor", "physiotherapist"],
        "pharmacy": ["pharmacy", "drugstore"],
        "dental": ["dentist"],
    },
}

# Tipo padrão para clustering
DEFAULT_PLACES_TYPES = {
    "gym": ["gym"],
    "office": ["bank", "real_estate_agency", "insurance_agency", "lawyer"],
    "university": ["university"],
    "supermarket": ["supermarket", "grocery_or_supermarket"],
}

# ---------------------------------------------------------------------------
# Análise de mercado por região (usada pelo módulo market_analysis)
# ---------------------------------------------------------------------------

# Concorrentes diretos: tipos de Place que indicam concorrência ao nicho
COMPETITOR_TYPES_BY_NICHE = {
    "Fitness":     ["gym"],
    "Infantil":    ["clothing_store", "store"],
    "Escolar":     ["book_store", "stationery_store"],
    "Alimentação": ["supermarket", "grocery_or_supermarket"],
    "Farmácia":    ["pharmacy", "drugstore"],
    "Beleza":      ["beauty_salon", "hair_care"],
    "Pet":         ["pet_store"],
    "Eletrônicos": ["electronics_store"],
    "Saúde":       ["hospital", "doctor"],
    "Outro":       ["store"],
}

# Negócios sinérgicos: complementam o nicho e atraem o mesmo público
SYNERGY_TYPES_BY_NICHE = {
    "Fitness":     ["park", "stadium", "health"],
    "Infantil":    ["school", "primary_school", "park"],
    "Escolar":     ["school", "university", "library"],
    "Alimentação": ["restaurant", "cafe", "bakery"],
    "Farmácia":    ["hospital", "doctor", "dentist"],
    "Beleza":      ["clothing_store", "shopping_mall", "spa"],
    "Pet":         ["veterinary_care", "park"],
    "Eletrônicos": ["shopping_mall", "department_store"],
    "Saúde":       ["pharmacy", "physiotherapist"],
    "Outro":       ["shopping_mall"],
}

# Âncoras de tráfego: geradores universais de fluxo (qualquer nicho)
ANCHOR_TYPES = ["shopping_mall", "supermarket", "bank", "subway_station", "bus_station"]

# Raio padrão para análise de mercado (em metros)
MARKET_ANALYSIS_RADIUS = 800

# Nº máximo de regiões top a analisar (limita uso de quota Places)
MARKET_ANALYSIS_TOP_N = 5

# ---------------------------------------------------------------------------
# Sazonalidade por nicho (índice 0-100 para cada mês Jan–Dez)
# ---------------------------------------------------------------------------
SAZONALIDADE_BY_NICHE: dict = {
    "Fitness":     [95, 90, 80, 70, 65, 55, 50, 55, 65, 70, 75, 80],
    "Infantil":    [75, 70, 65, 70, 75, 80, 90, 95, 85, 70, 75, 90],
    "Escolar":     [60, 60, 65, 70, 60, 50, 55, 90, 95, 80, 75, 60],
    "Alimentação": [80, 80, 85, 85, 85, 80, 80, 80, 85, 85, 90, 95],
    "Farmácia":    [85, 80, 80, 75, 70, 75, 80, 80, 80, 80, 85, 90],
    "Beleza":      [80, 85, 90, 85, 90, 80, 75, 75, 80, 85, 90, 95],
    "Pet":         [80, 80, 80, 85, 85, 80, 75, 75, 80, 80, 80, 85],
    "Eletrônicos": [70, 65, 65, 65, 65, 65, 70, 65, 70, 75, 85, 100],
    "Saúde":       [85, 80, 80, 75, 75, 70, 70, 75, 80, 80, 80, 85],
    "Outro":       [80, 75, 80, 80, 80, 75, 75, 75, 80, 80, 85, 90],
}

# ---------------------------------------------------------------------------
# Parâmetros de ROI estimado por nível de investimento
# ---------------------------------------------------------------------------
ROI_PARAMS: dict = {
    "baixo": {
        "custo_setup_min": 10000, "custo_setup_max": 30000,
        "faturamento_mensal_base": 8000, "margem": 0.30, "payback_meses": 18,
        "label": "até R$30 mil",
    },
    "medio": {
        "custo_setup_min": 30000, "custo_setup_max": 150000,
        "faturamento_mensal_base": 25000, "margem": 0.28, "payback_meses": 24,
        "label": "R$30k – R$150k",
    },
    "alto": {
        "custo_setup_min": 150000, "custo_setup_max": 500000,
        "faturamento_mensal_base": 80000, "margem": 0.25, "payback_meses": 30,
        "label": "acima de R$150k",
    },
}

# Clustering
CLUSTERING_CONFIG = {
    "min_clusters": 2,
    "max_clusters": 5,
    "default_clusters": 3,
    "min_samples_per_cluster": 20,
    "random_state": 42,
    "n_init": 20,
}

# Ranking de clusters
RANKING_WEIGHTS = {
    "poi_weight": 0.6,
    "class_weight": 0.4,
}

# Mapeamento de classe social para valores ordinais
CLASS_ORDINAL = {
    "A": 5,
    "B": 4,
    "C": 3,
    "D": 2,
    "E": 1,
}

# Pesos padrão por classe (para heatmap)
DEFAULT_CLASS_WEIGHTS = {
    "A": 50000,
    "B": 20000,
    "C": 10000,
    "D": 5000,
    "E": 1000,
}

# Cache
CACHE_CONFIG = {
    "cache_file": CACHE_DIR / "cache_places.parquet",
    "max_age_days": 30,  # Cache expira após 30 dias
}

# Mapas
MAP_CONFIG = {
    "default_center": [-3.7319, -38.5267],  # Fortaleza
    "default_zoom": 12,
    "tiles": "cartodbpositron",
    "heatmap": {
        "radius": 22,
        "blur": 24,
        "max_zoom": 14,
        "min_opacity": 0.2,
    },
    "marker": {
        "icon": "shopping-cart",
        "prefix": "fa",
    }
}

# Cores para visualização
COLORS = {
    "cluster_palette": ["#d73027", "#fc8d59", "#fee090", "#91bfdb", "#4575b4", "#1a9850", "#66bd63", "#f46d43"],
    "class_colors": {
        "A": "green",
        "B": "orange",
        "C": "red",
        "D": "blue",
        "E": "gray",
    },
    "priority_colors": {
        1: "#f39c12",  # Ouro
        2: "#c0392b",  # Prata
        3: "#8e44ad",  # Bronze
        4: "#2980b9",
        5: "#16a085",
    }
}

# Interface Streamlit
STREAMLIT_CONFIG = {
    "page_title": "Smart Sale Fortaleza",
    "page_icon": "./assets/sale_icon_264139.png",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# Bairros conhecidos de Fortaleza
FORTALEZA_BAIRROS = [
    "Aldeota", "Meireles", "Centro", "Varjota", "Montese",
    "Messejana", "Barra do Ceará", "Papicu", "Cocó", "Dionísio Torres",
    "Joaquim Távora", "Fátima", "Benfica", "José Bonifácio", "Parquelândia",
    "Praia de Iracema", "Mucuripe", "Guararapes", "João XXIII", "Maraponga",
    "Henrique Jorge", "Bom Futuro", "Damas", "Serrinha", "Parque Dois Irmãos"
]

# Tipos comerciais conhecidos
TIPOS_COMERCIAIS = [
    "PEQUENOS REGIONAIS",
    "SUPER REGIONAIS",
    "HIPERMERCADO",
    "ATACAREJO",
    "FARMACIA",
    "DROGARIA",
    "ACADEMIA",
    "CONVENIENCIA",
]

# Validação
def validate_config():
    """Valida configurações essenciais."""
    warnings = []
    
    if not GOOGLE_API_KEY:
        warnings.append("⚠️  GOOGLE_API_KEY não configurada - funcionalidades de POI desabilitadas")
    
    if not DATA_DIR.exists():
        warnings.append(f"⚠️  Diretório de dados não encontrado: {DATA_DIR}")
    
    return warnings


# Executa validação ao importar
_warnings = validate_config()
if _warnings:
    for warning in _warnings:
        print(warning)
