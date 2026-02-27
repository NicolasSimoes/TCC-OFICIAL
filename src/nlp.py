
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
from pathlib import Path

# Carrega .env da raiz do projeto usando caminho absoluto
dotenv_path = Path(r'c:/Users/nicol/Downloads/TCC-Project-dev nov/TCC-Project-dev/.env')
load_dotenv(dotenv_path=dotenv_path)


# Tenta importar OpenAI
try:
    from openai import OpenAI
    _openai_imported = True
except ImportError:
    _openai_imported = False

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_AVAILABLE = _openai_imported and bool(OPENAI_API_KEY)

def identificar_nicho(texto: str) -> str:
    """
    Identifica o nicho do produto usando análise de palavras-chave.
    Fallback para classificação básica caso OpenAI não esteja disponível.
    
    Args:
        texto: Descrição do produto
        
    Returns:
        Nome do nicho identificado
    """
    if not texto or not texto.strip():
        return "Outro"
    
    texto = texto.lower().strip()
    
    # Mapeamento de palavras-chave para nichos
    nichos = {
        "Fitness": [
            "whey", "creatina", "academia", "suplemento", "proteina", "protein",
            "bcaa", "pre treino", "pre-treino", "massa muscular", "musculacao",
            "musculação", "hipercalorico", "hipercalórico", "termogenico", 
            "termogênico", "shake", "barras de proteina", "barra proteica"
        ],
        "Infantil": [
            "fralda", "bebe", "bebê", "mamadeira", "lenco", "lenço", "chupeta",
            "papinha", "carrinho", "berco", "berço", "pediatrico", "pediátrico",
            "crianca", "criança", "recem nascido", "recém-nascido", "infantil"
        ],
        "Escolar": [
            "caderno", "caneta", "mochila", "escolar", "lapis", "lápis", "estojo",
            "livro", "material escolar", "fichario", "fichário", "apontador",
            "borracha", "regua", "régua", "tesoura", "cola", "canetinha"
        ],
        "Alimentação": [
            "comida", "alimento", "bebida", "lanche", "salgado", "doce", "chocolate",
            "biscoito", "bolacha", "refrigerante", "suco", "agua", "água", "cafe",
            "café", "cha", "chá", "snack", "mercearia", "organico", "orgânico"
        ],
        "Farmácia": [
            "remedio", "remédio", "medicamento", "farmacia", "farmácia", "vitamina",
            "antialergico", "antialérgico", "analgesico", "analgésico", "antibiotico",
            "antibiótico", "pomada", "xarope", "comprimido", "capsula", "cápsula"
        ],
        "Beleza": [
            "cosmetico", "cosmético", "maquiagem", "perfume", "creme", "shampoo",
            "condicionador", "sabonete", "hidratante", "protetor solar", "batom",
            "esmalte", "cabelo", "pele", "facial", "corporal", "higiene"
        ],
        "Pet": [
            "cachorro", "gato", "pet", "racao", "ração", "animal", "brinquedo pet",
            "coleira", "caminha", "areia gato", "petisco", "veterinario", "veterinário"
        ],
        "Eletrônicos": [
            "eletronico", "eletrônico", "celular", "smartphone", "tablet", "notebook",
            "fone", "carregador", "cabo", "power bank", "bateria", "tech", "gadget"
        ]
    }
    
    # Contagem de matches por nicho
    scores = {}
    for nicho, palavras in nichos.items():
        score = sum(1 for palavra in palavras if palavra in texto)
        if score > 0:
            scores[nicho] = score
    
    # Retorna o nicho com maior score
    if scores:
        return max(scores, key=scores.get)
    
    return "Outro"


def sugerir_pois_para_nicho(nicho: str) -> List[str]:
    """
    Sugere tipos de POIs relevantes baseado no nicho identificado.
    
    Args:
        nicho: Nome do nicho
        
    Returns:
        Lista de tipos de POI para buscar na API
    """
    pois_map = {
        "Fitness": ["gym", "health", "spa", "sporting_goods_store", "park"],
        "Infantil": ["school", "primary_school", "park", "childcare", "toy_store"],
        "Escolar": ["school", "university", "library", "book_store", "stationery"],
        "Alimentação": ["supermarket", "grocery_or_supermarket", "restaurant", "cafe", "bakery"],
        "Farmácia": ["pharmacy", "drugstore", "hospital", "doctor", "physiotherapist"],
        "Beleza": ["beauty_salon", "hair_care", "spa", "clothing_store", "department_store"],
        "Pet": ["pet_store", "veterinary_care", "park"],
        "Eletrônicos": ["electronics_store", "home_goods_store", "department_store"],
        "Outro": ["supermarket", "shopping_mall", "store"]
    }
    
    return pois_map.get(nicho, pois_map["Outro"])


