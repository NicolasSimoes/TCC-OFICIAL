import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Calculator, TrendingUp, AlertCircle } from 'lucide-react';
import { estimateROI } from '@/lib/api';
import { ROIEstimate } from '@/types';

interface Props {
  niche: string;
  avgScore: number;
  investimento?: string; // herdado do contexto guiado
}

const fmt = (n: number) =>
  n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 });

const INV_OPTIONS = [
  { key: 'baixo', label: 'Baixo (até R$30k)' },
  { key: 'medio', label: 'Médio (R$30k–R$150k)' },
  { key: 'alto',  label: 'Alto (>R$150k)' },
];

export function ROISimulator({ niche, avgScore, investimento: initInv }: Props) {
  const [inv, setInv] = useState(initInv || 'medio');
  const [roi, setRoi] = useState<ROIEstimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErr(false);
    estimateROI(niche, inv, avgScore)
      .then(data => { if (!cancelled) setRoi(data); })
      .catch(() => { if (!cancelled) setErr(true); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [niche, inv, avgScore]);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <Calculator className="h-4 w-4 text-primary" />
          Simulador de ROI — {niche}
        </CardTitle>
        <div className="flex gap-1 mt-1">
          {INV_OPTIONS.map(o => (
            <button
              key={o.key}
              type="button"
              onClick={() => setInv(o.key)}
              className={`rounded-full px-2.5 py-0.5 text-[10px] font-medium border transition-all ${
                inv === o.key
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'text-muted-foreground border-border hover:border-primary/50'
              }`}
            >
              {o.label}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="space-y-2 animate-pulse">
            {[...Array(4)].map((_, i) => <div key={i} className="h-8 rounded bg-muted" />)}
          </div>
        )}
        {err && (
          <p className="flex items-center gap-1.5 text-xs text-amber-500">
            <AlertCircle className="h-3.5 w-3.5" />
            Backend offline — ROI não disponível sem API.
          </p>
        )}
        {roi && !loading && (
          <>
            {/* Setup cost */}
            <div className="mb-3 p-3 rounded-lg bg-muted/50 text-xs space-y-0.5">
              <p className="font-medium text-foreground">Custo de setup estimado</p>
              <p className="text-muted-foreground">
                {fmt(roi.custoSetupMin)} – {fmt(roi.custoSetupMax)}
              </p>
            </div>

            {/* Faturamento projetado */}
            <div className="grid grid-cols-3 gap-2 mb-3">
              {[
                { label: 'Mês 1', value: roi.faturamentoM1 },
                { label: '6 meses', value: roi.faturamentoM6 },
                { label: '12 meses', value: roi.faturamentoM12 },
              ].map(({ label, value }) => (
                <div key={label} className="p-2 rounded-lg border text-center">
                  <p className="text-[10px] text-muted-foreground">{label}</p>
                  <p className="text-sm font-semibold text-foreground">{fmt(value)}</p>
                </div>
              ))}
            </div>

            {/* Lucro + payback */}
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="p-2 rounded-lg border text-center">
                <p className="text-[10px] text-muted-foreground">Lucro líq. 12 meses</p>
                <p className={`text-sm font-bold ${roi.lucroLiquidoM12 > 0 ? 'text-emerald-600' : 'text-rose-500'}`}>
                  {fmt(roi.lucroLiquidoM12)}
                </p>
              </div>
              <div className="p-2 rounded-lg border text-center">
                <p className="text-[10px] text-muted-foreground">Payback estimado</p>
                <p className="text-sm font-bold text-foreground flex items-center justify-center gap-1">
                  <TrendingUp className="h-3 w-3 text-primary" />
                  {roi.paybackMeses} meses
                </p>
              </div>
            </div>

            {/* Premissas */}
            <details className="text-[10px] text-muted-foreground cursor-pointer">
              <summary className="font-medium cursor-pointer hover:text-foreground">Premissas</summary>
              <ul className="mt-1 space-y-0.5 pl-3 list-disc">
                {roi.premissas.map((p, i) => <li key={i}>{p}</li>)}
              </ul>
            </details>
          </>
        )}
      </CardContent>
    </Card>
  );
}
