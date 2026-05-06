
import os
import unicodedata
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from pathlib import Path

# Tenta importar scikit-learn para classificador real
try:
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import ComplementNB
    from sklearn.calibration import CalibratedClassifierCV
    _sklearn_available = True
except ImportError:
    _sklearn_available = False

# Carrega .env da raiz do projeto
dotenv_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path, override=True)

# Tenta importar OpenAI
try:
    from openai import OpenAI
    _openai_imported = True
except ImportError:
    _openai_imported = False

def get_openai_key():
    return os.getenv("OPENAI_API_KEY")

def is_openai_available():
    return _openai_imported and bool(get_openai_key())

OPENAI_API_KEY = get_openai_key()
OPENAI_AVAILABLE = is_openai_available()


# ---------------------------------------------------------------------------
# Dataset de treinamento para o classificador TF-IDF + Naive Bayes
# Cada entrada: (texto_exemplo, classe)
# Exemplos variados para cobrir vocabulário real do mercado brasileiro
# ---------------------------------------------------------------------------
_TRAINING_DATA: List[Tuple[str, str]] = [
    # Fitness
    ("whey protein concentrado", "Fitness"),
    ("creatina monohidratada 300g", "Fitness"),
    ("suplemento pré-treino c4", "Fitness"),
    ("bcaa aminoácidos essenciais", "Fitness"),
    ("hipercalórico massa muscular", "Fitness"),
    ("termogênico queima gordura", "Fitness"),
    ("barra proteica zero açúcar", "Fitness"),
    ("proteína isolada sem lactose", "Fitness"),
    ("academia musculação crossfit", "Fitness"),
    ("shake substituto de refeição", "Fitness"),
    ("coqueteleira academia treino", "Fitness"),
    ("luva musculação proteção", "Fitness"),
    ("suplemento vitamínico esportivo", "Fitness"),
    # Infantil
    ("fralda descartável recém nascido", "Infantil"),
    ("mamadeira anti cólica bebê", "Infantil"),
    ("chupeta ortodôntica silicone", "Infantil"),
    ("papinha nestlé frutas bebê", "Infantil"),
    ("carrinho passeio bebê conforto", "Infantil"),
    ("lenço umedecido fraldas", "Infantil"),
    ("berço grade madeira", "Infantil"),
    ("brinquedo educativo criança", "Infantil"),
    ("roupa bebê recém nascido", "Infantil"),
    ("babá eletrônica monitor", "Infantil"),
    ("pomada assaduras bebê", "Infantil"),
    ("cadeirinha carro infantil", "Infantil"),
    # Escolar
    ("caderno universitário 200 folhas", "Escolar"),
    ("caneta esferográfica azul", "Escolar"),
    ("mochila escolar reforçada", "Escolar"),
    ("estojo escolar material", "Escolar"),
    ("lápis grafite escolar caixa", "Escolar"),
    ("fichário com divisórias", "Escolar"),
    ("cola branca escolar 90g", "Escolar"),
    ("régua escolar 30cm", "Escolar"),
    ("calculadora científica estudante", "Escolar"),
    ("kit material escolar completo", "Escolar"),
    ("borracha lápis papelaria", "Escolar"),
    ("caneta hidrográfica colorida", "Escolar"),
    # Alimentação
    ("biscoito recheado chocolate", "Alimentação"),
    ("refrigerante guaraná 2 litros", "Alimentação"),
    ("suco de laranja natural", "Alimentação"),
    ("chocolate ao leite tablete", "Alimentação"),
    ("snack proteico salgado", "Alimentação"),
    ("café torrado moído", "Alimentação"),
    ("chá ervas misto", "Alimentação"),
    ("agua mineral sem gás", "Alimentação"),
    ("macarrão instantâneo sabor", "Alimentação"),
    ("granola orgânica aveia", "Alimentação"),
    ("lanche saudável barra cereal", "Alimentação"),
    ("comida congelada pratica", "Alimentação"),
    # Farmácia
    ("dipirona analgésico comprimido", "Farmácia"),
    ("ibuprofeno anti-inflamatório 600mg", "Farmácia"),
    ("vitamina c suplemento 1g", "Farmácia"),
    ("antibiótico amoxicilina", "Farmácia"),
    ("pomada cicatrizante", "Farmácia"),
    ("xarope tosse expectorante", "Farmácia"),
    ("anticoncepcional pílula", "Farmácia"),
    ("repelente mosquito spray", "Farmácia"),
    ("protetor solar fps 60", "Farmácia"),
    ("termômetro digital axilar", "Farmácia"),
    ("curativo band-aid caixa", "Farmácia"),
    ("soro fisiológico lavagem nasal", "Farmácia"),
    # Beleza
    ("shampoo hidratante cabelos secos", "Beleza"),
    ("condicionador reconstrutor fios", "Beleza"),
    ("creme hidratante corporal", "Beleza"),
    ("perfume importado masculino", "Beleza"),
    ("batom matte duradouro", "Beleza"),
    ("base líquida cobertura total", "Beleza"),
    ("esmalte unhas gel", "Beleza"),
    ("sabonete esfoliante pele", "Beleza"),
    ("máscara capilar nutrição", "Beleza"),
    ("sérum vitamina c facial", "Beleza"),
    ("maquiagem kit completo", "Beleza"),
    ("tinta cabelo coloração", "Beleza"),
    # Pet
    ("ração cachorro adulto 15kg", "Pet"),
    ("ração gato pelo curto", "Pet"),
    ("coleira antipulgas cachorro", "Pet"),
    ("petisco cão bifinho", "Pet"),
    ("brinquedo mordedor cachorro", "Pet"),
    ("areia higiênica gato 4kg", "Pet"),
    ("arranhador gato sisal", "Pet"),
    ("antipulgas gato cão", "Pet"),
    ("comedouro automático pet", "Pet"),
    ("shampoo banho cachorro", "Pet"),
    ("veterinário vacina pet", "Pet"),
    ("cama pet ortopédica", "Pet"),
    # Eletrônicos
    ("smartphone android 128gb", "Eletrônicos"),
    ("fone ouvido bluetooth sem fio", "Eletrônicos"),
    ("carregador rápido usb-c", "Eletrônicos"),
    ("notebook i5 8gb ssd", "Eletrônicos"),
    ("smartwatch monitor cardíaco", "Eletrônicos"),
    ("power bank 20000mah", "Eletrônicos"),
    ("cabo hdmi 2 metros", "Eletrônicos"),
    ("tablet android tela 10", "Eletrônicos"),
    ("caixinha bluetooth portátil", "Eletrônicos"),
    ("webcam full hd 1080p", "Eletrônicos"),
    ("teclado mecânico gamer", "Eletrônicos"),
    ("mouse sem fio ergonômico", "Eletrônicos"),
    # Saúde — serviços médicos e odontológicos
    ("clinica odontologica dentista consulta", "Saúde"),
    ("dentista implante ortodontia", "Saúde"),
    ("medico clinica geral saude", "Saúde"),
    ("hospital emergencia pronto socorro uti", "Saúde"),
    ("fisioterapia reabilitacao ortopedia", "Saúde"),
    ("laboratorio exame sangue diagnostico", "Saúde"),
    ("psicologo psiquiatra terapia mental", "Saúde"),
    ("nutricionista dieta reeducacao alimentar", "Saúde"),
    ("oftalmologista oculista visao olhos", "Saúde"),
    ("dermatologista pele acne tratamento", "Saúde"),
    ("pediatria crianca saude infantil medico", "Saúde"),
    ("plano saude convenio medico hospitalar", "Saúde"),
    ("estetica clinica botox harmonizacao facial", "Saúde"),
    ("vacina imunizacao posto saude", "Saúde"),
    ("cirurgia plastica estetica corporal", "Saúde"),
]


