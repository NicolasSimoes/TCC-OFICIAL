import { Lightbulb } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { motion } from 'framer-motion';

interface MarketInsightsProps {
  insights: string[];
}

export function MarketInsights({ insights }: MarketInsightsProps) {
  return (
    <Card className="p-4">
      <h3 className="font-semibold mb-4 flex items-center gap-2">
        <Lightbulb className="h-5 w-5 text-yellow-400" />
        Análise de Mercado
      </h3>
      <div className="space-y-3">
        {insights.map((insight, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex items-start gap-3 rounded-lg bg-muted/30 p-3"
          >
            <span className="text-lg">💡</span>
            <p className="text-sm text-muted-foreground leading-relaxed">{insight}</p>
          </motion.div>
        ))}
      </div>
    </Card>
  );
}
