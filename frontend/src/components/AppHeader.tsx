import { MapPin } from 'lucide-react';

interface AppHeaderProps {
  apiOnline?: boolean | null;
}

export function AppHeader({ apiOnline }: AppHeaderProps) {
  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-border">
      <div className="mx-auto max-w-3xl px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MapPin className="h-5 w-5 text-primary" />
          <span className="font-semibold text-foreground tracking-tight">Smart Sale</span>
          <span className="text-xs font-medium text-muted-foreground">Fortaleza</span>
        </div>

        {apiOnline !== null && apiOnline !== undefined && (
          <span className={`flex items-center gap-1.5 text-xs ${apiOnline ? 'text-emerald-600' : 'text-amber-500'}`}>
            <span className={`inline-block h-1.5 w-1.5 rounded-full ${apiOnline ? 'bg-emerald-500' : 'bg-amber-400'}`} />
            {apiOnline ? 'API online' : 'Demo mode'}
          </span>
        )}
      </div>
    </header>
  );
}
