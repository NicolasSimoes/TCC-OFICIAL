# Síntese Técnica para Validação Científica — Smart Sale Fortaleza

> **Objetivo deste documento:** servir como base de consulta para uma pesquisa profunda
> (deep search) na **documentação oficial da Google Places API**, validando
> cientificamente os parâmetros, tipos de POI e thresholds adotados pelo módulo de
> análise de mercado do TCC.

---

## 1. Contexto do Projeto

**Smart Sale Fortaleza** é um sistema de geomarketing que recomenda regiões de Fortaleza/CE
para venda de produtos. O pipeline combina:

1. **NLP (TF-IDF + ComplementNB)** — classifica o produto em 1 de 9 nichos
2. **Clustering (KMeans vs DBSCAN)** — agrupa pontos da base local por similaridade
3. **Google Places Nearby Search** — enriquece com POIs reais ao redor de cada ponto
4. **Análise de mercado por região** — calcula Concorrentes, Sinergias e Âncoras nas top-5

A **análise de mercado** é o foco deste documento. Ela responde:
- Existem concorrentes diretos próximos?
- O público-alvo já circula nessa área?
- Há geradores de tráfego (shopping, supermercado, transporte)?

---

## 2. Hipóteses de Marketing que Fundamentam a Lógica

| Hipótese | Fundamento teórico | Como o sistema mede |
|----------|-------------------|---------------------|
| **H1.** Concorrentes próximos disputam o mesmo cliente | Modelo de Hotelling (1929) — competição espacial | Conta estabelecimentos do mesmo tipo num raio |
| **H2.** Negócios complementares atraem o mesmo público | Teoria de aglomeração comercial (Porter, 1998) | Conta tipos correlacionados ao nicho |
| **H3.** Âncoras geram tráfego pedestre | Anchor store theory (Eppli & Benjamin, 1994) | Conta shoppings, supermercados, transporte |
| **H4.** Acessibilidade pedestre = ~800m | "5-minute walk" / 15-minute city (Moreno, 2020) | Raio fixo de 800m no Nearby Search |

---

## 3. Parâmetros Adotados e Justificativa

### 3.1 Raio de busca: **800 metros**

| Justificativa | Fonte |
|--------------|-------|
| Distância média percorrível a pé em ~10min (4,8 km/h) | Walkability index — TRB (2000) |
| Equivalente a uma "vizinhança de bairro" | NACTO Urban Design |
| Suficiente para capturar densidade comercial sem extrapolar zona de influência | Heurística empírica |

**🔍 A validar com Gemini:**
- Qual o **raio máximo** aceito pelo endpoint `nearbysearch`? (atualmente: 50.000m)
- Qual o **raio mínimo** prático para densidade comercial urbana?
- Existe documentação Google recomendando faixas por tipo de POI?

### 3.2 Top-5 regiões analisadas (não todas)

| Justificativa | Detalhe |
|--------------|--------|
| Economia de cota da API | Cada região = ~3 buscas × 5 tipos = ~15 requests |
| Foco nos melhores clusters | Já ranqueados pelo `score_potencial` do KMeans |
| 5 = trade-off custo/benefício | Suficiente para decisão estratégica |

**🔍 A validar:**
- Cota gratuita atual da Places API (limite por dia/mês)
- Custo por request do Nearby Search (Standard vs Atmosphere)

### 3.3 Classificação de saturação

| Concorrentes | Classe | Racional |
|--------------|--------|----------|
| 0 | vazio | Mercado virgem (oportunidade ou demanda inexistente) |
| 1–2 | baixa | Boa janela de entrada |
| 3–5 | média | Mercado consolidado, ainda comporta entrada |
| 6+ | alta | Risco de canibalização |

**🔍 A validar:**
- Existem estudos empíricos sobre densidade ótima de concorrentes por nicho?
- Há literatura sobre saturação de mercado em raios pedestres?

---

## 4. Tipos de POI Buscados (Google Places types)

### 4.1 Concorrentes diretos por nicho

| Nicho | Tipos `places.types` |
|-------|---------------------|
| Fitness | `gym` |
| Infantil | `clothing_store`, `store` |
| Escolar | `book_store`, `stationery_store` |
| Alimentação | `supermarket`, `grocery_or_supermarket` |
| Farmácia | `pharmacy`, `drugstore` |
| Beleza | `beauty_salon`, `hair_care` |
| Pet | `pet_store` |
| Eletrônicos | `electronics_store` |
| Saúde | `hospital`, `doctor` |

**🔍 A validar com Gemini:**
- Esses tipos ainda são suportados na **Places API (New) v1**?
- A versão nova usa `includedTypes` em vez de `type` — quais mudanças?
- Há tipos novos/mais específicos (ex: `fitness_center` vs `gym`)?
- O tipo `grocery_or_supermarket` foi **deprecado** em algum momento?

### 4.2 Sinergias por nicho

| Nicho | Tipos sinérgicos |
|-------|-----------------|
| Fitness | `park`, `stadium`, `health` |
| Infantil | `school`, `primary_school`, `park` |
| Escolar | `school`, `university`, `library` |
| Alimentação | `restaurant`, `cafe`, `bakery` |
| Farmácia | `hospital`, `doctor`, `dentist` |
| Beleza | `clothing_store`, `shopping_mall`, `spa` |
| Pet | `veterinary_care`, `park` |
| Eletrônicos | `shopping_mall`, `department_store` |
| Saúde | `pharmacy`, `physiotherapist` |

