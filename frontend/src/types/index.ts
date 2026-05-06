export interface Region {
  id: string;
  name: string;
  score: number;
  potential: number;
  lat: number;
  lng: number;
  socialClass: 'A' | 'B' | 'C' | 'D' | 'E';
  commercialType: string;
  pois: number;
  population: number;
  competitors: number;
}

export interface ClusteringMetrics {
  algoritmo?: string;
  justificativa?: string;
  silhouette?: number;
  davies_bouldin?: number;
  n_clusters?: number;
  elbow?: Record<string, number>;
  kmeans_silhouette?: number;
  dbscan_silhouette?: number;
}

export interface AnalysisResult {
  product: string;
  niche: string;
  totalRegions: number;
  avgScore: number;
  topNeighborhood: string;
  topCommercialType: string;
  regions: Region[];
  insights: string[];
  actionPlan: ActionItem[];
  strategy: Strategy;
  demographics: Demographics;
  // Métricas ML da API
  metricas_clustering?: ClusteringMetrics;
  nlp_confianca?: number;
  nlp_metodo?: string;
}

export interface ActionItem {
  id: string;
  text: string;
  checked: boolean;
}

export interface Strategy {
  summary: string;
  executiveSummary: string;
  targetAudience: string;
  recommendations: string[];
  nextSteps: string[];
  marketPotential: string;
}

export interface Demographics {
  socialClasses: { name: string; value: number; fill: string }[];
  commercialTypes: { name: string; count: number; fill: string }[];
}

export interface Filters {
  socialClasses: string[];
  commercialTypes: string[];
  neighborhoods: string[];
}
