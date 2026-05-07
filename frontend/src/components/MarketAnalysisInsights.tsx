import { Region } from '@/types';
import { Building2, Users, Anchor, Activity, Target } from 'lucide-react';
import { motion } from 'framer-motion';

interface MarketAnalysisInsightsProps {
  regions: Region[];
}

const SATURACAO_LABEL: Record<string, { label: string; color: string }> = {
  vazio: { label: 'Mercado vazio', color: 'bg-emerald-500' },
  baixa: { label: 'Saturação baixa', color: 'bg-green-500' },
  media: { label: 'Saturação média', color: 'bg-yellow-500' },
  alta: { label: 'Saturação alta', color: 'bg-red-500' },
};

export function MarketAnalysisInsights({ regions }: MarketAnalysisInsightsProps) {
  const analysed = regions.filter((r) => r.marketAnalysis).slice(0, 5);

  if (analysed.length === 0) {
    return null;
  }

  return (
    <div className="rounded-lg border bg-card p-5">
      <div className="mb-4 flex items-center gap-2">
        <Target className="h-5 w-5 text-primary" />
        <h3 className="font-semibold">Análise de Mercado por Região</h3>
        <span className="ml-auto text-xs text-muted-foreground">
          via Google Places · raio {analysed[0].marketAnalysis?.raio_m}m
        </span>
      </div>

      <p className="mb-4 text-xs text-muted-foreground">
        Concorrentes diretos, negócios sinérgicos e âncoras de tráfego nas top {analysed.length} regiões.
      </p>

      <div className="space-y-3">
        {analysed.map((region, idx) => {
          const m = region.marketAnalysis!;
          const sat = SATURACAO_LABEL[m.saturacao];
          return (
            <motion.div
              key={region.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.06 }}
              className="rounded-lg border bg-background p-3"
            >
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-xs font-bold text-muted-foreground w-5 shrink-0">
                    #{idx + 1}
                  </span>
                  <span className="text-sm font-medium truncate">
                    {region.name.split(' - ')[0]}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <span className={`h-2 w-2 rounded-full ${sat.color}`} />
                  <span className="text-xs text-muted-foreground">{sat.label}</span>
                </div>
              </div>

              <div className="mb-2 grid grid-cols-3 gap-2">
                <Metric
                  icon={<Building2 className="h-3.5 w-3.5" />}
                  label="Concorrentes"
                  value={m.competitors}
                  tone={m.competitors > 5 ? 'danger' : m.competitors > 2 ? 'warn' : 'ok'}
                />
                <Metric
                  icon={<Users className="h-3.5 w-3.5" />}
                  label="Sinergias"
                  value={m.synergies}
                  tone={m.synergies >= 3 ? 'ok' : 'neutral'}
                />
                <Metric
                  icon={<Anchor className="h-3.5 w-3.5" />}
                  label="Âncoras"
                  value={m.anchors}
                  tone={m.anchors >= 2 ? 'ok' : 'neutral'}
                />
              </div>

              <div className="flex items-start gap-2 rounded-md bg-muted/40 p-2">
                <Activity className="h-3.5 w-3.5 text-primary mt-0.5 shrink-0" />
                <p className="text-xs text-muted-foreground leading-relaxed">{m.insight}</p>
              </div>

              {/* Nomes dos concorrentes */}
              {m.competitor_names && m.competitor_names.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {m.competitor_names.map((name, i) => (
                    <span
                      key={i}
                      className="text-[10px] rounded-full border bg-background px-2 py-0.5 text-muted-foreground"
                    >
                      {name}
                    </span>
                  ))}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  tone: 'ok' | 'warn' | 'danger' | 'neutral';
}) {
  const toneClass = {
    ok: 'text-emerald-600',
    warn: 'text-amber-600',
    danger: 'text-red-600',
    neutral: 'text-foreground',
  }[tone];

  return (
    <div className="rounded-md border bg-background p-2 text-center">
      <div className={`flex items-center justify-center gap-1 ${toneClass}`}>
        {icon}
        <span className="text-base font-bold tabular-nums">{value}</span>
      </div>
      <p className="text-[10px] uppercase tracking-wide text-muted-foreground mt-0.5">
        {label}
      </p>
    </div>
  );
}