def sugerir_pesos_classe(nicho: str) -> Dict[str, int]:
    """
    Sugere pesos dinâmicos por classe social baseado no nicho.
    
    Args:
        nicho: Nome do nicho
        
    Returns:
        Dicionário com pesos {classe: peso}
    """
    pesos_map = {
        "Fitness": {"A": 50000, "B": 30000, "C": 5000},      # Foco em classe alta
        "Infantil": {"A": 20000, "B": 20000, "C": 15000},    # Distribuído
        "Escolar": {"A": 15000, "B": 25000, "C": 20000},     # Foco em classe média
        "Alimentação": {"A": 20000, "B": 25000, "C": 25000}, # Equilibrado
        "Farmácia": {"A": 30000, "B": 30000, "C": 20000},    # Classes A/B
        "Beleza": {"A": 40000, "B": 25000, "C": 10000},      # Foco em classe alta
        "Pet": {"A": 45000, "B": 20000, "C": 5000},          # Forte em classe alta
        "Eletrônicos": {"A": 50000, "B": 25000, "C": 8000},  # Foco em classe alta
        "Outro": {"A": 30000, "B": 20000, "C": 10000}        # Padrão
    }
    
    return pesos_map.get(nicho, pesos_map["Outro"])


def gerar_estrategia_comercial(
    produto: str, 
    nicho: str, 
    regioes: List[tuple],
    pesos_classe: Dict[str, int],
    filtros: Dict = None
) -> str:
    """
    Gera estratégia comercial personalizada usando OpenAI GPT-4.
    
    Args:
        produto: Nome/descrição do produto
        nicho: Nicho identificado
        regioes: Lista de regiões ideais [(lat, lon, nome), ...]
        pesos_classe: Pesos por classe social
        filtros: Filtros aplicados pelo usuário
        
    Returns:
        Texto com estratégia comercial detalhada
    """
    if not _openai_imported:
        return _estrategia_fallback(produto, nicho, regioes, pesos_classe)

    api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _estrategia_fallback(produto, nicho, regioes, pesos_classe)

    try:
        client = OpenAI(api_key=api_key)

        # Prepara contexto
        classe_focal = max(pesos_classe, key=pesos_classe.get)
        # Compatível com lista de dicts (novo formato)
        top_regioes = [r.get('nome', str(r)) for r in regioes[:5]] if regioes else []

        filtros_texto = ""
        if filtros:
            if filtros.get("classe"):
                filtros_texto += f"\n- Classes sociais: {', '.join(filtros['classe'])}"
            if filtros.get("tipo"):
                filtros_texto += f"\n- Tipo de estabelecimento: {filtros['tipo']}"
            if filtros.get("bairro"):
                filtros_texto += f"\n- Bairros: {', '.join(filtros['bairro'])}"

        prompt = f"""Você é um consultor especialista em geomarketing e estratégia comercial para Fortaleza/CE.

Analise os dados abaixo e crie uma estratégia comercial DETALHADA e ACIONÁVEL:

PRODUTO: {produto}
NICHO: {nicho}
CLASSE FOCAL: {classe_focal} (maior potencial)
TOP 5 REGIÕES: {', '.join(top_regioes) if top_regioes else 'Nenhuma região identificada'}

FILTROS APLICADOS:{filtros_texto if filtros_texto else ' Nenhum'}

PESOS POR CLASSE:
{chr(10).join([f'- Classe {k}: {v:,}' for k, v in sorted(pesos_classe.items())])}

Forneça:
1. **Análise de Mercado**: Por que esse produto funciona nessas regiões?
2. **Público-Alvo**: Perfil demográfico e comportamental
3. **Estratégia de Posicionamento**: Como posicionar o produto
4. **Canais de Venda**: Onde e como vender (físico, online, parcerias)
5. **Precificação**: Sugestão de faixa de preço por classe social
6. **Ações Táticas**: 3-5 ações imediatas para começar
7. **Riscos e Mitigação**: Principais desafios e como superá-los

Seja específico para Fortaleza, use dados locais quando relevante, e dê exemplos práticos."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Mais econômico que gpt-4
            messages=[
                {"role": "system", "content": "Você é um especialista em geomarketing e estratégia comercial para o mercado de Fortaleza/CE."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"⚠️ Erro ao gerar estratégia com OpenAI: {str(e)}")
        return _estrategia_fallback(produto, nicho, regioes, pesos_classe)


def _estrategia_fallback(
    produto: str, 
    nicho: str, 
    regioes: List[tuple],
    pesos_classe: Dict[str, int]
) -> str:
    """Estratégia básica quando OpenAI não está disponível."""
    classe_focal = max(pesos_classe, key=pesos_classe.get)
    # Compatível com lista de dicts (novo formato)
    top_regioes = [r.get('nome', str(r)) for r in regioes[:3]] if regioes else []
    
    estrategias_por_nicho = {
        "Fitness": {
            "publico": "Praticantes de atividade física, frequentadores de academias",
            "canais": "Academias, lojas de suplementos, vendedores porta-a-porta",
            "preco": "Classe A/B: R$80-150, Classe C: R$50-80"
        },
        "Infantil": {
            "publico": "Pais e mães com crianças de 0-10 anos",
            "canais": "Farmácias, supermercados, lojas especializadas",
            "preco": "Classe A/B: R$30-80, Classe C: R$15-40"
        },
        "Escolar": {
            "publico": "Estudantes e pais, crianças e adolescentes",
            "canais": "Papelarias, supermercados, escolas (parcerias)",
            "preco": "Classe A/B: R$15-50, Classe C: R$5-25"
        },
        "Farmácia": {
            "publico": "Público geral com necessidades de saúde",
            "canais": "Farmácias, drogarias, delivery",
            "preco": "Variável conforme medicamento"
        },
        "Beleza": {
            "publico": "Mulheres 18-45 anos, público vaidoso",
            "canais": "Salões, perfumarias, lojas especializadas",
            "preco": "Classe A/B: R$50-200, Classe C: R$20-60"
        }
    }
    
    info = estrategias_por_nicho.get(nicho, {
        "publico": "Público geral",
        "canais": "Varejo tradicional",
        "preco": "Ajustar conforme concorrência"
    })
    
    return f"""## 📊 Estratégia Comercial - {produto}

