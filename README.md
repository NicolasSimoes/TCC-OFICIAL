# 🎯 Smart Sale Fortaleza

Sistema inteligente de recomendação de localização para vendas em Fortaleza usando IA, Machine Learning e análise geoespacial.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Uso](#uso)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [API Reference](#api-reference)
- [Contribuindo](#contribuindo)

## 🎯 Visão Geral

O **Smart Sale Fortaleza** é uma aplicação de geomarketing que utiliza inteligência artificial e machine learning para identificar os melhores locais de venda de produtos em Fortaleza/CE. O sistema:

1. **Analisa** o produto usando NLP avançado
2. **Identifica** o nicho de mercado automaticamente
3. **Enriquece** dados com POIs (Points of Interest) via Google Places API
4. **Clusteriza** localizações usando KMeans
5. **Ranqueia** regiões por potencial de venda
6. **Visualiza** resultados em mapas interativos

## ✨ Funcionalidades

### 🤖 Análise Inteligente de Produtos
- Classificação automática em 8+ nichos de mercado
- Sugestão dinâmica de POIs relevantes
- Pesos adaptativos por classe socioeconômica

### 📍 Enriquecimento Geográfico
- Integração com Google Places API
- Busca multiradial (400m, 800m, 1200m)
- Cache inteligente para economia de quota

### 📊 Machine Learning
- Clustering KMeans com número adaptativo de clusters
- Ranking automático por potencial de venda
- Métricas de qualidade (Silhouette Score)

### 🗺️ Visualização Avançada
- Mapas interativos com Folium
- HeatMaps por densidade
- Filtros dinâmicos por classe, tipo e bairro
- Gráficos de análise (Elbow, Silhouette)

### 🎨 Interface Moderna
- Design dark theme responsivo
- Feedback visual em tempo real
- Métricas e indicadores coloridos
- Expansíveis com detalhes da análise

## 🛠️ Tecnologias

### Core
- **Python 3.8+**
- **Streamlit** - Interface web
- **Pandas** - Manipulação de dados
- **Scikit-learn** - Machine Learning

### Visualização
- **Folium** - Mapas interativos
- **Matplotlib/Seaborn** - Gráficos estatísticos
- **Streamlit-Folium** - Integração de mapas

### APIs & Serviços
- **Google Places API** - Dados de POIs
- **OpenAI API** (opcional) - NLP avançado

### Utilidades
- **python-dotenv** - Gerenciamento de variáveis
- **requests** - HTTP com retry automático
- **openpyxl** - Leitura de Excel

## 📦 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Conta Google Cloud (para Places API)

### Passo a Passo

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/smart-sale-fortaleza.git
cd smart-sale-fortaleza

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt
```

## ⚙️ Configuração

### 1. Configure as Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e adicione suas chaves de API:

```env
# Google Places API Key (OBRIGATÓRIA para enriquecimento de POIs)
GOOGLE_API_KEY=sua_chave_google_aqui

# OpenAI API Key (OPCIONAL - para NLP avançado futuro)
OPENAI_API_KEY=sua_chave_openai_aqui
```

### 2. Obtenha a Google Places API Key

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione existente
3. Ative a **Places API**
4. Crie credenciais (API Key)
5. Copie a chave para o arquivo `.env`

⚠️ **Importante:** Proteja sua API key! Nunca commite o arquivo `.env`.

### 3. Prepare os Dados

Certifique-se de ter um arquivo de dados em `data/`:
- `Projeto.xlsx` (Excel) ou
- `clientes.csv` (CSV)

Formato esperado das colunas:
- `CLIENTE/NOME`: Nome do cliente
- `LATITUDE/LAT`: Coordenada de latitude
- `LONGITUDE/LON`: Coordenada de longitude
- `CLASSE SOCIAL/CLASSE`: A, B, C, D ou E
- `TIPO COMERCIAL/TIPO`: Categoria do estabelecimento
- `BAIRRO`: Bairro da localização

## 🚀 Uso

### Interface Web (Recomendado)

```bash
# Inicie a aplicação Streamlit
streamlit run src/interface.py
```

Acesse no navegador: `http://localhost:8501`

#### Usando a Interface:

1. **Digite o produto** no campo de busca (ex: "whey protein")
2. **Configure filtros** na sidebar:
   - Classe social (A, B, C, D, E)
   - Tipo de estabelecimento
   - Bairros específicos
3. **Clique em "Send"** para processar
4. **Visualize resultados**:
   - Nicho identificado
   - Métricas de análise
   - Mapa interativo com regiões ideais

### Linha de Comando

Para processamento em lote ou análises customizadas:

```bash
# Clustering completo com enriquecimento de POIs
python src/clustering_pipeline.py \
    --input data/clientes.csv \
    --usar_api true \
    --n_clusters 5 \
    --out_prefix resultados

# Sem usar a API (usa dados existentes)
python src/clustering_pipeline.py \
    --input data/clientes_enriquecidos.csv \
    --usar_api false \
    --n_clusters 3
```

#### Parâmetros:
- `--input`: Caminho para arquivo CSV de entrada
- `--usar_api`: `true` para buscar POIs, `false` para usar dados existentes
- `--n_clusters`: Número de clusters desejado
- `--out_prefix`: Prefixo dos arquivos de saída

#### Saídas:
- `{prefix}_enriquecidos.csv`: Dados com POIs
- `{prefix}_clusterizados.csv`: Dados com labels de cluster
- `{prefix}_mapa_clusters.html`: Mapa HTML interativo

## 📁 Estrutura do Projeto

```
TCC-Project-dev/
├── src/
│   ├── main.py                 # Orquestrador principal
│   ├── nlp.py                  # Análise de nicho e NLP
│   ├── clustering_pipeline.py  # Pipeline ML completo
│   ├── map.py                  # Geração de mapas
│   ├── interface.py            # Interface Streamlit
│   ├── data_loader.py          # Carregamento de dados
│   └── visualizations.py       # Gráficos e análises
│
├── data/
│   ├── Projeto.xlsx            # Dados principais (Excel)
│   ├── clientes.csv            # Dados brutos (CSV)
│   └── clientes_enriquecidos.csv # Dados + POIs
│
├── assets/
│   └── sale_icon_264139.png    # Ícones da aplicação
│
├── .env                        # Variáveis de ambiente (NÃO COMMITAR!)
├── .env.example                # Template de variáveis
├── .gitignore                  # Arquivos ignorados pelo Git
├── requirements.txt            # Dependências Python
├── README.md                   # Este arquivo
└── Mental Map.txt              # Documentação conceitual
```

## 🔌 API Reference

### `nlp.py`

#### `identificar_nicho(texto: str) -> str`
Identifica o nicho do produto baseado em palavras-chave.

**Parâmetros:**
- `texto`: Descrição do produto

**Retorna:** Nome do nicho (Fitness, Infantil, Escolar, etc.)

#### `analisar_produto_completo(produto: str) -> dict`
Análise completa incluindo nicho, POIs e pesos.

**Retorna:**
```python
{
    "nicho": "Fitness",
    "pois_sugeridos": ["gym", "health", "spa"],
    "pesos_classe": {"A": 50000, "B": 30000, "C": 5000},
    "descricao": "..."
}
```

### `clustering_pipeline.py`

#### `gerar_regioes_ideais(produto: str, filtros: dict) -> list`
Gera lista de regiões ideais usando clustering.

**Parâmetros:**
- `produto`: Nome do produto
- `filtros`: Dict com `classe`, `tipo`, `bairro`

**Retorna:** Lista de tuplas `(lat, lon, nome)`

### `data_loader.py`

#### `carregar_e_preparar_dados(caminho: str, sheet_name: Optional[str]) -> pd.DataFrame`
Carrega e prepara dados de CSV ou Excel.

**Features:**
- Detecção automática de formato
- Normalização de cabeçalhos
- Limpeza de coordenadas
- Validação de dados

## 📊 Algoritmos e Métricas

### Clustering
- **Algoritmo:** KMeans (sklearn)
- **Features:** Classe socioeconômica + POIs normalizados + Tipo comercial (one-hot)
- **Número de clusters:** Adaptativo (min 2, max 5, baseado no tamanho do dataset)

### Ranking de Clusters
Score de potencial calculado como:
```
score = 0.6 × média_POIs_normalizados + 0.4 × (classe_média / 5.0)
```

### Métricas de Qualidade
- **Silhouette Score:** Mede qualidade da separação dos clusters
- **Inércia:** Within-cluster sum of squares
- **Elbow Method:** Determina k ideal

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Notas de Desenvolvimento

### Cache de POIs
O sistema mantém cache local em `cache_places.parquet` para:
- Economia de quota da API
- Performance melhorada
- Consistência entre execuções

### Limitações Conhecidas
- Google Places API tem limite de 60 requisições/minuto
- Dataset pequeno pode gerar clusters ruins
- Coordenadas inválidas são descartadas automaticamente

### Roadmap
- [ ] Integração com OpenAI para NLP contextual
- [ ] Suporte a múltiplas cidades
- [ ] Exportação de relatórios em PDF
- [ ] Dashboard de métricas em tempo real
- [ ] API REST para integração externa

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Autores

- **Desenvolvedor** - Projeto TCC
- **Orientador** - [Nome]

## 🙏 Agradecimentos

- Google Places API
- Comunidade Streamlit
- Scikit-learn
- Folium

---

**Desenvolvido com ❤️ em Fortaleza/CE**
#   T C C - O F I C I A L  
 #   T C C - O F I C I A L  
 #   T C C - O F I C I A L  
 