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
SEARCH_RADII = [400, 800, 1200]

# Tipos de POIs por nicho
PLACES_TYPES_BY_NICHE = {
    "Fitness": {
        "gym": ["gym", "health"],
        "office": ["bank", "real_estate_agency", "insurance_agency", "lawyer"],
        "university": ["university"],
        "supermarket": ["supermarket", "grocery_or_supermarket"],
    },
    "Infantil": {
        "school": ["school", "primary_school"],
        "park": ["park"],
        "supermarket": ["supermarket", "grocery_or_supermarket"],
        "health": ["hospital", "doctor"],
    },
    "Escolar": {
        "school": ["school", "university"],
        "library": ["library", "book_store"],
        "office": ["bank", "real_estate_agency"],
        "supermarket": ["supermarket"],
    },
    "Alimentação": {
        "supermarket": ["supermarket", "grocery_or_supermarket"],
        "restaurant": ["restaurant", "cafe", "bakery"],
        "office": ["bank", "real_estate_agency"],
    },
    "Farmácia": {
        "health": ["pharmacy", "drugstore", "hospital", "doctor"],
        "supermarket": ["supermarket"],
        "office": ["bank"],
    },
    "Beleza": {
        "beauty": ["beauty_salon", "hair_care", "spa"],
        "shopping": ["shopping_mall", "department_store"],
        "office": ["bank"],
    },
    "Pet": {
        "pet": ["pet_store", "veterinary_care"],
        "park": ["park"],
        "supermarket": ["supermarket"],
    },
    "Eletrônicos": {
        "electronics": ["electronics_store", "home_goods_store"],
        "shopping": ["shopping_mall", "department_store"],
        "office": ["bank", "real_estate_agency"],
    },
    "Outro": {
        "general": ["supermarket", "shopping_mall", "store"],
    }
}

# Tipo padrão para clustering
DEFAULT_PLACES_TYPES = {
    "gym": ["gym"],
    "office": ["bank", "real_estate_agency", "insurance_agency", "lawyer"],
    "university": ["university"],
    "supermarket": ["supermarket", "grocery_or_supermarket"],
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
