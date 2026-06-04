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

from nlp import analisar_produto_completo, gerar_estrategia_comercial, identificar_nicho_com_confianca, extrair_produto_do_contexto  # noqa: E402
from clustering_pipeline import gerar_regioes_ideais_com_metricas  # noqa: E402
from config import SAZONALIDADE_BY_NICHE, ROI_PARAMS  # noqa: E402


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
    analise_mercado: Optional[dict] = Field(
        default=None,
        description="Análise de mercado via Google Places (concorrentes, sinergias, âncoras)",
    )


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


class GridPoint(BaseModel):
    """Representa um ponto da grade de 30 pontos de Fortaleza com score para heatmap."""
    lat: float
    lon: float
    poi_count: int = Field(description="Número absoluto de POIs do nicho neste ponto")
    score: float = Field(description="Score normalizado 0-100 para visualização")


class AnalyzeResponse(BaseModel):
    produto: str
    analise: Analysis
    regioes: List[Region]
    total_regioes: int
    metricas_clustering: Optional[ClusteringMetrics] = None
    sazonalidade: Optional[List[int]] = Field(
        default=None,
        description="Índices sazonais mensais 0-100 (Jan-Dez) para o nicho",
    )
    grid_points: Optional[List[GridPoint]] = Field(
        default=None,
        description="Todos os 30 pontos da grade de Fortaleza com scores para heatmap",
    )


class ROIRequest(BaseModel):
    nicho: str
    investimento: str = Field(default="medio", description="baixo | medio | alto")
    avg_score: float = Field(default=70.0, ge=0, le=100)


class ROIResponse(BaseModel):
    custo_setup_min: int
    custo_setup_max: int
    faturamento_m1: int
    faturamento_m6: int
    faturamento_m12: int
    payback_meses: int
    lucro_liquido_m12: int
    margem: float
    label_investimento: str
    premissas: List[str]


class StrategyRequest(BaseModel):
    produto: str
    nicho: str
    regioes: List[Region] = Field(default_factory=list)
    pesos_classe: dict = Field(default_factory=dict)
    filtros: Optional[Filters] = None
    contexto_negocio: Optional[dict] = Field(default=None, description="Contexto do negócio (descrição, objetivo, investimento)")


class StrategyResponse(BaseModel):
    estrategia: str


class BusinessContext(BaseModel):
    """Contexto livre informado pelo usuário no modo guiado (chat)."""
    descricao_negocio: str = Field(..., min_length=10, max_length=2000)
    objetivo: Optional[str] = Field(default=None, description="expandir | testar | primeiro_ponto")
    investimento: Optional[str] = Field(default=None, description="baixo | medio | alto")


class ContextAnalyzeRequest(BaseModel):
    contexto: BusinessContext
    filtros: Filters = Field(default_factory=Filters)


