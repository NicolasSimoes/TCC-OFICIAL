import { Eye } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Region, Strategy, Demographics } from '@/types';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface StrategyTabsProps {
  regions: Region[];
  strategy: Strategy;
  demographics: Demographics;
  onFocusRegion: (region: Region) => void;
}

/** Converte markdown simples (##, **, *, ---, listas) em HTML legível */
function renderMarkdown(text: string): string {
  return text
    .replace(/---+/g, '<hr class="my-3 border-border" />')
    .replace(/^### (.+)$/gm, '<h4 class="font-semibold text-sm mt-4 mb-1">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="font-semibold text-base mt-4 mb-1">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 class="font-bold text-lg mt-4 mb-1">$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code class="bg-muted px-1 rounded text-xs">$1</code>')
    .replace(/^(\d+)\. (.+)$/gm, '<li class="ml-4 list-decimal">$2</li>')
    .replace(/^[-*] (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
    .replace(/\n{2,}/g, '<br /><br />')
    .replace(/\n/g, '<br />');
}

// Tab: Resumo Executivo
function ExecutiveSummaryTab({ strategy }: { strategy: Strategy }) {
  return (
    <div className="space-y-4">
      <Card className="p-4">
        <h3 className="font-semibold text-primary mb-2">Resumo da Análise</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {strategy.summary}
        </p>
      </Card>
      <Card className="p-4">
        <h3 className="font-semibold mb-2">Visão Executiva</h3>
        <div
          className="text-sm text-muted-foreground leading-relaxed prose-sm"
          dangerouslySetInnerHTML={{ __html: renderMarkdown(strategy.executiveSummary) }}
        />
      </Card>
      <Card className="p-4">
        <h3 className="font-semibold mb-2">Potencial de Mercado</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {strategy.marketPotential}
        </p>
      </Card>
    </div>
  );
}

// Tab: Top 10 Regiões
function Top10Tab({ regions, onFocusRegion }: { regions: Region[]; onFocusRegion: (region: Region) => void }) {
  const top10 = regions.slice(0, 10);

  const getScoreBadgeVariant = (score: number): "success" | "info" | "warning" | "destructive" => {
    if (score >= 85) return 'success';
    if (score >= 70) return 'info';
    if (score >= 55) return 'warning';
    return 'destructive';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="p-3 text-left font-semibold text-primary">#</th>
            <th className="p-3 text-left font-semibold">Região</th>
            <th className="p-3 text-left font-semibold">Score</th>
            <th className="p-3 text-left font-semibold">Potencial</th>
            <th className="p-3 text-left font-semibold">Classe</th>
            <th className="p-3 text-center font-semibold">Ação</th>
          </tr>
        </thead>
        <tbody>
          {top10.map((region, index) => (
            <motion.tr
              key={region.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={cn(
                "border-b transition-colors hover:bg-accent/50",
                index % 2 === 0 ? "bg-card" : "bg-muted/20"
              )}
            >
              <td className="p-3 font-bold text-muted-foreground">{index + 1}</td>
              <td className="p-3 font-medium">{region.name.split(' - ')[0]}</td>
              <td className="p-3">
                <Badge variant={getScoreBadgeVariant(region.score)}>
                  {region.score.toFixed(1)}
                </Badge>
              </td>
              <td className="p-3">
                <span className="text-primary font-medium">{region.potential.toFixed(0)}%</span>
              </td>
              <td className="p-3">{region.socialClass}</td>
              <td className="p-3 text-center">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onFocusRegion(region)}
                  className="text-primary hover:text-primary"
                >
                  <Eye className="h-4 w-4 mr-1" />
                  Ver no mapa
                </Button>
              </td>
            </motion.tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Tab: Estratégia Comercial
function StrategyTab({ strategy }: { strategy: Strategy }) {
  return (
    <Accordion type="multiple" defaultValue={['target', 'recommendations']} className="space-y-2">
      <AccordionItem value="target" className="border rounded-lg px-4">
        <AccordionTrigger className="hover:no-underline">
          <span className="font-semibold">Público-Alvo</span>
        </AccordionTrigger>
        <AccordionContent>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {strategy.targetAudience}
          </p>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="recommendations" className="border rounded-lg px-4">
        <AccordionTrigger className="hover:no-underline">
          <span className="font-semibold">Recomendações</span>
        </AccordionTrigger>
        <AccordionContent>
          <ul className="space-y-2">
            {strategy.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start gap-2 text-sm">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                <span className="text-muted-foreground">{rec}</span>
              </li>
            ))}
          </ul>
        </AccordionContent>
      </AccordionItem>

      <AccordionItem value="nextSteps" className="border rounded-lg px-4">
        <AccordionTrigger className="hover:no-underline">
          <span className="font-semibold">Próximos Passos</span>
        </AccordionTrigger>
        <AccordionContent>
          <ol className="space-y-2">
            {strategy.nextSteps.map((step, index) => (
              <li key={index} className="flex items-start gap-3 text-sm">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                  {index + 1}
                </span>
                <span className="text-muted-foreground mt-0.5">{step}</span>
              </li>
            ))}
          </ol>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}

// Tab: Análise Demográfica
function DemographicsTab({ demographics }: { demographics: Demographics }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Pie Chart - Classes Sociais */}
      <Card className="p-4">
        <h3 className="font-semibold mb-4">Distribuição por Classe Social</h3>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={demographics.socialClasses}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={2}
                dataKey="value"
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                labelLine={false}
              >
                {demographics.socialClasses.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(217 33% 17%)',
                  border: '1px solid hsl(217 33% 26%)',
                  borderRadius: '8px',
                  color: 'hsl(210 40% 98%)',
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Bar Chart - Tipos Comerciais */}
      <Card className="p-4">
        <h3 className="font-semibold mb-4">Distribuição por Tipo Comercial</h3>
        <div className="h-[250px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={demographics.commercialTypes} layout="vertical">
              <XAxis type="number" stroke="hsl(215 20% 65%)" fontSize={12} />
              <YAxis
                type="category"
                dataKey="name"
                stroke="hsl(215 20% 65%)"
                fontSize={12}
                width={80}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(217 33% 17%)',
                  border: '1px solid hsl(217 33% 26%)',
                  borderRadius: '8px',
                  color: 'hsl(210 40% 98%)',
                }}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {demographics.commercialTypes.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}

export function StrategyTabs({ regions, strategy, demographics, onFocusRegion }: StrategyTabsProps) {
  return (
    <Card className="p-4">
      <Tabs defaultValue="summary" className="w-full">
        <TabsList className="w-full flex-wrap h-auto gap-1 bg-muted/50 p-1">
          <TabsTrigger value="summary" className="flex-1 min-w-[120px]">
            Resumo Executivo
          </TabsTrigger>
          <TabsTrigger value="top10" className="flex-1 min-w-[120px]">
            Top 10 Regiões
          </TabsTrigger>
          <TabsTrigger value="strategy" className="flex-1 min-w-[120px]">
            Estratégia Comercial
          </TabsTrigger>
          <TabsTrigger value="demographics" className="flex-1 min-w-[120px]">
            Análise Demográfica
          </TabsTrigger>
        </TabsList>

        <div className="mt-4">
          <TabsContent value="summary" className="mt-0">
            <ExecutiveSummaryTab strategy={strategy} />
          </TabsContent>
          <TabsContent value="top10" className="mt-0">
            <Top10Tab regions={regions} onFocusRegion={onFocusRegion} />
          </TabsContent>
          <TabsContent value="strategy" className="mt-0">
            <StrategyTab strategy={strategy} />
          </TabsContent>
          <TabsContent value="demographics" className="mt-0">
            <DemographicsTab demographics={demographics} />
          </TabsContent>
        </div>
      </Tabs>
    </Card>
  );
}
