import { useState, useEffect, useRef } from 'react';
import { AppHeader } from '@/components/AppHeader';
import { BusinessChat, BusinessContextData } from '@/components/BusinessChat';
import { MetricsCards } from '@/components/MetricsCards';
import { MLMetrics } from '@/components/MLMetrics';
import { AnalysisDetails } from '@/components/AnalysisDetails';
import { MapView } from '@/components/MapView';
import { StrategyTabs } from '@/components/StrategyTabs';
import { MarketInsights } from '@/components/MarketInsights';
import { ActionPlan } from '@/components/ActionPlan';
import { MarketAnalysisInsights } from '@/components/MarketAnalysisInsights';
import { SeasonalityCard } from '@/components/SeasonalityCard';
import { FlowChart } from '@/components/FlowChart';
import { ROISimulator } from '@/components/ROISimulator';
import { CompareModal } from '@/components/CompareModal';
import { generateMockAnalysis } from '@/lib/mock-data';
import { analyzeByContext, pingApi } from '@/lib/api';
import { AnalysisResult, Region } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertCircle, FileDown, GitCompare } from 'lucide-react';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [focusRegion, setFocusRegion] = useState<Region | null>(null);
  const [showCompare, setShowCompare] = useState(false);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    pingApi().then(setApiOnline);
  }, []);

  const handleContextSubmit = async (ctx: BusinessContextData) => {
    setIsLoading(true);
    setFocusRegion(null);
    let analysisResult: AnalysisResult;
    try {
      analysisResult = await analyzeByContext(
        {
          descricao: ctx.descricao,
          objetivo: ctx.objetivo,
          investimento: ctx.investimento,
        },
        { usarApi: ctx.usarApi },
      );
      setApiOnline(true);
    } catch (e) {
      console.warn('Falha modo contexto, usando mock:', e);
      setApiOnline(false);
      await new Promise((r) => setTimeout(r, 600));
      analysisResult = generateMockAnalysis(ctx.descricao.slice(0, 40));
    }
    setResult(analysisResult);
    setIsLoading(false);
  };

  useEffect(() => {
    if (result && !isLoading && resultsRef.current) {
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 200);
    }
  }, [result, isLoading]);

  const handleFocusRegion = (region: Region) => {
    setFocusRegion(region);
    document.getElementById('map-section')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  return (
    <div className="min-h-screen bg-background">
      <AppHeader apiOnline={apiOnline} />

      <main className="mx-auto max-w-3xl px-4 py-10">

        {/* Hero + Search */}
        <section className="mb-10 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-foreground mb-2">
            Encontre o ponto ideal<br />
            <span className="text-primary">para o seu produto</span>
          </h1>
          <p className="text-muted-foreground mb-6 text-sm">
            Pipeline de geomarketing com NLP, clustering e dados geoespaciais de Fortaleza
          </p>

          <BusinessChat onSubmit={handleContextSubmit} isLoading={isLoading} />
        </section>

        {/* Loading skeleton */}
        {isLoading && (
          <div className="space-y-4 animate-pulse">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-20 rounded-lg bg-muted" />
              ))}
            </div>
            <div className="h-48 rounded-lg bg-muted" />
            <div className="h-72 rounded-lg bg-muted" />
          </div>
        )}

        {/* Results */}
        <AnimatePresence>
          {result && !isLoading && (
            <motion.div
              ref={resultsRef}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="space-y-6"
            >
              {/* Result header */}
              <div className="flex items-center gap-2 text-sm text-muted-foreground border-b pb-4">
                <CheckCircle className="h-4 w-4 text-primary shrink-0" />
                <span>
                  <strong className="text-foreground">{result.totalRegions} regiões</strong> identificadas para{' '}
                  <strong className="text-foreground">{result.product}</strong>{' '}
                  · nicho <span className="text-primary font-medium">{result.niche}</span>
                </span>
              </div>

              <MetricsCards
                totalRegions={result.totalRegions}
                avgScore={result.avgScore}
                topNeighborhood={result.topNeighborhood}
                topCommercialType={result.topCommercialType}
              />

              {apiOnline && result.metricas_clustering && (
                <MLMetrics
                  metrics={result.metricas_clustering}
                  nlpConfianca={result.nlp_confianca}
                  nlpMetodo={result.nlp_metodo}
                />
              )}

              <AnalysisDetails
                product={result.product}
                niche={result.niche}
                regions={result.regions}
                avgScore={result.avgScore}
              />

              <section id="map-section">
                <MapView
                  regions={result.regions}
                  focusRegion={focusRegion}
                  onRegionClick={setFocusRegion}
                  gridPoints={result.gridPoints}
                />
              </section>

              <MarketAnalysisInsights regions={result.regions} />

              <StrategyTabs
                regions={result.regions}
                strategy={result.strategy}
                demographics={result.demographics}
                onFocusRegion={handleFocusRegion}
              />

              {/* Sazonalidade + Fluxo */}
              {result.sazonalidade && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <SeasonalityCard sazonalidade={result.sazonalidade} niche={result.niche} />
                  <FlowChart niche={result.niche} />
                </div>
              )}
              {!result.sazonalidade && (
                <FlowChart niche={result.niche} />
              )}

              {/* ROI Simulator */}
              <ROISimulator
                niche={result.niche}
                avgScore={result.avgScore}
                investimento={result.investimento}
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <MarketInsights insights={result.insights} />
                <ActionPlan
                  actions={result.actionPlan}
                  storageKey={`smart-sale-${result.product}`}
                />
              </div>

              {/* Botões de ação */}
              <div className="flex flex-wrap gap-2 no-print pt-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="flex items-center gap-1.5 rounded-lg border px-4 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:border-primary/50 transition-all"
                >
                  <FileDown className="h-3.5 w-3.5" />
                  Exportar PDF
                </button>
                <button
                  type="button"
                  onClick={() => setShowCompare(true)}
                  className="flex items-center gap-1.5 rounded-lg border px-4 py-2 text-xs font-medium text-muted-foreground hover:text-foreground hover:border-primary/50 transition-all"
                >
                  <GitCompare className="h-3.5 w-3.5" />
                  Comparar "E se?"
                </button>
              </div>

              {/* Compare modal */}
              {showCompare && (
                <CompareModal original={result} onClose={() => setShowCompare(false)} />
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty state */}
        {!result && !isLoading && (
          <div className="mt-12 text-center text-muted-foreground text-sm space-y-1">
            {apiOnline === false && (
              <p className="flex items-center justify-center gap-1.5 text-amber-500">
                <AlertCircle className="h-4 w-4" /> Backend offline — usando dados de demonstração
              </p>
            )}
            <p className="text-xs opacity-60">Conte sobre seu negócio em 3 etapas — a IA extrai o produto e adapta a estratégia</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