class ContextAnalyzeResponse(AnalyzeResponse):
    """Resposta do modo guiado: igual ao /analyze + produto extraído + estratégia."""
    produto_extraido: str
    publico_alvo_inferido: Optional[str] = None
    palavras_chave: Optional[str] = None
    estrategia: Optional[str] = None


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
        regioes, metricas_raw, grid_points = gerar_regioes_ideais_com_metricas(
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
            sazonalidade=SAZONALIDADE_BY_NICHE.get(analise["nicho"], SAZONALIDADE_BY_NICHE["Outro"]),
            grid_points=[GridPoint(**gp) for gp in grid_points] if grid_points else None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro no pipeline: {exc}") from exc


@app.post("/roi/estimate", response_model=ROIResponse, tags=["analysis"])
def roi_estimate(payload: ROIRequest) -> ROIResponse:
    """Estima ROI simplificado com base no nível de investimento e score médio."""
    params = ROI_PARAMS.get(payload.investimento, ROI_PARAMS["medio"])
    score_mult = 0.5 + 0.5 * max(0.0, min(1.0, payload.avg_score / 100.0))
    fat_base = params["faturamento_mensal_base"]
    margem = params["margem"]

    fat_m1 = int(fat_base * score_mult * 0.6)   # mês 1 é ramp-up
    fat_m6 = int(fat_base * score_mult * 0.85 * 6)
    fat_m12 = int(fat_base * score_mult * 12)
    lucro_m12 = int(fat_m12 * margem - params["custo_setup_min"])

    return ROIResponse(
        custo_setup_min=params["custo_setup_min"],
        custo_setup_max=params["custo_setup_max"],
        faturamento_m1=fat_m1,
        faturamento_m6=fat_m6,
        faturamento_m12=fat_m12,
        payback_meses=params["payback_meses"],
        lucro_liquido_m12=max(0, lucro_m12),
        margem=margem,
        label_investimento=params["label"],
        premissas=[
            f"Investimento: {params['label']}",
            f"Faturamento base mensal do nicho estimado em R${fat_base:,.0f}",
            f"Fator de localização (score {payload.avg_score:.0f}/100): {score_mult:.2f}x",
            f"Margem líquida estimada: {margem*100:.0f}%",
            "Valores são estimativas para planejamento — valide com pesquisa de campo.",
        ],
    )


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
            contexto_negocio=payload.contexto_negocio,
        )
        return StrategyResponse(estrategia=texto)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/analyze/context", response_model=ContextAnalyzeResponse, tags=["analysis"])
def analyze_context(payload: ContextAnalyzeRequest) -> ContextAnalyzeResponse:
    """
    Modo guiado: recebe descrição livre do negócio + objetivo + investimento.
    Extrai o produto via OpenAI, executa o pipeline completo (NLP + clustering)
    e gera estratégia comercial enriquecida com o contexto.
    """
    desc = (payload.contexto.descricao_negocio or "").strip()
    if len(desc) < 10:
        raise HTTPException(status_code=400, detail="Descrição do negócio muito curta (mínimo 10 caracteres)")

    try:
        # 1. Extrai produto/público/keywords do contexto
        extraido = extrair_produto_do_contexto(desc)
        produto = extraido.get("produto") or desc[:60]

        # 2. Pipeline NLP + clustering padrão
        analise = analisar_produto_completo(produto)
        nlp_info = identificar_nicho_com_confianca(produto)
        filtros_dict = payload.filtros.model_dump()
        regioes, metricas_raw, grid_points = gerar_regioes_ideais_com_metricas(
            produto, filtros_dict, analise["nicho"]
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

        # 3. Estratégia enriquecida com contexto
        contexto_dict = {
            "descricao_negocio": desc,
            "objetivo": payload.contexto.objetivo,
            "investimento": payload.contexto.investimento,
            "publico_alvo": extraido.get("publico_alvo", ""),
        }
        estrategia_texto = gerar_estrategia_comercial(
            produto=produto,
            nicho=analise["nicho"],
            regioes=regioes,
            pesos_classe=analise["pesos_classe"],
            filtros=filtros_dict,
            contexto_negocio=contexto_dict,
        )

        return ContextAnalyzeResponse(
            produto=produto,
            produto_extraido=produto,
            publico_alvo_inferido=extraido.get("publico_alvo") or None,
            palavras_chave=extraido.get("palavras_chave") or None,
            analise=Analysis(
                **analise,
                nlp_confianca=nlp_info.get("confianca"),
                nlp_metodo=nlp_info.get("metodo"),
            ),
            regioes=[Region(**r) for r in regioes],
            total_regioes=len(regioes),
            metricas_clustering=metricas,
            estrategia=estrategia_texto,
            sazonalidade=SAZONALIDADE_BY_NICHE.get(analise["nicho"], SAZONALIDADE_BY_NICHE["Outro"]),
            grid_points=[GridPoint(**gp) for gp in grid_points] if grid_points else None,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erro no pipeline contextual: {exc}") from exc
