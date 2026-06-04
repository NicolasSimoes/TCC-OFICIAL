/**
 * Cliente da API REST (FastAPI) do Smart Sale Fortaleza.
 *
 * Endpoint base configurável via variável de ambiente Vite:
 *   VITE_API_BASE_URL (default: http://localhost:8000)
 *
 * Em caso de falha de rede/backend, o caller pode optar por usar dados mock.
 */

import {
  AnalysisResult,
  Region,
  Filters,
  ActionItem,
  Strategy,
  Demographics,
  ClusteringMetrics,
  ROIEstimate,
} from '@/types';

const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL?.replace(/\/$/, '') ||
  'http://localhost:8000';

// ---------------------------------------------------------------------------
// Tipos do backend (snake_case)
// ---------------------------------------------------------------------------
interface BackendRegion {
  lat: number;
  lon: number;
  nome: string;
  motivo?: string | null;
  cluster?: number | null;
  score?: number | null;
  classe_med?: number | null;
  poi_med?: number | null;
  tipo_comercial?: string | null;
  classe_social?: string | null;
  analise_mercado?: {
    competitors: number;
    synergies: number;
    anchors: number;
    density: number;
    saturacao: 'vazio' | 'baixa' | 'media' | 'alta';
    raio_m: number;
    insight: string;
    competitor_names?: string[];
  } | null;
}

interface BackendAnalysis {
  nicho: string;
  pois_sugeridos: string[];
  pesos_classe: Record<string, number>;
  descricao: string;
  nlp_confianca?: number | null;
  nlp_metodo?: string | null;
}

interface BackendClusteringMetrics {
  algoritmo?: string | null;
  justificativa?: string | null;
  silhouette?: number | null;
  davies_bouldin?: number | null;
  n_clusters?: number | null;
  elbow?: Record<string, number> | null;
  kmeans_silhouette?: number | null;
  dbscan_silhouette?: number | null;
}

interface BackendAnalyzeResponse {
  produto: string;
  analise: BackendAnalysis;
  regioes: BackendRegion[];
  total_regioes: number;
  metricas_clustering?: BackendClusteringMetrics | null;
  sazonalidade?: number[] | null;
  grid_points?: Array<{
    lat: number;
    lon: number;
    poi_count: number;
    score: number;
  }> | null;
}

