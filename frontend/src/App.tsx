import { useState, useEffect, useRef } from 'react';
import { AppHeader } from '@/components/AppHeader';
import { SearchBar } from '@/components/SearchBar';
import { FilterSidebar } from '@/components/FilterSidebar';
import { SuccessBanner } from '@/components/SuccessBanner';
import { MetricsCards } from '@/components/MetricsCards';
import { AnalysisDetails } from '@/components/AnalysisDetails';
import { MapView } from '@/components/MapView';
import { StrategyTabs } from '@/components/StrategyTabs';
import { MarketInsights } from '@/components/MarketInsights';
import { ActionPlan } from '@/components/ActionPlan';
import { generateMockAnalysis } from '@/lib/mock-data';
import { AnalysisResult, Filters, Region } from '@/types';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [showBanner, setShowBanner] = useState(false);
  const [focusRegion, setFocusRegion] = useState<Region | null>(null);
  const [filters, setFilters] = useState<Filters>({
    socialClasses: [],
    commercialTypes: [],
    neighborhoods: [],
  });

  const resultsRef = useRef<HTMLDivElement>(null);

  // Filtrar regiões baseado nos filtros
  const filteredRegions = result?.regions.filter((region) => {
    const matchClass =
      filters.socialClasses.length === 0 ||
      filters.socialClasses.includes(region.socialClass);
    const matchType =
      filters.commercialTypes.length === 0 ||
      filters.commercialTypes.includes(region.commercialType);
    const matchNeighborhood =
      filters.neighborhoods.length === 0 ||
      filters.neighborhoods.some((n) => region.name.includes(n));

    return matchClass && matchType && matchNeighborhood;
  });

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setShowBanner(false);
    setFocusRegion(null);

    // Simular tempo de análise (3 segundos)
    await new Promise((resolve) => setTimeout(resolve, 3000));

    const analysisResult = generateMockAnalysis(query);
    setResult(analysisResult);
    setIsLoading(false);
    setShowBanner(true);
  };

  // Scroll para resultados quando análise terminar
  useEffect(() => {
    if (result && !isLoading && resultsRef.current) {
      setTimeout(() => {
        resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 300);
    }
  }, [result, isLoading]);

  const handleFocusRegion = (region: Region) => {
    setFocusRegion(region);
    // Scroll para o mapa
    const mapElement = document.getElementById('map-section');
    if (mapElement) {
      mapElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <AppHeader />

      <div className="flex">
        {/* Sidebar - Desktop */}
        {result && (
          <FilterSidebar
            filters={filters}
            onFiltersChange={setFilters}
            className="hidden lg:flex sticky top-[60px] h-[calc(100vh-60px)]"
          />
        )}

        {/* Main Content */}
        <main className="flex-1 px-4 py-6 md:px-6 lg:px-8">
          <div className="mx-auto max-w-5xl space-y-6">
            {/* Search Section */}
            <section className="py-8">
              <div className="text-center mb-8">
                <h1 className="text-2xl md:text-3xl font-bold mb-2">
                  Encontre o <span className="text-primary">local ideal</span> para seu negócio
                </h1>
                <p className="text-muted-foreground">
                  Análise geoespacial e de mercado com inteligência artificial
                </p>
              </div>
              <SearchBar onSearch={handleSearch} isLoading={isLoading} />
            </section>

            {/* Results Section */}
            <AnimatePresence>
              {result && !isLoading && (
                <motion.div
                  ref={resultsRef}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                  className="space-y-6"
                >
                  {/* Success Banner */}
                  <SuccessBanner
                    totalRegions={filteredRegions?.length || result.totalRegions}
                    product={result.product}
                    niche={result.niche}
                    show={showBanner}
                  />

                  {/* Metrics */}
                  <MetricsCards
                    totalRegions={filteredRegions?.length || result.totalRegions}
                    avgScore={result.avgScore}
                    topNeighborhood={result.topNeighborhood}
                    topCommercialType={result.topCommercialType}
                  />

                  {/* Analysis Details */}
                  <AnalysisDetails
                    product={result.product}
                    niche={result.niche}
                    regions={filteredRegions || result.regions}
                    avgScore={result.avgScore}
                  />

                  {/* Map */}
                  <section id="map-section">
                    <MapView
                      regions={filteredRegions || result.regions}
                      focusRegion={focusRegion}
                      onRegionClick={setFocusRegion}
                    />
                  </section>

                  {/* Strategy Tabs */}
                  <StrategyTabs
                    regions={filteredRegions || result.regions}
                    strategy={result.strategy}
                    demographics={result.demographics}
                    onFocusRegion={handleFocusRegion}
                  />

                  {/* Bottom Section: Insights + Action Plan */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <MarketInsights insights={result.insights} />
                    <ActionPlan
                      actions={result.actionPlan}
                      storageKey={`smart-sale-${result.product}`}
                    />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>
      </div>

      {/* Mobile Filter Button */}
      {result && (
        <FilterSidebar
          filters={filters}
          onFiltersChange={setFilters}
          className="lg:hidden"
        />
      )}
    </div>
  );
}

export default App;