def _normalizar(texto: str) -> str:
    """Remove acentos e normaliza para o classificador."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii").lower()


# ---------------------------------------------------------------------------
# Constrói e treina o pipeline TF-IDF + ComplementNB uma única vez
# ComplementNB é superior ao MultinomialNB para classes desbalanceadas
# ---------------------------------------------------------------------------
def _build_classifier() -> Optional[object]:
    if not _sklearn_available:
        return None
    textos = [_normalizar(t) for t, _ in _TRAINING_DATA]
    labels = [l for _, l in _TRAINING_DATA]
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),   # unigrams + bigrams capturam "pre treino"
            min_df=1,
            sublinear_tf=True,    # log(tf) suaviza frequências altas
        )),
        ("clf", ComplementNB(alpha=0.3)),
    ])
    pipe.fit(textos, labels)
    return pipe


_CLASSIFIER = _build_classifier()
_CLASSIFIER_TRAINED = _CLASSIFIER is not None

if _CLASSIFIER_TRAINED:
    print("✓ Classificador NLP (TF-IDF + ComplementNB) treinado com sucesso")
else:
    print("⚠️  scikit-learn não disponível — usando fallback por keywords")


def identificar_nicho(texto: str) -> str:
    """
    Identifica o nicho do produto via pipeline TF-IDF + ComplementNB.

    O modelo é treinado na inicialização do módulo com um corpus curado
    de exemplos em português (ver _TRAINING_DATA). Para entradas fora do
    vocabulário treinado, a confiança cai e o fallback por keywords assume.

    Args:
        texto: Descrição do produto

    Returns:
        Nome do nicho identificado
    """
    if not texto or not texto.strip():
        return "Outro"

    if _CLASSIFIER_TRAINED:
        normalizado = _normalizar(texto)
        nicho_ml = _CLASSIFIER.predict([normalizado])[0]

        # Usa probabilidade para decidir se confia no modelo ou no fallback
        proba = _CLASSIFIER.predict_proba([normalizado])[0]
        confianca = float(max(proba))

        if confianca >= 0.35:
            return nicho_ml

    # Fallback por keywords (usado quando confiança < 35%)
    return _identificar_nicho_keywords(texto)


def identificar_nicho_com_confianca(texto: str) -> Dict:
    """
    Retorna o nicho identificado junto com métricas do classificador.
    Útil para a API e para transparência acadêmica.

    Returns:
        {nicho, confianca, metodo, probabilidades}
    """
    if not texto or not texto.strip():
        return {"nicho": "Outro", "confianca": 0.0, "metodo": "fallback", "probabilidades": {}}

    if _CLASSIFIER_TRAINED:
        normalizado = _normalizar(texto)
        nicho_ml = _CLASSIFIER.predict([normalizado])[0]
        proba = _CLASSIFIER.predict_proba([normalizado])[0]
        classes = _CLASSIFIER.classes_
        confianca = float(max(proba))
        prob_dict = {c: round(float(p), 4) for c, p in zip(classes, proba)}

        if confianca >= 0.35:
            return {
                "nicho": nicho_ml,
                "confianca": round(confianca, 4),
                "metodo": "TF-IDF + ComplementNB",
                "probabilidades": prob_dict,
            }

    nicho_kw = _identificar_nicho_keywords(texto)
    return {
        "nicho": nicho_kw,
        "confianca": 1.0,
        "metodo": "keyword-matching (fallback)",
        "probabilidades": {},
    }


def _identificar_nicho_keywords(texto: str) -> str:
    """Classificação por keywords — fallback quando confiança do ML é baixa."""
    texto = texto.lower().strip()
    nichos = {
        "Fitness": [
            "whey", "creatina", "academia", "suplemento", "proteina", "protein",
            "bcaa", "pre treino", "pre-treino", "massa muscular", "musculacao",
            "musculação", "hipercalorico", "hipercalórico", "termogenico",
            "termogênico", "shake", "barras de proteina", "barra proteica",
        ],
        "Infantil": [
            "fralda", "bebe", "bebê", "mamadeira", "lenco", "lenço", "chupeta",
            "papinha", "carrinho", "berco", "berço", "pediatrico", "pediátrico",
            "crianca", "criança", "recem nascido", "recém-nascido", "infantil",
        ],
        "Escolar": [
            "caderno", "caneta", "mochila", "escolar", "lapis", "lápis", "estojo",
            "livro", "material escolar", "fichario", "fichário", "apontador",
            "borracha", "regua", "régua", "tesoura", "cola", "canetinha",
        ],
        "Alimentação": [
            "comida", "alimento", "bebida", "lanche", "salgado", "doce", "chocolate",
            "biscoito", "bolacha", "refrigerante", "suco", "agua", "água", "cafe",
            "café", "cha", "chá", "snack", "mercearia", "organico", "orgânico",
        ],
        "Farmácia": [
            "remedio", "remédio", "medicamento", "farmacia", "farmácia", "vitamina",
            "antialergico", "antialérgico", "analgesico", "analgésico", "antibiotico",
            "antibiótico", "pomada", "xarope", "comprimido", "capsula", "cápsula",
        ],
        "Beleza": [
            "cosmetico", "cosmético", "maquiagem", "perfume", "creme", "shampoo",
            "condicionador", "sabonete", "hidratante", "protetor solar", "batom",
            "esmalte", "cabelo", "pele", "facial", "corporal", "higiene",
        ],
        "Pet": [
            "cachorro", "gato", "pet", "racao", "ração", "animal", "brinquedo pet",
            "coleira", "caminha", "areia gato", "petisco", "veterinario", "veterinário",
        ],
        "Eletrônicos": [
            "eletronico", "eletrônico", "celular", "smartphone", "tablet", "notebook",
            "fone", "carregador", "cabo", "power bank", "bateria", "tech", "gadget",
        ],
        "Saúde": [
            "clinica", "clínica", "medico", "médico", "dentista", "odontolog",
            "fisioterapia", "hospital", "saude", "saúde", "consulta", "exame",
            "laboratorio", "laboratório", "psicologo", "psicólogo", "nutricionista",
            "oftalmologista", "ortopedia", "pediatria", "cardiologista",
            "dermatolog", "estetica", "estética", "vacina", "cirurgia", "terapia",
        ],
    }
    # Match parcial para capturar variações (odontológica, médico, etc.)
    scores = {n: sum(1 for p in ps if p in texto or any(p in w for w in texto.split())) for n, ps in nichos.items()}
    scores = {n: s for n, s in scores.items() if s > 0}
    return max(scores, key=scores.get) if scores else "Outro"


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
        "Outro": ["supermarket", "shopping_mall", "store"],
        "Saúde": ["hospital", "doctor", "health", "pharmacy", "dentist"],
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
        "Outro": {"A": 30000, "B": 20000, "C": 10000},  # Padrão
        "Saúde": {"A": 45000, "B": 30000, "C": 10000},   # Serviços premium: foco em A/B
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
        print("⚠️ OpenAI não importado")
        return _estrategia_fallback(produto, nicho, regioes, pesos_classe)

    api_key = get_openai_key()
    if not api_key:
        print("⚠️ OPENAI_API_KEY não encontrada")
        return _estrategia_fallback(produto, nicho, regioes, pesos_classe)
    
    print(f"✓ OpenAI disponível, gerando estratégia com IA...")

    try:
        client = OpenAI(api_key=api_key)

        # Prepara contexto
        classe_focal = max(pesos_classe, key=pesos_classe.get)
        # Aceita tanto dicts (formato novo) quanto tuplas (formato legado)
        top_regioes = [_nome_regiao(r) for r in regioes[:5]] if regioes else []

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


def _nome_regiao(r) -> str:
    """Extrai o nome de uma região aceitando tanto dict quanto tupla (lat, lon, nome)."""
    if isinstance(r, dict):
        return r.get("nome", str(r))
    if isinstance(r, (list, tuple)):
        # Formato legado: (lat, lon, nome) ou (lat, lon)
        if len(r) >= 3:
            return str(r[2])
        return str(r)
    return str(r)


def _estrategia_fallback(
    produto: str, 
    nicho: str, 
    regioes: List[tuple],
    pesos_classe: Dict[str, int]
) -> str:
    """Estratégia básica quando OpenAI não está disponível."""
    classe_focal = max(pesos_classe, key=pesos_classe.get)
    # Aceita tanto dicts (formato novo) quanto tuplas (formato legado)
    top_regioes = [_nome_regiao(r) for r in regioes[:3]] if regioes else []
    
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
        "Saúde": {
            "publico": "Adultos e famílias buscando serviços médicos e odontológicos de qualidade",
            "canais": "Clínicas, hospitais, indicações médicas, planos de saúde, redes sociais",
            "preco": "Classe A/B: R$200-1.000 por consulta/procedimento, Classe C: R$80-250"
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


