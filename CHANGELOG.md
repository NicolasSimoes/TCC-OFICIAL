# Changelog - Smart Sale Fortaleza

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [2.0.0] - 2024-11-04

### 🔒 Segurança

#### CORRIGIDO
- **API Key Exposta:** Removida chave hardcoded do código
- Criado sistema de variáveis de ambiente com `.env`
- Adicionado `.env.example` como template
- Atualizado `.gitignore` para proteger credenciais

### 🤖 NLP - Análise de Produtos

#### ADICIONADO
- **8 nichos de mercado:** Fitness, Infantil, Escolar, Alimentação, Farmácia, Beleza, Pet, Eletrônicos
- **Análise expandida:** Mais de 100 palavras-chave categorizadas
- **Sistema de scoring:** Contagem inteligente de matches por nicho
- **Funções auxiliares:**
  - `sugerir_pois_para_nicho()` - POIs relevantes por nicho
  - `sugerir_pesos_classe()` - Pesos dinâmicos por classe social
  - `analisar_produto_completo()` - Análise completa do produto

#### MELHORADO
- Classificação mais precisa com análise contextual
- Pesos adaptativos baseados no nicho identificado
- Documentação completa com type hints

### 📊 Data Loading

#### ADICIONADO
- **Novo módulo `data_loader.py`:**
  - Suporte a CSV e Excel com detecção automática
  - Normalização de cabeçalhos (remove acentos, padroniza)
  - Mapeamento inteligente de colunas (aliases)
  - Limpeza automática de coordenadas
  - Validação de classes sociais
  - Remoção de duplicatas
  - Pipeline completo `carregar_e_preparar_dados()`

#### CORRIGIDO
- Inconsistência entre formatos Excel e CSV
- Coordenadas multiplicadas por 1.000.000 agora são corrigidas
- Colunas faltantes agora geram erros claros

### 🔧 Clustering Pipeline

#### ADICIONADO
- Tratamento robusto de erros em todas as funções
- Sistema de retry com backoff exponencial
- Validação de status da API (OVER_QUERY_LIMIT, etc)
- Mensagens de progresso coloridas (✓, ⚠️, ❌)
- Número adaptativo de clusters baseado no dataset
- Logs detalhados de cada etapa

#### MELHORADO
- `gerar_regioes_ideais()` agora funciona com Excel e CSV
- Aplicação correta de filtros (classe, tipo, bairro)
- Fallback gracioso quando há poucos dados
- Cache otimizado de chamadas à API
- Performance de requests HTTP (retry automático)

#### CORRIGIDO
- Timeout em requests agora é tratado
- Erros da API não quebram o pipeline
- Dados vazios retornam lista vazia ao invés de erro

### 🎨 Interface (Streamlit)

#### ADICIONADO
- **Sidebar aprimorada:**
  - Descrições detalhadas dos filtros
  - Contador de filtros ativos
  - Seção "Sobre" com tecnologias
  - 13+ bairros de Fortaleza
  - Opção "Todos" para tipo comercial
- **Feedback visual:**
  - 3 métricas coloridas (Nicho, POIs, Classe Focal)
  - Barra de progresso por classe social
  - Expander com detalhes da análise
  - Emojis e ícones informativos
- **Melhor UX:**
  - Mensagens de erro amigáveis
  - Loading states com spinners
  - Mapa responsivo (1200x600)
  - Layout otimizado

#### CORRIGIDO
- Filtros agora são aplicados corretamente
- Imports corrigidos (paths relativos)
- Compatibilidade com novo sistema de análise

### 📈 Visualizações

#### ADICIONADO
- **Novo módulo `visualizations.py`:**
  - `plot_elbow_method()` - Método Elbow para K ideal
  - `plot_silhouette_scores()` - Scores por número de clusters
  - `plot_silhouette_analysis()` - Análise detalhada por cluster
  - `plot_cluster_distribution()` - Barras + Pizza
  - `plot_cluster_characteristics()` - 4 gráficos de análise
  - `fig_to_base64()` - Conversão para Streamlit

#### CARACTERÍSTICAS
- Gráficos profissionais com Matplotlib/Seaborn
- Anotações automáticas de valores
- Cores customizáveis por tema
- Exportação em alta resolução (150 DPI)

### ⚙️ Configuração

#### ADICIONADO
- **Novo módulo `config.py`:**
  - Configurações centralizadas
  - Constantes organizadas por categoria
  - Validação automática ao importar
  - Documentação inline
  - Suporte a múltiplos nichos

### 📝 Documentação

#### ADICIONADO
- **README.md completo:**
  - Badges de status
  - Índice navegável
  - Seção de instalação detalhada
  - Guia de configuração da API
  - Exemplos de uso (CLI + Web)
  - API Reference
  - Estrutura do projeto
  - Explicação de algoritmos
  - Roadmap futuro
- **Script de verificação:**
  - `check_setup.py` - Valida ambiente completo
  - Testes automáticos de imports
  - Sugestões de correção
  - Resumo colorido

#### MELHORADO
- Comentários de código mais descritivos
- Docstrings completas com type hints
- Mensagens de erro mais claras

### 📦 Dependências

#### ATUALIZADO
- `requirements.txt` limpo e organizado
- Apenas dependências essenciais
- Versões específicas para estabilidade
- Comentários por categoria
- Dependências opcionais marcadas

#### REMOVIDO
- Pacotes não utilizados (70+ removidos):
  - MySQL connectors
  - Selenium, PyAutoGUI
  - Game engines
  - Etc.

### 🐛 Correções de Bugs

#### CORRIGIDO
- API key hardcoded exposta no repositório
- Pipeline quebrado entre Excel e CSV
- Filtros da interface não aplicados
- Imports circulares
- Coordenadas inválidas quebrando o app
- Clusters com poucos dados gerando erro
- Cache não sendo salvo corretamente
- Timeout sem retry
- Mensagens de erro crípticas

### 🚀 Performance

#### MELHORADO
- Retry automático em falhas de rede
- Cache inteligente de POIs (economia de quota)
- Requests com session persistente
- Processamento otimizado de dados
- Número adaptativo de clusters

### ⚠️ Breaking Changes

- `gerar_regioes_ideais()` agora retorna formato diferente
- Estrutura de filtros padronizada
- Colunas de dados devem seguir novo schema
- API key agora via `.env` (obrigatório)

### 🔜 Próximos Passos

- [ ] Integração com OpenAI para NLP contextual
- [ ] Exportação de relatórios em PDF
- [ ] Dashboard de métricas em tempo real
- [ ] Suporte a múltiplas cidades
- [ ] API REST para integração externa
- [ ] Testes automatizados
- [ ] CI/CD pipeline

---

## [1.0.0] - 2024-XX-XX (Versão Original)

### Funcionalidades Iniciais
- NLP básico com regex
- Clustering KMeans
- Visualização com Folium
- Interface Streamlit básica
- Integração com Google Places API

### Problemas Conhecidos
- API key exposta no código
- Pipeline inconsistente
- Sem tratamento de erros
- Filtros não funcionais
- Documentação mínima

---

**Formato baseado em [Keep a Changelog](https://keepachangelog.com/)**