### 🎯 Análise de Mercado
O produto **{produto}** foi classificado no nicho **{nicho}**, com maior potencial na **Classe {classe_focal}**.

**Regiões Prioritárias:**
{chr(10).join([f'- {r}' for r in top_regioes]) if top_regioes else '- Nenhuma região identificada com os filtros aplicados'}

### 👥 Público-Alvo
{info['publico']}

### 📍 Canais de Venda Recomendados
{info['canais']}

### 💰 Precificação Sugerida
{info['preco']}

### ⚡ Ações Táticas Imediatas
1. **Visitar as regiões prioritárias** e fazer pesquisa de campo
2. **Mapear concorrentes** nas áreas identificadas
3. **Testar vendas piloto** em {top_regioes[0] if top_regioes else 'região de alto potencial'}
4. **Estabelecer parcerias** com estabelecimentos locais
5. **Coletar feedback** e ajustar estratégia

### ⚠️ Considerações
- Esta análise foi gerada sem IA avançada. Para estratégia mais detalhada, configure a API da OpenAI.
- Sempre valide dados com pesquisa de campo antes de investir.

---
💡 **Dica:** Configure `OPENAI_API_KEY` no arquivo `.env` para estratégias mais detalhadas e personalizadas."""


def analisar_produto_completo(produto: str) -> Dict[str, any]:
    """
    Análise completa do produto retornando nicho, POIs e pesos sugeridos.
    
    Args:
        produto: Descrição do produto
        
    Returns:
        Dicionário com nicho, pois_sugeridos e pesos_classe
    """
    nicho = identificar_nicho(produto)
    pois = sugerir_pois_para_nicho(nicho)
    pesos = sugerir_pesos_classe(nicho)
    
    return {
        "nicho": nicho,
        "pois_sugeridos": pois,
        "pesos_classe": pesos,
        "descricao": f"Produto classificado como {nicho} com {len(pois)} tipos de POI relevantes"
    }


