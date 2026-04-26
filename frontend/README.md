# Smart Sale Fortaleza - Frontend

Frontend React moderno para o sistema Smart Sale Fortaleza - Geomarketing com IA.

## Stack Técnica

- **React 18** + **TypeScript**
- **Vite** (bundler)
- **TailwindCSS 3** (estilização)
- **shadcn/ui** (componentes base)
- **react-leaflet** (mapas interativos)
- **Recharts** (gráficos)
- **Framer Motion** (animações)
- **Lucide React** (ícones)

## Instalação

```bash
cd frontend
npm install
```

## Desenvolvimento

```bash
npm run dev
```

O servidor de desenvolvimento será iniciado em `http://localhost:5173`.

## Build para Produção

```bash
npm run build
npm run preview
```

## Estrutura de Pastas

```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── ui/           # Componentes shadcn/ui
│   │   ├── AppHeader.tsx
│   │   ├── SearchBar.tsx
│   │   ├── FilterSidebar.tsx
│   │   ├── SuccessBanner.tsx
│   │   ├── MetricsCards.tsx
│   │   ├── AnalysisDetails.tsx
│   │   ├── MapView.tsx
│   │   ├── StrategyTabs.tsx
│   │   ├── MarketInsights.tsx
│   │   └── ActionPlan.tsx
│   ├── lib/
│   │   ├── mock-data.ts  # Dados de demonstração
│   │   └── utils.ts      # Utilitários
│   ├── types/
│   │   └── index.ts      # Tipos TypeScript
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## Features

- 🗺️ Mapa interativo com Leaflet
- 📊 Gráficos de análise demográfica
- 🎨 Design System com tema escuro
- 📱 Totalmente responsivo (mobile-first)
- 🔍 Busca com autocomplete
- 🎯 Filtros por classe social, tipo comercial e bairros
- ✅ Plano de ação com persistência local
- ♿ Acessível (WCAG 2.1 AA)

## Design System

### Cores (HSL)

| Token | Cor | HSL |
|-------|-----|-----|
| Background | #0f172a | 222 47% 11% |
| Card | #1e293b | 217 33% 17% |
| Primary | #22c55e | 142 71% 45% |
| Foreground | #f1f5f9 | 210 40% 98% |
| Muted | #cbd5e1 | 215 20% 65% |
| Border | #334155 | 217 33% 26% |

### Breakpoints

| Nome | Min-width |
|------|-----------|
| sm | 640px |
| md | 768px |
| lg | 1024px |
| xl | 1280px |

## Licença

MIT © Smart Sale Fortaleza
