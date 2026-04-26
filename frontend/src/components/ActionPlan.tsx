import { useEffect, useState } from 'react';
import { CheckSquare } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { ActionItem } from '@/types';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface ActionPlanProps {
  actions: ActionItem[];
  storageKey?: string;
}

export function ActionPlan({ actions, storageKey = 'smart-sale-actions' }: ActionPlanProps) {
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  // Carregar do localStorage
  useEffect(() => {
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      try {
        setCheckedItems(JSON.parse(saved));
      } catch {
        // Ignore parse errors
      }
    }
  }, [storageKey]);

  // Salvar no localStorage
  const toggleItem = (id: string) => {
    setCheckedItems((prev) => {
      const updated = { ...prev, [id]: !prev[id] };
      localStorage.setItem(storageKey, JSON.stringify(updated));
      return updated;
    });
  };

  const completedCount = Object.values(checkedItems).filter(Boolean).length;

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold flex items-center gap-2">
          <CheckSquare className="h-5 w-5 text-primary" />
          Plano de Ação
        </h3>
        <span className="text-xs text-muted-foreground">
          {completedCount}/{actions.length} concluídos
        </span>
      </div>

      {/* Progress bar */}
      <div className="mb-4 h-2 rounded-full bg-muted overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${(completedCount / actions.length) * 100}%` }}
          transition={{ duration: 0.5 }}
          className="h-full bg-primary"
        />
      </div>

      <div className="space-y-2">
        {actions.map((action, index) => {
          const isChecked = checkedItems[action.id] || false;

          return (
            <motion.label
              key={action.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className={cn(
                "flex cursor-pointer items-center gap-3 rounded-lg p-3 transition-all",
                isChecked
                  ? "bg-primary/10 border border-primary/30"
                  : "bg-muted/30 hover:bg-muted/50"
              )}
            >
              <Checkbox
                checked={isChecked}
                onCheckedChange={() => toggleItem(action.id)}
                className={cn(isChecked && "border-primary")}
              />
              <span
                className={cn(
                  "text-sm flex-1 transition-all",
                  isChecked && "text-muted-foreground line-through"
                )}
              >
                {action.text}
              </span>
            </motion.label>
          );
        })}
      </div>
    </Card>
  );
}