// ---------------------------------------------------------------------------
// HTTP helper
// ---------------------------------------------------------------------------
async function postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`API ${path} ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Mappers backend → frontend
// ---------------------------------------------------------------------------
function isValidClass(c: unknown): c is Region['socialClass'] {
  return c === 'A' || c === 'B' || c === 'C' || c === 'D' || c === 'E';
}

function mapRegion(r: BackendRegion, idx: number): Region {
  const score = r.score ?? 0;
  // Backend agora retorna score em [0, 100] diretamente (score por linha normalizado)
  const score100 = Math.max(0, Math.min(100, Math.round(score * 10) / 10));
  return {
    id: `region-${idx + 1}`,
    name: r.nome || `Região ${idx + 1}`,
    score: score100,
    potential: Math.round((score100 * 0.95) * 10) / 10,
    lat: r.lat,
    lng: r.lon,
    socialClass: isValidClass(r.classe_social) ? r.classe_social : 'C',
    commercialType: r.tipo_comercial || 'Outros',
    pois: Math.round((r.poi_med ?? 0) * 100),
    population: 0,
    competitors: r.analise_mercado?.competitors ?? 0,
    marketAnalysis: r.analise_mercado
      ? {
          competitors: r.analise_mercado.competitors,
          synergies: r.analise_mercado.synergies,
          anchors: r.analise_mercado.anchors,
          density: r.analise_mercado.density,
          saturacao: r.analise_mercado.saturacao,
          raio_m: r.analise_mercado.raio_m,
          insight: r.analise_mercado.insight,
          competitor_names: r.analise_mercado.competitor_names ?? [],
        }
      : undefined,
  };
}

function buildInsights(product: string, niche: string, regions: Region[]): string[] {
  if (regions.length === 0) {
    return [`Nenhuma região encontrada para "${product}" no nicho ${niche} com os filtros atuais.`];
  }
  const top = regions[0];
  const avg = regions.reduce((s, r) => s + r.score, 0) / regions.length;
  const ab = regions.filter(r => r.socialClass === 'A' || r.socialClass === 'B').length;
  return [
    `Nicho "${niche}" tem maior potencial em ${top.name.split(' - ')[0]} (score ${top.score.toFixed(1)}).`,
    `${ab} de ${regions.length} regiões (${((ab / regions.length) * 100).toFixed(0)}%) estão em classes A/B.`,
    `Score médio: ${avg.toFixed(1)} pontos.`,
    `Total de ${regions.length} pontos georreferenciados pelo pipeline de clustering.`,
  ];
}

function buildDemographics(regions: Region[]): Demographics {
  const classCount: Record<string, number> = { A: 0, B: 0, C: 0, D: 0, E: 0 };
  const typeCount: Record<string, number> = {};
  regions.forEach(r => {
    classCount[r.socialClass] = (classCount[r.socialClass] || 0) + 1;
    typeCount[r.commercialType] = (typeCount[r.commercialType] || 0) + 1;
  });
  const classColors: Record<string, string> = {
    A: 'hsl(142, 71%, 45%)',
    B: 'hsl(217, 91%, 60%)',
    C: 'hsl(45, 93%, 47%)',
    D: 'hsl(24, 94%, 50%)',
    E: 'hsl(0, 84%, 60%)',
  };
  return {
    socialClasses: Object.entries(classCount).map(([k, v]) => ({
      name: `Classe ${k}`,
      value: v,
      fill: classColors[k],
    })),
    commercialTypes: Object.entries(typeCount).map(([k, v]) => ({
      name: k,
      count: v,
      fill: 'hsl(215, 20%, 65%)',
    })),
  };
}

function defaultActionPlan(product: string, niche: string): ActionItem[] {
  return [
    { id: '1', text: `Visitar as 3 regiões com maior score para análise de campo`, checked: false },
    { id: '2', text: `Mapear concorrentes diretos no nicho ${niche}`, checked: false },
    { id: '3', text: `Validar viabilidade de ponto comercial nas zonas top`, checked: false },
    { id: '4', text: `Desenhar piloto de venda de ${product}`, checked: false },
    { id: '5', text: `Estabelecer parcerias com estabelecimentos locais`, checked: false },
  ];
}

function buildStrategyFromText(product: string, niche: string, regions: Region[], text: string): Strategy {
  const top = regions.slice(0, 5).map(r => r.name.split(' - ')[0]);
  const avg = regions.length ? regions.reduce((s, r) => s + r.score, 0) / regions.length : 0;
  return {
    summary: `Pipeline encontrou ${regions.length} pontos para "${product}" (nicho ${niche}). Score médio: ${avg.toFixed(1)}.`,
    executiveSummary: text || `Análise de ${product} no nicho ${niche}. Top regiões: ${top.join(', ') || '—'}.`,
    targetAudience: `Inferido pelos pesos de classe do pipeline: foco nas regiões de classe predominante identificadas.`,
    marketPotential: `Estimativa baseada nos clusters do KMeans e enriquecimento de POIs (Google Places).`,
    recommendations: [
      `Priorizar atuação em ${top[0] || 'cluster top 1'}`,
      `Validar com pesquisa de campo nas 3 zonas de maior score`,
      `Considerar enriquecer dados com Google Places API para refinar score`,
      `Avaliar parcerias e modelos de canal local`,
    ],
    nextSteps: [
      `Semana 1-2: Pesquisa de campo nas regiões prioritárias`,
      `Semana 3-4: Teste piloto em 3-5 pontos`,
      `Mês 2+: Expansão progressiva conforme tração`,
    ],
  };
}

// ---------------------------------------------------------------------------
// API pública
// ---------------------------------------------------------------------------

export interface AnalyzeOptions {
  filters?: Filters;
  signal?: AbortSignal;
  /** Se true, também solicita /strategy (mais lento). */
  withStrategy?: boolean;
  /** Se true, enriquece com Google Places API no backend (+15-30s). */
  usarApi?: boolean;
}

export async function analyzeProduct(
  query: string,
  options: AnalyzeOptions = {},
): Promise<AnalysisResult> {
  const filtros = {
    classe: options.filters?.socialClasses ?? [],
    tipo:
      options.filters?.commercialTypes?.length === 1
        ? options.filters.commercialTypes[0]
        : null,
    bairro: options.filters?.neighborhoods ?? [],
    usar_api: options.usarApi ?? false,
  };

  const data = await postJson<BackendAnalyzeResponse>(
    '/analyze',
    { produto: query, filtros },
    options.signal,
  );

  const regions = data.regioes.map(mapRegion);
  const product = data.produto;
  const niche = data.analise.nicho;

  // Estratégia opcional (chamada extra)
  let estrategiaText = '';
  if (options.withStrategy) {
    try {
      const r = await postJson<{ estrategia: string }>(
        '/strategy',
        {
          produto: product,
          nicho: niche,
          regioes: data.regioes,
          pesos_classe: data.analise.pesos_classe,
          filtros,
        },
        options.signal,
      );
      estrategiaText = r.estrategia || '';
    } catch (e) {
      console.warn('Falha ao gerar estratégia, usando fallback:', e);
    }
  }

  // Top neighborhood / commercialType
  const top = regions[0];
  const typeCount: Record<string, number> = {};
  regions.forEach(r => (typeCount[r.commercialType] = (typeCount[r.commercialType] || 0) + 1));
  const topType =
    Object.entries(typeCount).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A';

  // Mapeia métricas de clustering (se disponíveis)
  const metricas_clustering: ClusteringMetrics | undefined =
    data.metricas_clustering
      ? {
          algoritmo: data.metricas_clustering.algoritmo ?? undefined,
          justificativa: data.metricas_clustering.justificativa ?? undefined,
          silhouette: data.metricas_clustering.silhouette ?? undefined,
          davies_bouldin: data.metricas_clustering.davies_bouldin ?? undefined,
          n_clusters: data.metricas_clustering.n_clusters ?? undefined,
          elbow: data.metricas_clustering.elbow ?? undefined,
          kmeans_silhouette: data.metricas_clustering.kmeans_silhouette ?? undefined,
          dbscan_silhouette: data.metricas_clustering.dbscan_silhouette ?? undefined,
        }
      : undefined;

  return {
    product,
    niche,
    totalRegions: regions.length,
    avgScore:
      regions.length === 0
        ? 0
        : Math.round((regions.reduce((s, r) => s + r.score, 0) / regions.length) * 10) / 10,
    topNeighborhood: top ? top.name.split(' - ')[0] : '—',
    topCommercialType: topType,
    regions,
    insights: buildInsights(product, niche, regions),
    actionPlan: defaultActionPlan(product, niche),
    strategy: buildStrategyFromText(product, niche, regions, estrategiaText),
    demographics: buildDemographics(regions),
    metricas_clustering,
    nlp_confianca: data.analise.nlp_confianca ?? undefined,
    nlp_metodo: data.analise.nlp_metodo ?? undefined,
    sazonalidade: data.sazonalidade ?? undefined,
    gridPoints: data.grid_points?.map(gp => ({
      lat: gp.lat,
      lon: gp.lon,
      poi_count: gp.poi_count,
      score: gp.score,
    })) ?? undefined,
  };
}

export async function pingApi(signal?: AbortSignal): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { signal });
    return res.ok;
  } catch {
    return false;
  }
}

// ---------------------------------------------------------------------------
// Modo guiado (chat por contexto)
// ---------------------------------------------------------------------------

export interface BusinessContextPayload {
  descricao: string;
  objetivo: 'expandir' | 'testar' | 'primeiro_ponto';
  investimento: 'baixo' | 'medio' | 'alto';
}

interface BackendContextResponse extends BackendAnalyzeResponse {
  produto_extraido: string;
  publico_alvo_inferido?: string | null;
  palavras_chave?: string | null;
  estrategia?: string | null;
}

export async function analyzeByContext(
  ctx: BusinessContextPayload,
  options: { filters?: Filters; signal?: AbortSignal; usarApi?: boolean } = {},
): Promise<AnalysisResult> {
  const filtros = {
    classe: options.filters?.socialClasses ?? [],
    tipo:
      options.filters?.commercialTypes?.length === 1
        ? options.filters.commercialTypes[0]
        : null,
    bairro: options.filters?.neighborhoods ?? [],
    usar_api: options.usarApi ?? false,
  };

  const data = await postJson<BackendContextResponse>(
    '/analyze/context',
    {
      contexto: {
        descricao_negocio: ctx.descricao,
        objetivo: ctx.objetivo,
        investimento: ctx.investimento,
      },
      filtros,
    },
    options.signal,
  );

  const regions = data.regioes.map(mapRegion);
  const product = data.produto_extraido || data.produto;
  const niche = data.analise.nicho;

  const top = regions[0];
  const typeCount: Record<string, number> = {};
  regions.forEach(r => (typeCount[r.commercialType] = (typeCount[r.commercialType] || 0) + 1));
  const topType =
    Object.entries(typeCount).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A';

  const metricas_clustering: ClusteringMetrics | undefined = data.metricas_clustering
    ? {
        algoritmo: data.metricas_clustering.algoritmo ?? undefined,
        justificativa: data.metricas_clustering.justificativa ?? undefined,
        silhouette: data.metricas_clustering.silhouette ?? undefined,
        davies_bouldin: data.metricas_clustering.davies_bouldin ?? undefined,
        n_clusters: data.metricas_clustering.n_clusters ?? undefined,
        elbow: data.metricas_clustering.elbow ?? undefined,
        kmeans_silhouette: data.metricas_clustering.kmeans_silhouette ?? undefined,
        dbscan_silhouette: data.metricas_clustering.dbscan_silhouette ?? undefined,
      }
    : undefined;

  return {
    product,
    niche,
    totalRegions: regions.length,
    avgScore:
      regions.length === 0
        ? 0
        : Math.round((regions.reduce((s, r) => s + r.score, 0) / regions.length) * 10) / 10,
    topNeighborhood: top ? top.name.split(' - ')[0] : '—',
    topCommercialType: topType,
    regions,
    insights: buildInsights(product, niche, regions),
    actionPlan: defaultActionPlan(product, niche),
    strategy: buildStrategyFromText(product, niche, regions, data.estrategia || ''),
    demographics: buildDemographics(regions),
    metricas_clustering,
    nlp_confianca: data.analise.nlp_confianca ?? undefined,
    nlp_metodo: data.analise.nlp_metodo ?? undefined,
    sazonalidade: (data as any).sazonalidade ?? undefined,
    investimento: ctx.investimento,
    gridPoints: data.grid_points?.map(gp => ({
      lat: gp.lat,
      lon: gp.lon,
      poi_count: gp.poi_count,
      score: gp.score,
    })) ?? undefined,
  };
}

export const API_BASE = API_BASE_URL;

// ---------------------------------------------------------------------------
// ROI estimado
// ---------------------------------------------------------------------------
export async function estimateROI(
  nicho: string,
  investimento: string,
  avgScore: number,
  signal?: AbortSignal,
): Promise<ROIEstimate> {
  const data = await postJson<{
    custo_setup_min: number;
    custo_setup_max: number;
    faturamento_m1: number;
    faturamento_m6: number;
    faturamento_m12: number;
    payback_meses: number;
    lucro_liquido_m12: number;
    margem: number;
    label_investimento: string;
    premissas: string[];
  }>('/roi/estimate', { nicho, investimento, avg_score: avgScore }, signal);
  return {
    custoSetupMin: data.custo_setup_min,
    custoSetupMax: data.custo_setup_max,
    faturamentoM1: data.faturamento_m1,
    faturamentoM6: data.faturamento_m6,
    faturamentoM12: data.faturamento_m12,
    paybackMeses: data.payback_meses,
    lucroLiquidoM12: data.lucro_liquido_m12,
    margem: data.margem,
    labelInvestimento: data.label_investimento,
    premissas: data.premissas,
  };
}
