import streamlit as st
import time
from main import processar_requisicao
from streamlit_folium import st_folium
from nlp import analisar_produto_completo, gerar_estrategia_comercial
import sys
from pathlib import Path
import hashlib

# Adiciona src ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

# OTIMIZAÇÃO: Cache para análises de produto (evita reprocessamento)
@st.cache_data(ttl=3600, show_spinner=False)
def analisar_produto_cached(produto: str):
    """Versão cacheada da análise de produto."""
    return analisar_produto_completo(produto)

@st.cache_data(ttl=3600, show_spinner=False)
def processar_requisicao_cached(produto: str, filtros_hash: str, _filtros: dict):
    """Versão cacheada do processamento de requisição.

    O parâmetro `_filtros` começa com underscore para que o Streamlit não
    tente fazer hash de um dict mutável (quebraria o cache). A chave de
    cache real é `filtros_hash`.
    """
    return processar_requisicao(produto, _filtros)

st.set_page_config(
    page_title="Smart Sale Fortaleza",
    page_icon="./assets/sale_icon_264139.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

#CSS
st.markdown("""
    <style>
        /* Fundo geral */
        .stApp {
            background-color: #0f172a;
            color: #e2e8f0;
            font-family: 'Inter', sans-serif;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1e293b;
        }

        /* Título da sidebar */
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
            color: #22c55e;
            font-weight: 700;
        }

        /* Textos e inputs */
        .stTextInput > div > div > input {
            background-color: #1f2937;
            color: #f9fafb;
            border-radius: 8px;
            border: 1px solid #374151;
        }

        /* Botões */
        .stButton>button {
            background-color: #22c55e !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            height: 30px !important; /* força altura igual ao input */
            width: 100% !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            transition: 0.2s;
            margin-top: 2px !important; /* corrige alinhamento */
        }

        .stButton>button:hover {
            background-color: #16a34a !important;
            transform: scale(1.03);
        }

        .stButton>button:focus {
            outline: none !important;
            box-shadow: none !important;
        }

        /* Cabeçalho */
        .main-title {
            color: #22c55e;
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-top: 10px;
        }

        .subtitle {
            text-align: center;
            color: #94a3b8;
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }

        /* Placeholder */
        .stAlert {
            background-color: #1f2937;
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)




#sidebar
with st.sidebar:
    st.header("🎯 Filtros Avançados")
    
    st.markdown("---")
    st.subheader("Classe Social")
    classe = st.multiselect(
        "Selecione as classes de interesse",
        ["A", "B", "C", "D", "E"],
        default=[],
        help="Classe A: Alta renda, B: Média-alta, C: Média, D/E: Baixa renda"
    )
    
    st.markdown("---")
    st.subheader("Tipo de Estabelecimento")
    tipo = st.selectbox(
        "Tipo comercial",
        ["Todos", "PEQUENOS REGIONAIS", "SUPER REGIONAIS", "Mercado", "Farmácia", "Academia"],
        index=0,
        help="Filtre por tipo de estabelecimento comercial"
    )
    
    st.markdown("---")
    st.subheader("Bairros")
    bairros_disponiveis = [
        "Aldeota", "Meireles", "Centro", "Varjota", "Montese",
        "Messejana", "Barra do Ceara", "Papicu", "Cocó", "Dionísio Torres",
        "Joaquim Távora", "Fátima", "Benfica"
    ]
    bairro = st.multiselect(
        "Selecione os bairros",
        bairros_disponiveis,
        default=[],
        help="Deixe vazio para considerar todos os bairros"
    )
    
    st.markdown("---")
    
    # Opção de enriquecimento de POIs
    st.subheader("🔧 Opções Avançadas")
    usar_api = st.checkbox(
        "Enriquecer com Google Places API",
        value=False,
        help="⚠️ Consulta a API do Google Places para buscar POIs próximos. Consome quota da API."
    )
    
    if not usar_api:
        st.warning("⚠️ POIs desabilitados. Os dados de localização não incluirão pontos de interesse próximos.")
    else:
        st.info("✓ API habilitada. Consultará POIs próximos (academias, supermercados, etc.)")
    
    st.markdown("---")
    
    # Contador de filtros ativos
    filtros_ativos = 0
    if classe: filtros_ativos += 1
    if tipo and tipo != "Todos": filtros_ativos += 1
    if bairro: filtros_ativos += 1
    
    if filtros_ativos > 0:
        st.success(f"✓ {filtros_ativos} filtro(s) ativo(s)")
    else:
        st.info("ℹ️ Nenhum filtro aplicado")
    
    st.markdown("---")
    st.markdown("### 📊 Sobre")
    st.markdown("""
    **Smart Sale Fortaleza** usa:
    - 🤖 IA para análise de produto
    - 📍 Dados geográficos  
    - 📈 Machine Learning
    - 🗺️ Visualização interativa
    """)




st.markdown("<h1 class='main-title'>Smart Sale Fortaleza</h1>", unsafe_allow_html=True)

st.markdown("<p class='subtitle'>Encontre os melhores locais para vender seu produto em Fortaleza</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Inicializa session_state para manter resultados
if 'resultados' not in st.session_state:
    st.session_state.resultados = None

col1, col2, col3 = st.columns([2, 6, 2])
with col2:
    # Campo + botão estilo ChatGPT
    col_input, col_button = st.columns([7, 1])

    with col_input:
        produto = st.text_input(
            "Produto",
            placeholder="Digite o produto que deseja vender...",
            label_visibility="collapsed",
            key="produto_input"
        )

    with col_button:
        enviar = st.button("Send", key="enviar_button")

    # Estilização adicional do input (foco)
    st.markdown("""
    <style>
        div[data-baseweb="input"] > div:focus-within {
            border: 1px solid #22c55e !important;
        }
    </style>
    """, unsafe_allow_html=True)
   
if enviar:
    if not produto.strip():
        st.warning("⚠️ Você não digitou nada ainda!")
    else:
        # Prepara filtros
        filtros = {
            "classe": classe if classe else [],
            "tipo": None if tipo == "Todos" else tipo,
            "bairro": bairro if bairro else [],
            "usar_api": usar_api
        }
        
        # OTIMIZADO: Usa cache para evitar reprocessamento
        # Mostra análise do produto (com cache)
        with st.spinner("🔍 Analisando produto..."):
            analise = analisar_produto_cached(produto)
        
        # Cria hash dos filtros para cache (converte dict para string ordenada)
        filtros_str = f"{sorted(filtros.items())}"
        filtros_hash = hashlib.md5(filtros_str.encode()).hexdigest()
        
        # Processa regiões ideais (com cache)
        if usar_api:
            with st.spinner("📍 Identificando melhores regiões... (Enriquecendo ~10 locais com Google Places API - ~20 segundos)"):
                nicho, mapa, regioes = processar_requisicao_cached(produto, filtros_hash, _filtros=filtros)
        else:
            with st.spinner("📍 Identificando melhores regiões..."):
                nicho, mapa, regioes = processar_requisicao_cached(produto, filtros_hash, _filtros=filtros)
        
        # NÃO gera estratégia automaticamente (será gerada sob demanda na aba)
        # Salva resultados no session_state SEM estratégia ainda
        # NOTA: Não salvamos o mapa diretamente - ele será regenerado a partir das regiões
        st.session_state.resultados = {
            'produto': produto,
            'analise': analise,
            'nicho': nicho,
            'regioes': regioes,
            'estrategia': None  # Será gerada sob demanda
        }

# Mostra resultados se existirem
if st.session_state.resultados is not None:
    res = st.session_state.resultados
    
    # Feedback de sucesso NO TOPO
    st.success(f"✅ Análise completa! Produto: **{res['produto']}** | Nicho: **{res['analise']['nicho']}**")
    
    st.markdown("---")
    
    # Exibe resultado da análise - MÉTRICAS
    st.markdown("### 📊 Análise do Produto")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Nicho Identificado", res['analise']['nicho'], delta="Alta precisão")
    with col_b:
        st.metric("POIs Relevantes", len(res['analise']['pois_sugeridos']), delta="Tipos mapeados")
    with col_c:
        pesos = res['analise']['pesos_classe']
        classe_foco = max(pesos, key=pesos.get)
        st.metric("Classe Focal", classe_foco, delta=f"Peso: {pesos[classe_foco]:,}")
    
    # Exibe informações adicionais
    with st.expander("🔍 Detalhes da Análise", expanded=False):
        st.markdown(f"**Descrição:** {res['analise']['descricao']}")
        st.markdown(f"**POIs sugeridos:** {', '.join(res['analise']['pois_sugeridos'][:5])}")
        
        st.markdown("**Pesos por Classe:**")
        for classe_key, peso in res['analise']['pesos_classe'].items():
            st.progress(peso / 50000, text=f"Classe {classe_key}: {peso:,}")
    
    st.markdown("---")
    
    # === MAPA PRIMEIRO (sempre visível) ===
    st.markdown("### 🗺️ Mapa de Regiões Ideais")
    
    # Regenera o mapa a partir das regiões (mais estável que salvar objeto Folium)
    from map import gerar_mapa
    regioes_para_mapa = res.get('regioes', [])
    if regioes_para_mapa:
        mapa_atual = gerar_mapa(regioes_para_mapa, nicho=res.get('nicho', 'Outro'), produto=res.get('produto', ''))
        st_folium(mapa_atual, width=1200, height=600, returned_objects=[], key="mapa_principal")
    else:
        st.warning("⚠️ Nenhuma região encontrada. Ajuste os filtros e tente novamente.")
    
    st.markdown("---")
    
    # === ESTRATÉGIA COMERCIAL APRIMORADA ===
    st.markdown("### 💡 Estratégia Comercial Inteligente")
    
    # OTIMIZAÇÃO: Gera estratégia SOB DEMANDA (lazy loading)
    if res.get('estrategia') is None:
        # Verifica se usuário quer gerar a estratégia
        col_gerar, col_info = st.columns([2, 8])
        with col_gerar:
            gerar_btn = st.button("🚀 Gerar Estratégia Detalhada", key="gerar_estrategia", type="primary")
        with col_info:
            st.info("👆 Clique para gerar estratégia comercial personalizada com IA (OpenAI)")
        
        # Gera estratégia quando botão é clicado
        if gerar_btn:
            with st.spinner("💡 Gerando estratégia comercial com IA... Aguarde ~10 segundos"):
                estrategia = gerar_estrategia_comercial(
                    produto=res['produto'],
                    nicho=res['analise']['nicho'],
                    regioes=res['regioes'],
                    pesos_classe=res['analise']['pesos_classe'],
                    filtros={}
                )
                st.session_state.resultados['estrategia'] = estrategia
                st.rerun()
        
        # Mostra preview básico enquanto não gera
        with st.expander("📋 Preview da Estratégia Básica"):
            st.markdown(f"""
            ### Estratégia Rápida para {res['produto']}
            
            **Nicho:** {res['analise']['nicho']}
            
            **Ações Imediatas:**
            1. Visite as zonas prioritárias no mapa acima
            2. Faça pesquisa de campo nos 3-5 pontos principais
            3. Teste seu produto com clientes reais
            4. Ajuste preço baseado no feedback
            5. Expanda para novas áreas gradualmente
            
            💡 Clique em "Gerar Estratégia" para análise completa com IA
            """)
    
    elif res.get('estrategia'):
        # Tabs para organizar melhor a estratégia
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Visão Geral", "🎯 Execução", "💰 Financeiro", "📈 Métricas"])
        
        with tab1:
            st.markdown("#### 📋 Resumo da Estratégia")
            
            # Cards com informações-chave
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**🎯 Nicho de Mercado**")
                st.info(f"**{res['analise']['nicho']}**")
                st.caption("Categoria identificada por IA")
            
            with col2:
                st.markdown("**👥 Público-Alvo Principal**")
                pesos = res['analise']['pesos_classe']
                classe_foco = max(pesos, key=pesos.get)
                st.success(f"**Classe {classe_foco}**")
                st.caption(f"Peso: {pesos[classe_foco]:,} pontos")
            
            with col3:
                regioes = res.get('regioes', [])
                st.markdown("**📍 Área de Cobertura**")
                if regioes:
                    bairros_unicos = len(set([r.get('nome', '').split(' - ')[0] for r in regioes[:20]]))
                    st.warning(f"**{bairros_unicos}+ bairros**")
                    st.caption(f"{len(regioes)} pontos mapeados")
                else:
                    st.warning("**Verificar filtros**")
            
            st.markdown("---")
            
            # Estratégia completa com formatação melhorada
            st.markdown("#### 📄 Estratégia Detalhada")
            with st.expander("Ver estratégia completa gerada por IA", expanded=False):
                st.markdown(res['estrategia'])
        
        with tab2:
            st.markdown("#### 🚀 Plano de Execução")
            
            # Timeline de ações
            st.markdown("**📅 Semana 1-2: Preparação**")
            col1, col2 = st.columns([1, 9])
            with col1:
                st.markdown("☐")
            with col2:
                st.markdown("Realizar pesquisa de campo nas zonas prioritárias")
            
            col1, col2 = st.columns([1, 9])
            with col1:
                st.markdown("☐")
            with col2:
                st.markdown("Mapear concorrentes diretos e indiretos")
            
            col1, col2 = st.columns([1, 9])
            with col1:
                st.markdown("☐")
            with col2:
                st.markdown("Definir canais de venda (físico, online, parcerias)")
            
            st.markdown("---")
            st.markdown("**📅 Semana 3-4: Teste Piloto**")
            col1, col2 = st.columns([1, 9])
            with col1:
                st.markdown("☐")
            with col2:
                st.markdown("Selecionar 3-5 pontos para venda teste")
            
            col1, col2 = st.columns([1, 9])
            with col1:
                st.markdown("☐")
            with col2:
                st.markdown("Coletar feedback de clientes e ajustar abordagem")
            
            st.markdown("---")
            st.markdown("**📅 Mês 2+: Expansão**")
            col1, col2 = st.columns([1, 9])
            with col1:
                st.markdown("☐")
            with col2:
                st.markdown("Escalar para zonas secundárias se resultados positivos")
            
            col1, col2 = st.columns([1, 9])
            with col1:
                st.markdown("☐")
            with col2:
                st.markdown("Estabelecer parcerias com estabelecimentos locais")
        
        with tab3:
            st.markdown("#### 💰 Análise Financeira")
            
            # Estimativas financeiras baseadas no nicho
            nicho = res['analise']['nicho']
            
            # Dados por nicho (estimativas)
            dados_financeiros = {
                "Fitness": {"investimento": "R$ 5.000 - 15.000", "margem": "30-50%", "payback": "3-6 meses"},
                "Infantil": {"investimento": "R$ 3.000 - 10.000", "margem": "25-40%", "payback": "4-8 meses"},
                "Escolar": {"investimento": "R$ 2.000 - 8.000", "margem": "20-35%", "payback": "2-4 meses"},
                "Alimentação": {"investimento": "R$ 5.000 - 20.000", "margem": "15-30%", "payback": "6-12 meses"},
                "Farmácia": {"investimento": "R$ 3.000 - 12.000", "margem": "20-40%", "payback": "4-8 meses"},
                "Beleza": {"investimento": "R$ 4.000 - 15.000", "margem": "35-60%", "payback": "3-6 meses"},
                "Pet": {"investimento": "R$ 3.000 - 10.000", "margem": "25-45%", "payback": "4-7 meses"},
                "Eletrônicos": {"investimento": "R$ 10.000 - 30.000", "margem": "10-25%", "payback": "8-12 meses"},
                "Outro": {"investimento": "R$ 3.000 - 15.000", "margem": "20-40%", "payback": "4-8 meses"}
            }
            
            dados = dados_financeiros.get(nicho, dados_financeiros["Outro"])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💵 Investimento Inicial", dados["investimento"])
                st.caption("Estimativa para operação piloto")
            with col2:
                st.metric("📊 Margem Esperada", dados["margem"])
                st.caption("Baseado no nicho identificado")
            with col3:
                st.metric("⏱️ Payback Estimado", dados["payback"])
                st.caption("Tempo para retorno do investimento")
            
            st.markdown("---")
            
            st.warning("⚠️ **Atenção:** Valores estimados. Realize análise financeira detalhada antes de investir.")
            
            # Componentes de custo
            with st.expander("💡 Principais componentes de custo"):
                st.markdown("""
                - **Estoque inicial**: Produtos para teste
                - **Logística**: Transporte e armazenamento
                - **Marketing**: Material promocional, divulgação local
                - **Operacional**: Vendedores, comissões
                - **Legalização**: Alvarás, licenças se necessário
                """)
        
        with tab4:
            st.markdown("#### 📈 KPIs Recomendados")
            st.caption("Indicadores-chave para acompanhar o sucesso da operação")
            
            # KPIs por fase
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎯 KPIs de Vendas**")
                st.markdown("""
                - **Ticket Médio**: Valor médio por venda
                - **Taxa de Conversão**: Visitas → Vendas
                - **Volume de Vendas**: Unidades vendidas/dia
                - **Faturamento**: Receita total por zona
                - **Clientes Recorrentes**: % de recompra
                """)
            
            with col2:
                st.markdown("**📊 KPIs Operacionais**")
                st.markdown("""
                - **Cobertura**: % de pontos ativos
                - **Tempo médio por venda**: Eficiência
                - **Estoque girando**: Rotatividade
                - **Satisfação do cliente**: NPS
                - **Custo de Aquisição**: CAC por cliente
                """)
            
            st.markdown("---")
            
            st.info("💡 **Dica**: Defina metas SMART (Específicas, Mensuráveis, Atingíveis, Relevantes, Temporais) para cada KPI")
        
        # Ações rápidas no final
        st.markdown("---")
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            st.download_button(
                label="📥 Download PDF",
                data=res['estrategia'],
                file_name=f"estrategia_{res['produto'].replace(' ', '_')}.txt",
                mime="text/plain",
                key="download_estrategia"
            )
        
        with col_btn2:
            if st.button("📋 Copiar Texto", key="copiar_estrategia"):
                st.toast("✓ Estratégia copiada!")
        
        with col_btn3:
            if st.button("📧 Compartilhar", key="share_estrategia"):
                st.info("💡 Em desenvolvimento: Compartilhamento por email")
        
        with col_btn4:
            if st.button("🔄 Nova Análise", key="nova_analise"):
                st.session_state.resultados = None
                st.rerun()
    
    else:
        st.warning("⚠️ **Estratégia não disponível**")
        st.info("💡 Configure `OPENAI_API_KEY` no arquivo `.env` para gerar estratégias personalizadas com IA.")
        
        # Sugestões básicas mesmo sem API
        with st.expander("📋 Sugestões Básicas de Estratégia"):
            st.markdown(f"""
            ### Estratégia Básica para {res['produto']}
            
            **Nicho:** {res['analise']['nicho']}
            
            **Ações Imediatas:**
            1. Visite as zonas prioritárias identificadas no mapa
            2. Converse com proprietários de estabelecimentos locais
            3. Teste seu produto em 3-5 pontos diferentes
            4. Ajuste preço e abordagem baseado no feedback
            5. Expanda gradualmente para novas áreas
            
            **Canais Sugeridos:**
            - Venda porta-a-porta em estabelecimentos
            - Parcerias com lojas locais
            - Divulgação em redes sociais geolocalizadas
            - Indicações de clientes satisfeitos
            """)
    
    # Análise Estratégica de Regiões
    st.markdown("---")
    st.markdown("### 🎯 Análise Estratégica de Mercado")
    regioes = res.get('regioes', [])
    
    if not regioes:
        st.info("Nenhuma região identificada com os filtros aplicados.")
    else:
        from collections import Counter
        
        # Agrupa por cluster para análise
        regioes_por_cluster = {}
        for regiao in regioes:
            cluster_id = regiao.get('cluster', 'Sem cluster')
            if cluster_id not in regioes_por_cluster:
                regioes_por_cluster[cluster_id] = []
            regioes_por_cluster[cluster_id].append(regiao)
        
        # === RESUMO EXECUTIVO ===
        st.subheader("📊 Resumo Executivo")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Zonas Prioritárias", len(regioes_por_cluster), delta="clusters")
        with col2:
            pontos_totais = len(regioes)
            st.metric("Pontos Mapeados", pontos_totais, delta="locais")
        with col3:
            melhor_cluster = sorted(regioes_por_cluster.items(), 
                                   key=lambda x: x[1][0].get('score', 0), 
                                   reverse=True)[0]
            st.metric("Melhor Zona", f"Cluster {melhor_cluster[0] + 1}", 
                     delta=f"Score {melhor_cluster[1][0].get('score', 0):.2f}")
        with col4:
            classes = set(r.get('classe_social', 'N/A') for r in regioes)
            st.metric("Classes Presentes", len([c for c in classes if c != 'N/A']), delta="variação")
        
        st.markdown("---")
        
        # === ZONAS PRIORITÁRIAS (TOP 3) ===
        st.subheader("🏆 Top 3 Zonas de Atuação")
        st.caption("Áreas com maior potencial de venda baseado em clustering e perfil socioeconômico")
        
        top_clusters = sorted(regioes_por_cluster.items(), 
                            key=lambda x: x[1][0].get('score', 0), 
                            reverse=True)[:3]
        
        for rank, (cluster_id, cluster_regioes) in enumerate(top_clusters, 1):
            info = cluster_regioes[0]
            score = info.get('score', 0)
            classe_med = info.get('classe_med', 0)
            
            # Cor da medalha
            medal = ["🥇", "🥈", "🥉"][rank-1]
            
            with st.expander(f"{medal} **Zona #{rank} - Cluster {cluster_id + 1}** | Score: {score:.2f} | Classe Média: {classe_med:.1f}/5.0", expanded=(rank==1)):
                
                # Características da zona
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.markdown("**📍 Cobertura Geográfica:**")
                    bairros = list(set([r.get('nome', '').split(' - ')[0] for r in cluster_regioes[:10]]))
                    st.write(f"• {len(cluster_regioes)} pontos identificados")
                    st.write(f"• Principais bairros: {', '.join(bairros[:3])}")
                    
                    st.markdown("**👥 Perfil Socioeconômico:**")
                    classes_zona = [r.get('classe_social', 'N/A') for r in cluster_regioes]
                    classe_comum = Counter(classes_zona).most_common(1)[0]
                    st.write(f"• Classe predominante: **{classe_comum[0]}** ({classe_comum[1]} pontos)")
                    st.write(f"• Índice de classe: {classe_med:.1f}/5.0")
                
                with col_b:
                    st.markdown("**🏢 Tipos de Estabelecimentos:**")
                    tipos = [r.get('tipo_comercial', 'N/A') for r in cluster_regioes]
                    tipos_count = Counter(tipos).most_common(3)
                    for tipo, count in tipos_count:
                        st.write(f"• {tipo}: {count} locais")
                    
                    st.markdown("**💡 Recomendação:**")
                    if score > 2.5:
                        st.success("✅ **PRIORIDADE ALTA** - Iniciar operação imediatamente")
                    elif score > 1.5:
                        st.info("🔹 **PRIORIDADE MÉDIA** - Potencial moderado, avaliar concorrência")
                    else:
                        st.warning("⚠️ **PRIORIDADE BAIXA** - Considerar apenas após saturação das zonas prioritárias")
                
                # Botão para ver detalhes
                if st.button(f"📋 Ver lista completa de pontos", key=f"detalhes_{cluster_id}"):
                    st.markdown("**Pontos mapeados nesta zona:**")
                    for i, regiao in enumerate(cluster_regioes[:10], 1):
                        st.caption(f"{i}. {regiao.get('nome', 'N/A')} - Lat: {regiao.get('lat', 0):.4f}, Lon: {regiao.get('lon', 0):.4f}")
                    if len(cluster_regioes) > 10:
                        st.caption(f"... e mais {len(cluster_regioes) - 10} pontos")
        
        st.markdown("---")
        
        # === PRÓXIMOS PASSOS ===
        st.subheader("🚀 Plano de Ação Recomendado")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📅 Curto Prazo (1-2 semanas):**")
            st.write("1. Visitar Zona #1 para validação de campo")
            st.write("2. Mapear concorrentes diretos na região")
            st.write("3. Identificar parceiros estratégicos locais")
            st.write("4. Testar venda piloto em 3-5 pontos")
        
        with col2:
            st.markdown("**📈 Médio Prazo (1-2 meses):**")
            st.write("1. Expandir para Zona #2 se resultados positivos")
            st.write("2. Estabelecer parcerias com estabelecimentos")
            st.write("3. Ajustar estratégia baseado em feedback")
            st.write("4. Escalar operação nas zonas validadas")
        
        # Verifica POIs
        tem_pois = any("POIs próximos:" in r.get('motivo', '') for r in regioes)
        if not tem_pois:
            st.info("💡 **Dica:** Ative 'Enriquecer com Google Places API' na barra lateral para análise mais detalhada com pontos de interesse próximos.")






