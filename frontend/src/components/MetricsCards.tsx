import { useEffect, useState } from 'react';
import { MapPin, TrendingUp, Building2, Star } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { motion } from 'framer-motion';

interface MetricsCardsProps {
  totalRegions: number;
  avgScore: number;
  topNeighborhood: string;
  topCommercialType: string;
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  delay: number;
}

function MetricCard({ icon, label, value, delay }: MetricCardProps) {
  const [displayValue, setDisplayValue] = useState<string | number>(typeof value === 'number' ? 0 : value);

  useEffect(() => {
    if (typeof value === 'number') {
      const duration = 1500;
      const steps = 60;
      const increment = value / steps;
      let current = 0;
      
      const timer = setInterval(() => {
        current += increment;
        if (current >= value) {
          setDisplayValue(value);
          clearInterval(timer);
        } else {
          setDisplayValue(Math.round(current * 10) / 10);
        }
      }, duration / steps);

      return () => clearInterval(timer);
    }
  }, [value]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <Card className="group relative overflow-hidden p-4 transition-all hover:border-primary/50 hover:shadow-lg hover:shadow-primary/5">
        <div className="flex items-start gap-4">
          <div className="rounded-lg bg-primary/10 p-3 text-primary group-hover:bg-primary/20 transition-colors">
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="mt-1 text-2xl font-bold text-primary truncate">
              {displayValue}
            </p>
          </div>
        </div>
        <div className="absolute bottom-0 left-0 h-1 w-full bg-gradient-to-r from-primary/0 via-primary/50 to-primary/0 opacity-0 transition-opacity group-hover:opacity-100" />
      </Card>
    </motion.div>
  );
}

export function MetricsCards({ totalRegions, avgScore, topNeighborhood, topCommercialType }: MetricsCardsProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <MetricCard
        icon={<MapPin className="h-5 w-5" />}
        label="Regiões Ideais"
        value={totalRegions}
        delay={0}
      />
      <MetricCard
        icon={<TrendingUp className="h-5 w-5" />}
        label="Score Médio"
        value={avgScore}
        delay={0.1}
      />
      <MetricCard
        icon={<Star className="h-5 w-5" />}
        label="Top Bairro"
        value={topNeighborhood}
        delay={0.2}
      />
      <MetricCard
        icon={<Building2 className="h-5 w-5" />}
        label="Tipo Comercial"
        value={topCommercialType}
        delay={0.3}
      />
    </div>
  );
}
