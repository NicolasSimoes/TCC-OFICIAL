import { MapPin, TrendingUp, Building2 } from 'lucide-react';

interface MetricsCardsProps {
  totalRegions: number;
  avgScore: number;
  topNeighborhood: string;
  topCommercialType: string;
}

interface Metric {
  icon: React.ReactNode;
  label: string;
  value: string | number;
}

function MetricCard({ icon, label, value }: Metric) {
  return (
    <div className="rounded-lg border bg-white p-4">
      <div className="flex items-center gap-2 text-muted-foreground mb-2">
        {icon}
        <span className="text-xs font-medium uppercase tracking-wide">{label}</span>
      </div>
      <p className="text-xl font-bold text-foreground truncate">{value}</p>
    </div>
  );
}

export function MetricsCards({ totalRegions, avgScore, topNeighborhood, topCommercialType }: MetricsCardsProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      <MetricCard icon={<MapPin className="h-3.5 w-3.5" />} label="Regiões" value={totalRegions} />
      <MetricCard icon={<TrendingUp className="h-3.5 w-3.5" />} label="Score Médio" value={avgScore} />
      <MetricCard icon={<MapPin className="h-3.5 w-3.5" />} label="Top Bairro" value={topNeighborhood} />
      <MetricCard icon={<Building2 className="h-3.5 w-3.5" />} label="Tipo" value={topCommercialType} />
    </div>
  );
}
