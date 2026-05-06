# Smart Sale Fortaleza

Sistema inteligente de recomendacao de localizacao para vendas em Fortaleza usando IA, Machine Learning e analise geoespacial.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

---

## Visao Geral

O **Smart Sale Fortaleza** e uma aplicacao de geomarketing que utiliza inteligencia artificial e machine learning para identificar os melhores locais de venda de produtos em Fortaleza/CE. O sistema:

1. **Analisa** o produto usando NLP avancado
2. **Identifica** o nicho de mercado automaticamente
3. **Enriquece** dados com POIs (Points of Interest) via Google Places API
4. **Clusteriza** localizacoes usando KMeans
5. **Ranqueia** regioes por potencial de venda
6. **Gera estrategia** comercial com OpenAI GPT-4o-mini
7. **Visualiza** resultados em mapas interativos

---

## Arquitetura

\Frontend (React/TS) <--HTTP--> Backend (FastAPI/Python)
                                 |- NLP: TF-IDF + ComplementNB
                                 |- Clustering: KMeans / DBSCAN
                                 |- Google Places API
                                 \- OpenAI GPT-4o-mini
\
---

## Tecnologias

| Camada | Tecnologia | Versao |
|--------|-----------|--------|
| Frontend | React + TypeScript | 18+ |
| Estilo | Tailwind CSS | 3+ |
| Mapas | Leaflet + React-Leaflet | 1.9+ |
| Graficos | Recharts | 2+ |
| Animacoes | Framer Motion | 10+ |
| Backend | FastAPI | 0.100+ |
| ML / NLP | scikit-learn | 1.3+ |
| Geo | GeoPandas, Folium | latest |
| IA | OpenAI GPT-4o-mini | 2.35+ |
| POIs | Google Places API | v1 |

---

## Pipeline de Analise

### 1. Classificacao NLP
- Modelo: **TF-IDF + ComplementNB**
- 9 nichos: Fitness, Infantil, Escolar, Alimentacao, Farmacia, Beleza, Pet, Eletronicos, Saude
- Confianca calculada por probabilidade posterior

### 2. Feature Engineering
- Features de nicho: scores normalizados por tipo de POI proximo
- Normalizacao: StandardScaler

### 3. Clustering
- **Algoritmo selecionado**: KMeans (comparado com DBSCAN)
- **k otimo**: metodo do cotovelo + **knee point** (distancia perpendicular)
- **Metricas**: Silhouette Score, Davies-Bouldin Index, Inertia

### 4. Ranking e Score
- Score por linha: 0.70 x (classe/5) + 0.30 x rank_bonus (sem POIs)
- Com POIs: peso_poi x poi_norm + peso_classe x (classe/5)
- Escala final: 0-100

---

## Instalacao

### Pre-requisitos
- Python 3.8+
- Node.js 18+
- Chaves de API: Google Places + OpenAI (opcionais, mas recomendadas)

### Backend

\\ash
git clone https://github.com/NicolasSimoes/TCC-OFICIAL.git
cd TCC-OFICIAL
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
\
### Frontend

\\ash
cd frontend
npm install
npm run dev
\
---

## Configuracao

Copie \.env.example\ para \.env\ e preencha suas chaves:

\\env
GOOGLE_API_KEY=sua_chave_google_places
OPENAI_API_KEY=sua_chave_openai
API_HOST=0.0.0.0
API_PORT=8000
API_CORS_ORIGINS=http://localhost:5173
\
> As APIs sao **opcionais**. Sem elas, o sistema usa dados locais e gera estrategias baseadas em templates.

---

## Uso

### Iniciar o Backend

\\ash
.venv\Scripts\activate
python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
\
### Iniciar o Frontend

\\ash
cd frontend && npm run dev
\
### Verificar saude da API

\\ash
curl http://localhost:8000/health
\
---

## API Reference

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | /health | Status e configuracao das APIs |
| POST | /analyze/product | Analise completa (NLP + clustering + estrategia) |
| POST | /analyze | Analise geoespacial simples |
| POST | /strategy | Geracao de estrategia comercial |

---

## Testes

\\ash
pytest tests/ -v
\
> 59 testes automatizados cobrindo: carregamento de dados, NLP, clustering, mapas e integracao.

---

## Autor

**Nicolas Simoes**
Bacharelado em Ciencias da Computacao
