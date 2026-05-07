import { useState } from 'react';
import { Loader2, ArrowRight, ArrowLeft, MessageSquare, Target, Wallet, Sparkles, MapPin } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';

export type Objetivo = 'expandir' | 'testar' | 'primeiro_ponto';
export type Investimento = 'baixo' | 'medio' | 'alto';

export interface BusinessContextData {
  descricao: string;
  objetivo: Objetivo;
  investimento: Investimento;
  usarApi: boolean;
}

interface BusinessChatProps {
  onSubmit: (ctx: BusinessContextData) => void;
  isLoading: boolean;
}

const OBJETIVOS: { value: Objetivo; label: string; desc: string }[] = [
  { value: 'expandir', label: 'Expandir', desc: 'Já tenho um negócio e quero abrir filial' },
  { value: 'testar', label: 'Testar mercado', desc: 'Quero validar antes de investir muito' },
  { value: 'primeiro_ponto', label: 'Primeiro ponto', desc: 'Vou abrir meu primeiro estabelecimento' },
];

const INVESTIMENTOS: { value: Investimento; label: string; desc: string }[] = [
  { value: 'baixo', label: 'Baixo', desc: 'até R$ 30k' },
  { value: 'medio', label: 'Médio', desc: 'R$ 30k – 150k' },
  { value: 'alto', label: 'Alto', desc: 'acima de R$ 150k' },
];

export function BusinessChat({ onSubmit, isLoading }: BusinessChatProps) {
  const [step, setStep] = useState(0);
  const [descricao, setDescricao] = useState('');
  const [objetivo, setObjetivo] = useState<Objetivo | null>(null);
  const [investimento, setInvestimento] = useState<Investimento | null>(null);
  const [usarApi, setUsarApi] = useState(false);

  const canNext0 = descricao.trim().length >= 20;
  const canNext1 = objetivo !== null;
  const canSubmit = investimento !== null && objetivo !== null && canNext0;

  const handleFinish = () => {
    if (!canSubmit) return;
    onSubmit({ descricao: descricao.trim(), objetivo: objetivo!, investimento: investimento!, usarApi });
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Indicador de etapas */}
      <div className="mb-6 flex items-center justify-center gap-2">
        {[0, 1, 2].map((s) => (
          <div
            key={s}
            className={`h-1.5 w-8 rounded-full transition-colors ${
              s <= step ? 'bg-primary' : 'bg-muted'
            }`}
          />
        ))}
        <span className="ml-2 text-xs text-muted-foreground">Etapa {step + 1} de 3</span>
      </div>

      <div className="rounded-xl border bg-white p-6 shadow-sm min-h-[280px]">
        <AnimatePresence mode="wait">
          {step === 0 && (
            <motion.div
              key="step0"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <div className="mb-4 flex items-center gap-2 text-primary">
                <MessageSquare className="h-5 w-5" />
                <h2 className="text-lg font-semibold">Conte sobre seu negócio</h2>
              </div>
              <p className="mb-3 text-sm text-muted-foreground">
                Descreva em poucas linhas: o que vende ou pretende vender, qual é o público,
                o que diferencia sua proposta. Quanto mais contexto, melhor a recomendação.
              </p>
              <textarea
                value={descricao}
                onChange={(e) => setDescricao(e.target.value)}
                placeholder="Ex: Tenho uma loja de suplementos voltada para atletas amadores, quero expandir para um segundo ponto em Fortaleza. Meu público é jovem de 20-35 anos com renda média..."
                className="w-full min-h-[140px] rounded-lg border border-border bg-background p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 resize-none"
                disabled={isLoading}
                autoFocus
              />
              <div className="mt-1 text-right text-xs text-muted-foreground">
                {descricao.length} caracteres {descricao.length < 20 && `(mínimo 20)`}
              </div>
            </motion.div>
          )}

          {step === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <div className="mb-4 flex items-center gap-2 text-primary">
                <Target className="h-5 w-5" />
                <h2 className="text-lg font-semibold">Qual seu objetivo principal?</h2>
              </div>
              <div className="space-y-2">
                {OBJETIVOS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setObjetivo(opt.value)}
                    disabled={isLoading}
                    className={`w-full text-left p-3 rounded-lg border-2 transition-all ${
                      objetivo === opt.value
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/40 bg-background'
                    }`}
                  >
                    <div className="font-medium text-sm">{opt.label}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">{opt.desc}</div>
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <div className="mb-4 flex items-center gap-2 text-primary">
                <Wallet className="h-5 w-5" />
                <h2 className="text-lg font-semibold">Faixa de investimento?</h2>
              </div>
              <p className="mb-3 text-sm text-muted-foreground">
                A estratégia será adaptada à sua realidade financeira.
              </p>
              <div className="grid grid-cols-3 gap-2">
                {INVESTIMENTOS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => setInvestimento(opt.value)}
                    disabled={isLoading}
                    className={`p-3 rounded-lg border-2 transition-all text-center ${
                      investimento === opt.value
                        ? 'border-primary bg-primary/5'
                        : 'border-border hover:border-primary/40 bg-background'
                    }`}
                  >
                    <div className="font-medium text-sm">{opt.label}</div>
                    <div className="text-xs text-muted-foreground mt-0.5">{opt.desc}</div>
                  </button>
                ))}
              </div>

              {/* Toggle Google Places */}
              <div className="mt-4 flex items-center justify-center gap-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setUsarApi(v => !v)}
                  className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus:outline-none ${usarApi ? 'bg-primary' : 'bg-muted-foreground/30'}`}
                  aria-pressed={usarApi}
                  disabled={isLoading}
                >
                  <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${usarApi ? 'translate-x-4' : 'translate-x-0'}`} />
                </button>
                <label className="flex items-center gap-1 text-xs text-muted-foreground cursor-pointer select-none" onClick={() => !isLoading && setUsarApi(v => !v)}>
                  <MapPin className="h-3 w-3" />
                  Análise de mercado real (Google Places)
                  {usarApi && <span className="ml-1 text-amber-500 font-medium">(+15–30s)</span>}
                </label>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navegação */}
      <div className="mt-4 flex items-center justify-between">
        <Button
          type="button"
          variant="ghost"
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0 || isLoading}
          className="gap-1"
        >
          <ArrowLeft className="h-4 w-4" /> Voltar
        </Button>

        {step < 2 ? (
          <Button
            type="button"
            onClick={() => setStep((s) => s + 1)}
            disabled={isLoading || (step === 0 && !canNext0) || (step === 1 && !canNext1)}
            className="gap-1"
          >
            Próximo <ArrowRight className="h-4 w-4" />
          </Button>
        ) : (
          <Button
            type="button"
            onClick={handleFinish}
            disabled={!canSubmit || isLoading}
            className="gap-1"
          >
            {isLoading ? (
              <><Loader2 className="h-4 w-4 animate-spin" /> Analisando…</>
            ) : (
              <><Sparkles className="h-4 w-4" /> Gerar análise</>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