**🔍 A validar:**
- O tipo `health` ainda é uma categoria genérica válida?
- `physiotherapist` é tipo oficial ou subcategoria?

### 4.3 Âncoras universais (geradores de fluxo)

```
shopping_mall
supermarket
bank
subway_station
bus_station
```

**🔍 A validar:**
- Fortaleza tem `subway_station` ou apenas `light_rail_station` (metrô de superfície)?
- `transit_station` cobre todos os modais?
- Há `train_station` ou outros relevantes para a realidade local?

---

## 5. Algoritmo de Contagem

Pseudocódigo do cálculo:

```python
def analyze_region_market(lat, lon, nicho, radius=800):
    competitors = sum(count_places(lat, lon, t, radius)
                      for t in COMPETITOR_TYPES_BY_NICHE[nicho])
    synergies   = sum(count_places(lat, lon, t, radius)
                      for t in SYNERGY_TYPES_BY_NICHE[nicho])
    anchors     = sum(count_places(lat, lon, t, radius)
                      for t in ANCHOR_TYPES)
    density     = competitors + synergies + anchors
    saturacao   = classify(competitors)
    return { competitors, synergies, anchors, density, saturacao }
```

A função `count_places` chama:

```
GET https://maps.googleapis.com/maps/api/place/nearbysearch/json
    ?location={lat},{lon}
    &radius={radius}
    &type={place_type}
    &key={GOOGLE_API_KEY}
```

E conta `len(data["results"])` — **limitado a 20 resultados por página** (sem paginação ativada).

**🔍 A validar com Gemini:**
- A v1 retorna mais que 20 resultados sem `next_page_token`?
- Vale a pena habilitar paginação (3 páginas = até 60 resultados)?
- Há diferença entre **Nearby Search** (legado) e **searchNearby** (v1)?
- Em quais cenários **Text Search** seria mais preciso que Nearby?
- Os novos campos `priceLevel`, `userRatingCount`, `rating` da v1 poderiam refinar a métrica de concorrentes (ex: ponderar por qualidade)?

---

## 6. Cache Local

O sistema armazena cada consulta no arquivo `cache/cache_places.parquet` com:

```
{ h: md5(lat|lon|type|radius), lat, lon, type, radius, count, ts }
```

- **TTL configurável** (padrão: 30 dias)
- Evita re-cobrança em buscas repetidas

**🔍 A validar:**
- Termos de uso da Places API permitem armazenamento de `count`? (não armazena `place_id` nem `name`, apenas contagem agregada)
- Há restrição de tempo de cache nos ToS?

---

## 7. Limitações Conhecidas

1. **Raio fixo (800m)** — pode não capturar concorrentes em avenidas adjacentes
2. **20 resultados por busca** — subestima densidade em áreas muito comerciais
3. **Cadastro Google desatualizado** — POIs fechados ainda aparecem
4. **Apenas top-5 regiões** — análise não é exaustiva
5. **Sem ponderação por qualidade** — academia 5-estrelas conta igual a 2-estrelas

---

## 8. Perguntas-Chave para a Pesquisa no Gemini

Use estas perguntas como roteiro de validação:

1. ✅ **Migração Places API v1**: Os endpoints `nearbysearch` (legacy) ainda funcionam? Qual a data de descontinuação anunciada?
2. ✅ **Tipos suportados**: Comparar nossa lista com a tabela oficial atual de `Place.types`. Quais foram deprecados? Quais foram adicionados?
3. ✅ **Raio**: Há recomendação oficial Google para raio em análise urbana? Default vs máximo?
4. ✅ **Paginação**: Custo e benefício de habilitar `next_page_token` (até 60 resultados).
5. ✅ **Cota**: Limite gratuito atual do Nearby Search? Custo por 1.000 requests?
6. ✅ **Cache**: O que os ToS dizem sobre armazenamento de contagens agregadas?
7. ✅ **Campos novos da v1**: `priceLevel`, `rating`, `userRatingCount`, `businessStatus` — quais agregariam valor analítico?
8. ✅ **Transporte público**: `subway_station`, `bus_station`, `transit_station`, `light_rail_station` — qual usar para Fortaleza?
9. ✅ **Nicho saúde**: `hospital` e `doctor` são bons proxies de concorrência para "clínicas/farmácias"? Há tipos mais específicos?
10. ✅ **Densidade comercial**: Existe métrica oficial Google (ex: Popular Times) que poderia substituir ou complementar nossa contagem?

---

## 9. Saída Esperada da Pesquisa

Após o deep search, gerar:

- [ ] **Tabela comparativa**: parâmetros atuais × recomendações Google × literatura
- [ ] **Lista de tipos** atualizada para Places API (New) v1
- [ ] **Justificativa científica** para o raio de 800m com referências
- [ ] **Plano de migração** caso a API legacy seja descontinuada
- [ ] **Sugestões de novos campos** a incorporar (rating, priceLevel)
- [ ] **Validação de saturação** com estudos empíricos de varejo

---

*Documento gerado em maio/2026 — Nicolas Simões — TCC Bacharelado em Ciência da Computação*
*Módulo de referência: `src/market_analysis.py`, `src/config.py`*
