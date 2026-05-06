import { useState, useEffect, useRef } from 'react';
import { AppHeader } from '@/components/AppHeader';
import { SearchBar } from '@/components/SearchBar';
import { MetricsCards } from '@/components/MetricsCards';
import { MLMetrics } from '@/components/MLMetrics';
import { AnalysisDetails } from '@/components/AnalysisDetails';
import { MapView } from '@/components/MapView';
import { StrategyTabs } from '@/components/StrategyTabs';
import { MarketInsights } from '@/components/MarketInsights';
import { ActionPlan } from '@/components/ActionPlan';
import { generateMockAnalysis } from '@/lib/mock-data';
import { analyzeProduct, pingApi } from '@/lib/api';
import { AnalysisResult, Region } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertCircle } from 'lucide-react';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [focusRegion, setFocusRegion] = useState<Region | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    pingApi().then(setApiOnline);
  }, []);

  const handleSearch = async (query: string, usarApi: boolean = false) => {
    setIsLoading(true);
    setFocusRegion(null);
    let analysisResult: AnalysisResult;
    try {
      analysisResult = await analyzeProduct(query, { withStrategy: true, usarApi });
      setApiOnline(true);
    } catch {
      setApiOnline(false);
      await new Promise((r) => setTimeout(r, 600));
      analysisResult = generateMockAnalysis(query);
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
          <p className="text-muted-foreground mb-8 text-sm">
            Pipeline de geomarketing com NLP, clustering e dados geoespaciais de Fortaleza
          </p>
          <SearchBar onSearch={handleSearch} isLoading={isLoading} />
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
                />
              </section>

              <StrategyTabs
                regions={result.regions}
                strategy={result.strategy}
                demographics={result.demographics}
                onFocusRegion={handleFocusRegion}
              />

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <MarketInsights insights={result.insights} />
                <ActionPlan
                  actions={result.actionPlan}
                  storageKey={`smart-sale-${result.product}`}
                />
              </div>
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
            <p>Digite o nome de um produto e pressione Analisar</p>
            <p className="text-xs opacity-60">ex: whey protein · fralda · shampoo · notebook</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
