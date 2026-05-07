import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, GitCompare, Loader2, AlertCircle } from 'lucide-react';
import { analyzeByContext } from '@/lib/api';
import { AnalysisResult } from '@/types';

interface Props {
  original: AnalysisResult;
  onClose: () => void;
}

const SCORE_COLOR = (s: number) =>
  s >= 75 ? 'text-emerald-600' : s >= 55 ? 'text-amber-500' : 'text-rose-500';

function Row({ label, a, b }: { label: string; a: React.ReactNode; b: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[1fr_1fr_1fr] text-xs border-b last:border-0 py-2">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-center font-medium">{a}</span>
      <span className="text-center font-medium">{b}</span>
    </div>
  );
}

export function CompareModal({ original, onClose }: Props) {
  const [desc, setDesc] = useState('');
  const [loading, setLoading] = useState(false);
  const [compared, setCompared] = useState<AnalysisResult | null>(null);
  const [err, setErr] = useState(false);

  const run = async () => {
    if (desc.trim().length < 5) return;
    setLoading(true);
    setErr(false);
    try {
      const result = await analyzeByContext(
        { descricao: desc, objetivo: 'testar', investimento: original.investimento as any || 'medio' },
        { usarApi: false },
      );
      setCompared(result);
    } catch {
      setErr(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
        onClick={e => { if (e.target === e.currentTarget) onClose(); }}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="bg-card rounded-xl shadow-2xl border w-full max-w-md max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <div className="flex items-center gap-2">
              <GitCompare className="h-4 w-4 text-primary" />
              <h2 className="text-sm font-semibold">Comparativo "E se?"</h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full p-1 hover:bg-muted transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Input */}
          <div className="p-4 space-y-2">
            <p className="text-xs text-muted-foreground">
              Descreva um segundo negócio/produto para comparar com <strong>{original.product}</strong>:
            </p>
            <textarea
              value={desc}
              onChange={e => setDesc(e.target.value)}
              rows={3}
              placeholder="ex: loja de roupas infantis no Mucuripe..."
              className="w-full rounded-lg border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <button
              type="button"
              onClick={run}
              disabled={loading || desc.trim().length < 5}
              className="w-full rounded-lg bg-primary text-primary-foreground text-xs font-medium py-2 disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              {loading && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              {loading ? 'Analisando…' : 'Comparar'}
            </button>
            {err && (
              <p className="flex items-center gap-1 text-xs text-rose-500">
                <AlertCircle className="h-3.5 w-3.5" /> Falha na análise. Tente novamente.
              </p>
            )}
          </div>

          {/* Comparison table */}
          {compared && (
            <div className="px-4 pb-4">
              <div className="rounded-lg border overflow-hidden">
                {/* Column headers */}
                <div className="grid grid-cols-[1fr_1fr_1fr] bg-muted px-3 py-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">
                  <span>Métrica</span>
                  <span className="text-center truncate">{original.product}</span>
                  <span className="text-center truncate">{compared.product}</span>
                </div>
                <div className="px-3">
                  <Row
                    label="Nicho"
                    a={original.niche}
                    b={compared.niche}
                  />
                  <Row
                    label="Score médio"
                    a={<span className={SCORE_COLOR(original.avgScore)}>{original.avgScore.toFixed(1)}</span>}
                    b={<span className={SCORE_COLOR(compared.avgScore)}>{compared.avgScore.toFixed(1)}</span>}
                  />
                  <Row
                    label="Regiões"
                    a={original.totalRegions}
                    b={compared.totalRegions}
                  />
                  <Row
                    label="Bairro top"
                    a={<span className="truncate block text-center">{original.topNeighborhood}</span>}
                    b={<span className="truncate block text-center">{compared.topNeighborhood}</span>}
                  />
                  <Row
                    label="Tipo comercial"
                    a={<span className="truncate block text-center">{original.topCommercialType}</span>}
                    b={<span className="truncate block text-center">{compared.topCommercialType}</span>}
                  />
                  {/* Winner */}
                  {original.avgScore !== compared.avgScore && (
                    <div className="py-2 text-center text-xs font-semibold text-emerald-600">
                      ✓ Melhor potencial: {original.avgScore > compared.avgScore ? original.product : compared.product}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
