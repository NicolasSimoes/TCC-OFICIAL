import { useState, useRef, useEffect } from 'react';
import { Search, Loader2, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { searchSuggestions } from '@/lib/mock-data';
import { motion, AnimatePresence } from 'framer-motion';

interface SearchBarProps {
  onSearch: (query: string, usarApi: boolean) => void;
  isLoading: boolean;
}

export function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
  const [usarApi, setUsarApi] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Filtrar sugestões baseado no que o usuário digita
  useEffect(() => {
    if (query.length > 0) {
      const filtered = searchSuggestions.filter((s) =>
        s.toLowerCase().includes(query.toLowerCase())
      );
      setFilteredSuggestions(filtered);
    } else {
      setFilteredSuggestions(searchSuggestions.slice(0, 6));
    }
  }, [query]);

  // Progress bar durante loading
  useEffect(() => {
    if (isLoading) {
      setProgress(0);
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 95) return prev;
          return prev + Math.random() * 10;
        });
      }, 200);
      return () => clearInterval(interval);
    } else {
      setProgress(100);
      setTimeout(() => setProgress(0), 500);
    }
  }, [isLoading]);

  // Fechar sugestões ao clicar fora
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim(), usarApi);
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Ex: whey protein, fralda, notebook..."
            className="h-11 pl-9 pr-4 text-sm bg-white border-border shadow-sm"
            disabled={isLoading}
            aria-label="Buscar produto"
          />
        </div>
        <Button
          type="submit"
          className="h-11 px-5 text-sm"
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Analisando</>
          ) : (
            'Analisar'
          )}
        </Button>
      </form>

      {/* Toggle Google Places API */}
      <div className="mt-2 flex items-center gap-2">
        <button
          type="button"
          onClick={() => setUsarApi(v => !v)}
          className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus:outline-none ${usarApi ? 'bg-primary' : 'bg-muted-foreground/30'}`}
          aria-pressed={usarApi}
        >
          <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${usarApi ? 'translate-x-4' : 'translate-x-0'}`} />
        </button>
        <label className="flex items-center gap-1 text-xs text-muted-foreground cursor-pointer select-none" onClick={() => setUsarApi(v => !v)}>
          <MapPin className="h-3 w-3" />
          Enriquecer com Google Places API
          {usarApi && <span className="ml-1 text-amber-500 font-medium">(+15–30s)</span>}
        </label>
      </div>

      {/* Sugestões */}
      <AnimatePresence>
        {showSuggestions && filteredSuggestions.length > 0 && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.1 }}
            className="absolute top-full left-0 z-50 mt-1 w-full rounded-lg border bg-white shadow-md"
          >
            <ul className="py-1">
              {filteredSuggestions.map((suggestion) => (
                <li key={suggestion}>
                  <button
                    type="button"
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-muted transition-colors"
                  >
                    <Search className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    <span>{suggestion}</span>
                  </button>
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Progress */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="mt-3"
          >
            <Progress value={progress} className="h-1" />
            <p className="mt-2 text-center text-xs text-muted-foreground">Processando pipeline ML…</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
