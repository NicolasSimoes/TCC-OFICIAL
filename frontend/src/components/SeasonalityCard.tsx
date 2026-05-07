import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp } from 'lucide-react';

const MONTHS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'];
const NOW_MONTH = new Date().getMonth(); // 0-based

interface Props {
  sazonalidade: number[];
  niche: string;
}

export function SeasonalityCard({ sazonalidade, niche }: Props) {
  if (!sazonalidade || sazonalidade.length !== 12) return null;

  const max = Math.max(...sazonalidade);
  const min = Math.min(...sazonalidade);
  const picoIdx = sazonalidade.indexOf(max);
  const baixaIdx = sazonalidade.indexOf(min);
  const currentScore = sazonalidade[NOW_MONTH];

  const momentoLabel =
    currentScore >= 80 ? 'ótimo momento' : currentScore >= 65 ? 'momento razoável' : 'momento de baixa';
  const momentoColor =
    currentScore >= 80 ? 'text-emerald-600' : currentScore >= 65 ? 'text-amber-500' : 'text-rose-500';

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-primary" />
          Sazonalidade — {niche}
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Agora ({MONTHS[NOW_MONTH]}): <span className={`font-medium ${momentoColor}`}>{momentoLabel}</span>
          {' '}· Pico: <strong>{MONTHS[picoIdx]}</strong> · Baixa: <strong>{MONTHS[baixaIdx]}</strong>
        </p>
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-[3px] h-16">
          {sazonalidade.map((val, i) => {
            const heightPct = ((val - min) / (max - min + 1)) * 80 + 20;
            const isCurrent = i === NOW_MONTH;
            const isPeak = i === picoIdx;
            const barColor = isCurrent
              ? 'bg-primary'
              : isPeak
              ? 'bg-emerald-400'
              : val < 65
              ? 'bg-rose-300'
              : 'bg-muted-foreground/30';
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-[2px]">
                <div
                  className={`w-full rounded-t-sm transition-all ${barColor}`}
                  style={{ height: `${heightPct}%` }}
                  title={`${MONTHS[i]}: ${val}`}
                />
                <span className={`text-[9px] leading-none ${isCurrent ? 'text-primary font-bold' : 'text-muted-foreground'}`}>
                  {MONTHS[i]}
                </span>
              </div>
            );
          })}
        </div>
        <div className="mt-2 flex gap-3 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-primary inline-block" /> mês atual</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-emerald-400 inline-block" /> pico do ano</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-rose-300 inline-block" /> baixa temporada</span>
        </div>
      </CardContent>
    </Card>
  );
}
