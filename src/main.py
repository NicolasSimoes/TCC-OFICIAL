from nlp import identificar_nicho, analisar_produto_completo
from map import gerar_mapa
from clustering_pipeline import gerar_regioes_ideais

def processar_requisicao(produto: str, filtros: dict):
    """
    Processa requisição completa do usuário.
    
    Args:
        produto: Nome/descrição do produto
        filtros: Dict com filtros aplicados
        
    Returns:
        Tuple (nicho, mapa_folium, regioes)
    """
    try:
        # Análise do produto
        print(f"\n{'='*50}")
        print(f"🎯 Processando: {produto}")
        print(f"{'='*50}")
        
        analise = analisar_produto_completo(produto)
        nicho = analise['nicho']
        
        print(f"✓ Nicho identificado: {nicho}")
        print(f"✓ POIs sugeridos: {analise['pois_sugeridos']}")
        
        # Gera regiões ideais com clustering (retorna lista de dicts)
        regioes = gerar_regioes_ideais(produto, filtros, nicho)
        
        # Gera mapa interativo com todas as informações
        # Passa lista completa de dicts para aproveitar score, cluster, etc.
        mapa = gerar_mapa(regioes, nicho=nicho, produto=produto)
        
        return nicho, mapa, regioes
        
    except Exception as e:
        print(f"❌ Erro em processar_requisicao: {str(e)}")
        import traceback
        traceback.print_exc()
        # Retorna valores padrão em caso de erro
        return "Erro", gerar_mapa([], nicho="Outro", produto=produto), []
