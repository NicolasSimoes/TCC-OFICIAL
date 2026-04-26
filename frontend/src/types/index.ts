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
