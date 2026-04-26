import { useState, useRef, useEffect } from 'react';
import { Search, Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import { searchSuggestions } from '@/lib/mock-data';
import { motion, AnimatePresence } from 'framer-motion';

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
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
      onSearch(query.trim());
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  return (
    <div ref={wrapperRef} className="relative w-full max-w-3xl mx-auto">
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
          <Input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Digite o nome do seu produto/serviço e a localidade"
            className="h-12 pl-10 pr-4 text-base"
            disabled={isLoading}
            aria-label="Buscar produto ou serviço"
          />
        </div>
        <Button
          type="submit"
          size="lg"
          className="h-12 px-6 sm:w-auto w-full"
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Analisando...
            </>
          ) : (
            <>
              <Send className="mr-2 h-5 w-5" />
              Enviar
            </>
          )}
        </Button>
      </form>

      {/* Dropdown de sugestões */}
      <AnimatePresence>
        {showSuggestions && filteredSuggestions.length > 0 && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.15 }}
            className="absolute top-full left-0 right-0 z-50 mt-2 rounded-lg border bg-card shadow-lg sm:right-auto sm:w-[calc(100%-100px)]"
          >
            <ul className="py-2">
              {filteredSuggestions.map((suggestion, index) => (
                <li key={suggestion}>
                  <button
                    type="button"
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm hover:bg-accent transition-colors"
                  >
                    <Search className="h-4 w-4 text-muted-foreground" />
                    <span>{suggestion}</span>
                  </button>
                  {index < filteredSuggestions.length - 1 && (
                    <div className="mx-4 border-b border-border/50" />
                  )}
                </li>
              ))}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading state */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-4 space-y-3"
          >
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span>Analisando mercado... ~15 segundos</span>
            </div>
            <Progress value={progress} className="h-2" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
