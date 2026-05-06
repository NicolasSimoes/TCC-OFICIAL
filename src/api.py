"""
API REST FastAPI para o Smart Sale Fortaleza.

Expõe o pipeline de análise (NLP + clustering + geomarketing) como endpoints
HTTP, permitindo que o frontend React (ou qualquer outro cliente) consuma os
resultados sem depender do Streamlit.

Como executar:
    uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

ou:
    python -m uvicorn api:app --reload   (de dentro de src/)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Garante que o diretório src/ esteja no path quando executado de fora.
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from nlp import analisar_produto_completo, gerar_estrategia_comercial, identificar_nicho_com_confianca  # noqa: E402
from clustering_pipeline import gerar_regioes_ideais_com_metricas  # noqa: E402


# ---------------------------------------------------------------------------
# Schemas (Pydantic)
# ---------------------------------------------------------------------------

class Filters(BaseModel):
    """Filtros opcionais aplicados sobre a base."""
    classe: List[str] = Field(default_factory=list, description="Classes sociais (A-E)")
    tipo: Optional[str] = Field(default=None, description="Tipo comercial")
    bairro: List[str] = Field(default_factory=list, description="Bairros alvo")
    usar_api: bool = Field(default=False, description="Enriquecer com Google Places API")


class AnalyzeRequest(BaseModel):
    produto: str = Field(..., min_length=1, max_length=200)
    filtros: Filters = Field(default_factory=Filters)


class Region(BaseModel):
    lat: float
    lon: float
    nome: str
    motivo: Optional[str] = None
    cluster: Optional[int] = None
    score: Optional[float] = None
    classe_med: Optional[float] = None
    poi_med: Optional[float] = None
    tipo_comercial: Optional[str] = None
    classe_social: Optional[str] = None


class Analysis(BaseModel):
    nicho: str
    pois_sugeridos: List[str]
    pesos_classe: dict
    descricao: str
    # Metadados do classificador NLP
    nlp_confianca: Optional[float] = None
    nlp_metodo: Optional[str] = None


class ClusteringMetrics(BaseModel):
    """Métricas de qualidade do clustering retornadas pela API."""
    algoritmo: Optional[str] = None
    justificativa: Optional[str] = None
    silhouette: Optional[float] = Field(default=None, description="[-1,1] — quanto maior, melhor separação")
    davies_bouldin: Optional[float] = Field(default=None, description="[0,∞) — quanto menor, mais compacto")
    n_clusters: Optional[int] = None
    elbow: Optional[dict] = Field(default=None, description="{k: inertia} para o Elbow Method")
    kmeans_silhouette: Optional[float] = None
    dbscan_silhouette: Optional[float] = None


class AnalyzeResponse(BaseModel):
    produto: str
    analise: Analysis
    regioes: List[Region]
    total_regioes: int
    metricas_clustering: Optional[ClusteringMetrics] = None


class StrategyRequest(BaseModel):
    produto: str
    nicho: str
    regioes: List[Region] = Field(default_factory=list)
    pesos_classe: dict = Field(default_factory=dict)
    filtros: Optional[Filters] = None


class StrategyResponse(BaseModel):
    estrategia: str


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def _cors_origins() -> List[str]:
    raw = os.getenv(
        "API_CORS_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://localhost:3000",
    )
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    # Em desenvolvimento, aceita qualquer porta localhost (5173-5200)
    for port in range(5173, 5201):
        candidate = f"http://localhost:{port}"
        if candidate not in origins:
            origins.append(candidate)
    return origins


app = FastAPI(
    title="Smart Sale Fortaleza API",
    version="1.1.0",
    description="API REST que expõe o pipeline de geomarketing inteligente.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "google_api_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "openai_api_configured": bool(os.getenv("OPENAI_API_KEY")),
    }


@app.post("/analyze/product", response_model=Analysis, tags=["analysis"])
def analyze_product(payload: AnalyzeRequest) -> Analysis:
    """Apenas classifica o produto (rápido, sem clustering)."""
    try:
        result = analisar_produto_completo(payload.produto)
        nlp_info = identificar_nicho_com_confianca(payload.produto)
        return Analysis(
            **result,
            nlp_confianca=nlp_info.get("confianca"),
            nlp_metodo=nlp_info.get("metodo"),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analyze", response_model=AnalyzeResponse, tags=["analysis"])
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    """Pipeline completo: NLP + clustering + ranqueamento de regiões."""
    if not payload.produto.strip():
        raise HTTPException(status_code=400, detail="Produto não informado")

    try:
        analise = analisar_produto_completo(payload.produto)
        nlp_info = identificar_nicho_com_confianca(payload.produto)
        filtros_dict = payload.filtros.model_dump()
        regioes, metricas_raw = gerar_regioes_ideais_com_metricas(
            payload.produto, filtros_dict, analise["nicho"]
        )
        metricas: Optional[ClusteringMetrics] = None
        if metricas_raw:
            km_info = metricas_raw.get("kmeans", {})
            db_info = metricas_raw.get("dbscan", {})
            metricas = ClusteringMetrics(
                algoritmo=metricas_raw.get("algoritmo"),
                justificativa=metricas_raw.get("justificativa"),
                silhouette=metricas_raw.get("silhouette"),
                davies_bouldin=metricas_raw.get("davies_bouldin"),
                n_clusters=km_info.get("n_clusters"),
                elbow=metricas_raw.get("elbow"),
                kmeans_silhouette=km_info.get("silhouette"),
                dbscan_silhouette=db_info.get("silhouette"),
            )
        return AnalyzeResponse(
            produto=payload.produto,
            analise=Analysis(
                **analise,
                nlp_confianca=nlp_info.get("confianca"),
                nlp_metodo=nlp_info.get("metodo"),
            ),
            regioes=[Region(**r) for r in regioes],
            total_regioes=len(regioes),
            metricas_clustering=metricas,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro no pipeline: {exc}") from exc


@app.post("/strategy", response_model=StrategyResponse, tags=["analysis"])
def strategy(payload: StrategyRequest) -> StrategyResponse:
    """Gera estratégia comercial (usa OpenAI se disponível, com fallback)."""
    try:
        regioes = [r.model_dump() for r in payload.regioes]
        filtros = payload.filtros.model_dump() if payload.filtros else None
        texto = gerar_estrategia_comercial(
            produto=payload.produto,
            nicho=payload.nicho,
            regioes=regioes,
            pesos_classe=payload.pesos_classe,
            filtros=filtros,
        )
        return StrategyResponse(estrategia=texto)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
