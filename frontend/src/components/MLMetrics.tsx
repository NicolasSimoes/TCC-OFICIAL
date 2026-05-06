/**
 * MLMetrics — métricas de clustering retornadas pelo backend.
 */
import { ClusteringMetrics } from '@/types';

interface Props {
  metrics: ClusteringMetrics;
  nlpConfianca?: number;
  nlpMetodo?: string;
}

function Score({ value, inverse = false }: { value?: number; inverse?: boolean }) {
  if (value === undefined || value === null)
    return <span className="text-muted-foreground text-xs">—</span>;
  const q = inverse ? 1 - Math.min(value, 2) / 2 : value;
  const cls = q > 0.65 ? 'text-emerald-600' : q > 0.4 ? 'text-amber-500' : 'text-red-500';
  return <span className={`font-mono text-sm font-semibold ${cls}`}>{value.toFixed(3)}</span>;
}

export function MLMetrics({ metrics, nlpConfianca, nlpMetodo }: Props) {
  return (
    <div className="rounded-lg border bg-white p-4 space-y-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Métricas do Pipeline ML</p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
        {/* NLP */}
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Classificador NLP</p>
          <p className="font-medium text-foreground leading-tight">{nlpMetodo?.replace(' (fallback)', '') || 'keywords'}</p>
          {nlpConfianca !== undefined && (
            <p className="text-xs text-muted-foreground">Confiança: <Score value={nlpConfianca} /></p>
          )}
        </div>

        {/* Algoritmo */}
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Algoritmo</p>
          <p className="font-medium text-foreground">{metrics.algoritmo || '—'}</p>
          <p className="text-xs text-muted-foreground">Clusters: {metrics.n_clusters ?? '—'}</p>
        </div>

        {/* Silhouette */}
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Silhouette Score</p>
          <Score value={metrics.silhouette} />
          <p className="text-xs text-muted-foreground leading-tight">KMeans: <Score value={metrics.kmeans_silhouette} /></p>
        </div>

        {/* Davies-Bouldin */}
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Davies-Bouldin</p>
          <Score value={metrics.davies_bouldin} inverse />
          <p className="text-xs text-muted-foreground leading-tight">DBSCAN: <Score value={metrics.dbscan_silhouette} /></p>
        </div>
      </div>

      {/* Elbow */}
      {metrics.elbow && Object.keys(metrics.elbow).length > 0 && (
        <div>
          <p className="text-xs text-muted-foreground mb-2">Elbow Method — Inércia por k</p>
          <div className="flex gap-4">
            {Object.entries(metrics.elbow).map(([k, v]) => (
              <div key={k} className="text-center">
                <p className="text-xs text-muted-foreground">k={k}</p>
                <p className="font-mono text-xs font-semibold">{v.toFixed(0)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {metrics.justificativa && (
        <p className="text-xs text-muted-foreground border-t pt-3 leading-relaxed">{metrics.justificativa}</p>
      )}
    </div>
  );
}
