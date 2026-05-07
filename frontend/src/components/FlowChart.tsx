import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users } from 'lucide-react';

// Índice de fluxo 0-100 por período: manhã (6-12), tarde (12-18), noite (18-23), fim de semana
const FLOW_BY_NICHE: Record<string, { manha: number; tarde: number; noite: number; fds: number }> = {
  Fitness:      { manha: 90, tarde: 50, noite: 85, fds: 80 },
  Infantil:     { manha: 70, tarde: 85, noite: 40, fds: 90 },
  Escolar:      { manha: 90, tarde: 80, noite: 20, fds: 30 },
  'Alimentação':{ manha: 55, tarde: 90, noite: 80, fds: 85 },
  'Farmácia':   { manha: 80, tarde: 85, noite: 55, fds: 70 },
  Beleza:       { manha: 50, tarde: 90, noite: 60, fds: 95 },
  Pet:          { manha: 60, tarde: 80, noite: 50, fds: 90 },
  'Eletrônicos':{ manha: 40, tarde: 85, noite: 70, fds: 95 },
  'Saúde':      { manha: 80, tarde: 80, noite: 40, fds: 50 },
  Outro:        { manha: 60, tarde: 75, noite: 55, fds: 70 },
};

const PERIODS = [
  { key: 'manha' as const,  label: 'Manhã',       sub: '6h – 12h',  color: '#f59e0b' },
  { key: 'tarde' as const,  label: 'Tarde',       sub: '12h – 18h', color: '#3b82f6' },
  { key: 'noite' as const,  label: 'Noite',       sub: '18h – 23h', color: '#6366f1' },
  { key: 'fds'   as const,  label: 'Fim de sem.', sub: 'sáb + dom', color: '#10b981' },
];

interface Props {
  niche: string;
}

export function FlowChart({ niche }: Props) {
  const flow = FLOW_BY_NICHE[niche] ?? FLOW_BY_NICHE['Outro'];
  const peakKey = PERIODS.reduce((best, p) => (flow[p.key] > flow[best.key] ? p : best), PERIODS[0]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <Users className="h-4 w-4 text-primary" />
          Fluxo de Pessoas — {niche}
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Melhor período: <strong>{peakKey.label}</strong> ({peakKey.sub})
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {PERIODS.map(p => {
            const val = flow[p.key];
            return (
              <div key={p.key} className="flex items-center gap-3">
                <div className="w-28 flex-shrink-0">
                  <p className="text-xs font-medium leading-none">{p.label}</p>
                  <p className="text-[10px] text-muted-foreground">{p.sub}</p>
                </div>
                <div className="flex-1 h-4 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${val}%`, backgroundColor: p.color }}
                  />
                </div>
                <span className="text-xs font-medium w-8 text-right">{val}</span>
              </div>
            );
          })}
        </div>
        <p className="mt-3 text-[10px] text-muted-foreground">
          Índice estimado com base no comportamento típico do nicho. Valide com pesquisa de campo.
        </p>
      </CardContent>
    </Card>
  );
}
