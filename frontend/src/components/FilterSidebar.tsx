import { useState } from 'react';
import { Filter, X, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { neighborhoodsList } from '@/lib/mock-data';
import { Filters } from '@/types';
import { cn } from '@/lib/utils';

const socialClassesList = ['A', 'B', 'C', 'D', 'E'];
const commercialTypesList = ['Varejo', 'Serviços', 'Alimentação', 'Saúde', 'Educação', 'Tecnologia'];

interface FilterSidebarProps {
  filters: Filters;
  onFiltersChange: (filters: Filters) => void;
  className?: string;
}

function FilterContent({ filters, onFiltersChange }: Omit<FilterSidebarProps, 'className'>) {
  const [localFilters, setLocalFilters] = useState<Filters>(filters);

  const activeFiltersCount = 
    localFilters.socialClasses.length + 
    localFilters.commercialTypes.length + 
    localFilters.neighborhoods.length;

  const toggleFilter = (category: keyof Filters, value: string) => {
    setLocalFilters((prev) => {
      const current = prev[category];
      const updated = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value];
      return { ...prev, [category]: updated };
    });
  };

  const applyFilters = () => {
    onFiltersChange(localFilters);
  };

  const clearFilters = () => {
    const empty: Filters = { socialClasses: [], commercialTypes: [], neighborhoods: [] };
    setLocalFilters(empty);
    onFiltersChange(empty);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-2">
          <Filter className="h-5 w-5 text-primary" />
          <h2 className="font-semibold">Filtros</h2>
        </div>
        {activeFiltersCount > 0 && (
          <Badge variant="default">{activeFiltersCount} ativos</Badge>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <Accordion type="multiple" defaultValue={['classes', 'types']} className="space-y-2">
          {/* Classes Sociais */}
          <AccordionItem value="classes" className="border rounded-lg px-3">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              Classes Sociais
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3 pt-2">
                {socialClassesList.map((cls) => (
                  <label
                    key={cls}
                    className="flex cursor-pointer items-center gap-3 rounded-md p-2 hover:bg-accent transition-colors"
                  >
                    <Checkbox
                      checked={localFilters.socialClasses.includes(cls)}
                      onCheckedChange={() => toggleFilter('socialClasses', cls)}
                    />
                    <span className="text-sm">Classe {cls}</span>
                  </label>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Tipos Comerciais */}
          <AccordionItem value="types" className="border rounded-lg px-3">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              Tipos Comerciais
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-3 pt-2">
                {commercialTypesList.map((type) => (
                  <label
                    key={type}
                    className="flex cursor-pointer items-center gap-3 rounded-md p-2 hover:bg-accent transition-colors"
                  >
                    <Checkbox
                      checked={localFilters.commercialTypes.includes(type)}
                      onCheckedChange={() => toggleFilter('commercialTypes', type)}
                    />
                    <span className="text-sm">{type}</span>
                  </label>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>

          {/* Bairros */}
          <AccordionItem value="neighborhoods" className="border rounded-lg px-3">
            <AccordionTrigger className="text-sm font-medium hover:no-underline">
              Bairros
            </AccordionTrigger>
            <AccordionContent>
              <div className="max-h-64 space-y-3 overflow-y-auto pt-2">
                {neighborhoodsList.map((neighborhood) => (
                  <label
                    key={neighborhood}
                    className="flex cursor-pointer items-center gap-3 rounded-md p-2 hover:bg-accent transition-colors"
                  >
                    <Checkbox
                      checked={localFilters.neighborhoods.includes(neighborhood)}
                      onCheckedChange={() => toggleFilter('neighborhoods', neighborhood)}
                    />
                    <span className="text-sm">{neighborhood}</span>
                  </label>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>

      <div className="border-t p-4 space-y-3">
        <Button onClick={applyFilters} className="w-full">
          Aplicar Filtros
        </Button>
        {activeFiltersCount > 0 && (
          <button
            onClick={clearFilters}
            className="w-full text-center text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            Limpar filtros
          </button>
        )}
      </div>
    </div>
  );
}

export function FilterSidebar({ filters, onFiltersChange, className }: FilterSidebarProps) {
  const [isOpen, setIsOpen] = useState(false);

  const activeFiltersCount = 
    filters.socialClasses.length + 
    filters.commercialTypes.length + 
    filters.neighborhoods.length;

  return (
    <>
      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden lg:flex w-[280px] flex-col border-r bg-card",
          className
        )}
      >
        <FilterContent filters={filters} onFiltersChange={onFiltersChange} />
      </aside>

      {/* Mobile Trigger Button */}
      <div className="lg:hidden fixed bottom-4 right-4 z-40">
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button size="lg" className="h-14 w-14 rounded-full shadow-lg">
              <Filter className="h-6 w-6" />
              {activeFiltersCount > 0 && (
                <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs font-bold">
                  {activeFiltersCount}
                </span>
              )}
            </Button>
          </DialogTrigger>
          <DialogContent className="h-[85vh] max-w-md p-0">
            <FilterContent
              filters={filters}
              onFiltersChange={(newFilters) => {
                onFiltersChange(newFilters);
                setIsOpen(false);
              }}
            />
          </DialogContent>
        </Dialog>
      </div>
    </>
  );
}
