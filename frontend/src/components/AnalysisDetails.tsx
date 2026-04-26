import { useState, useEffect } from 'react';
import { ChevronDown, Package, Tag, MapPin, TrendingUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Region } from '@/types';
import { cn } from '@/lib/utils';

interface AnalysisDetailsProps {
  product: string;
  niche: string;
  regions: Region[];
  avgScore: number;
}

export function AnalysisDetails({ product, niche, regions, avgScore }: AnalysisDetailsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Expandido por default em desktop
  useEffect(() => {
    const handleResize = () => {
      setIsExpanded(window.innerWidth >= 1024);
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Top 5 bairros únicos
  const topNeighborhoods = Array.from(
    new Map(
      regions.slice(0, 10).map((r) => [r.name.split(' - ')[0], r])
    ).values()
  ).slice(0, 5);

  const getScoreColor = (score: number) => {
    if (score >= 85) return 'bg-green-500';
    if (score >= 70) return 'bg-blue-500';
    if (score >= 55) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="rounded-lg border bg-card">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between p-4 text-left hover:bg-accent/50 transition-colors"
        aria-expanded={isExpanded}
      >
        <span className="font-semibold">Detalhes da Análise</span>
        <ChevronDown
          className={cn(
            "h-5 w-5 text-muted-foreground transition-transform duration-200",
            isExpanded && "rotate-180"
          )}
        />
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="border-t p-4 space-y-4">
              {/* Info básica */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary/10 p-2">
                    <Package className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Produto</p>
                    <p className="font-medium">{product}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary/10 p-2">
                    <Tag className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Nicho</p>
                    <p className="font-medium">{niche}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-primary/10 p-2">
                    <TrendingUp className="h-4 w-4 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Score Médio</p>
                    <p className="font-medium text-primary">{avgScore.toFixed(1)}</p>
                  </div>
                </div>
              </div>

              {/* Top 5 Bairros */}
              <div>
                <h4 className="mb-3 text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  Top 5 Bairros com Maior Potencial
                </h4>
                <div className="space-y-2">
                  {topNeighborhoods.map((region, index) => (
                    <div key={region.id} className="flex items-center gap-3">
                      <span className="w-6 text-center text-sm font-bold text-muted-foreground">
                        {index + 1}
                      </span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">
                            {region.name.split(' - ')[0]}
                          </span>
                          <span className="text-sm font-bold text-primary">
                            {region.score.toFixed(1)}
                          </span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-secondary overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${region.score}%` }}
                            transition={{ duration: 0.8, delay: index * 0.1 }}
                            className={cn("h-full rounded-full", getScoreColor(region.score))}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
