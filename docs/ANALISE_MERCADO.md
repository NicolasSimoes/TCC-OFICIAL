# Análise de Mercado por Região — Documentação da Lógica

## Visão Geral

Após identificar as melhores regiões pelo pipeline de clustering, o sistema realiza uma
**análise de mercado local** para as top-5 regiões. Para cada região, são coletados dados
reais via **Google Places Nearby Search** num raio de 800 metros, calculando três métricas:
**Concorrentes**, **Sinergias** e **Âncoras**.

---

## 1. Concorrentes

### O que são
Estabelecimentos que oferecem o **mesmo produto ou serviço** que o negócio analisado.
Representam **ameaça direta** ao empreendedor — quanto mais, maior a disputa pelo
mesmo cliente na mesma área.

### Como é calculado
O sistema consulta o Google Places buscando os tipos de estabelecimento associados ao nicho:

| Nicho | Tipos buscados |
|-------|---------------|
| Fitness | gym |
| Infantil | clothing_store, store |
| Escolar | book_store, stationery_store |
| Alimentação | supermarket, grocery_or_supermarket |
| Farmácia | pharmacy, drugstore |
| Beleza | beauty_salon, hair_care |
| Pet | pet_store |
| Eletrônicos | electronics_store |
| Saúde | hospital, doctor |

A contagem retornada pelo Google Places (até 20 por busca) é somada para todos os tipos
do nicho num raio de **800 metros** do ponto central da região.

### Classificação de saturação

| Concorrentes encontrados | Nível de saturação |
|--------------------------|-------------------|
| 0 | Vazio — mercado inexplorado |
| 1 a 2 | Baixa — boa janela de entrada |
| 3 a 5 | Média — competição moderada |
| 6 ou mais | Alta — mercado saturado |

---

## 2. Sinergias

### O que são
Estabelecimentos que **atraem o mesmo perfil de cliente** do negócio, mas não competem
diretamente. A presença deles indica que o público-alvo já frequenta aquela área,
aumentando o potencial de vendas por fluxo orgânico.

### Como é calculado
Da mesma forma que os concorrentes: busca no Google Places por tipos complementares ao nicho.

| Nicho | Tipos sinérgicos |
|-------|-----------------|
| Fitness | park, stadium, health |
| Infantil | school, primary_school, park |
| Escolar | school, university, library |
| Alimentação | restaurant, cafe, bakery |
| Farmácia | hospital, doctor, dentist |
| Beleza | clothing_store, shopping_mall, spa |
| Pet | veterinary_care, park |
| Eletrônicos | shopping_mall, department_store |
| Saúde | pharmacy, physiotherapist |

### Interpretação
- `sinergias >= 3` → o insight menciona **"forte sinergia"** na região
- Quanto maior o número, mais o público do nicho já circula no local

---

## 3. Âncoras

### O que são
Equipamentos urbanos de **geração massiva de fluxo**, independentes do nicho.
Shoppings, supermercados, bancos e pontos de transporte público atraem um volume
alto e constante de pessoas todos os dias — beneficiando qualquer tipo de negócio
próximo a eles.

### Tipos buscados (universais para todos os nichos)

```
shopping_mall
supermarket
bank
subway_station
bus_station
```

### Interpretação
- `âncoras >= 2` → o insight menciona **"região com âncoras de tráfego"**
- Uma região com shopping + terminal de ônibus, por exemplo, tem fluxo garantido

---

## 4. Densidade Comercial

### O que é
Soma total das três métricas:

```
density = competitors + synergies + anchors
```

É um proxy da **movimentação comercial geral** da região — quanto maior, mais
ativa é a área, independente da saturação do nicho específico.

---

## 5. Insight Automático

O sistema combina os três números para gerar uma frase interpretativa por região.

**Lógica de construção:**

```
1. Base do insight = classificação de saturação (vazio / baixa / média / alta)
2. SE sinergias >= 3  → adiciona "forte sinergia (N negócios complementares)"
3. SE âncoras >= 2   → adiciona "região com âncoras de tráfego (N)"
```

**Exemplos de insight gerado:**

> "Apenas 1 concorrente próximo — boa janela de entrada; forte sinergia (4 negócios complementares); região com âncoras de tráfego (3)"

> "5 concorrentes próximos — competição moderada; região com âncoras de tráfego (2)"

> "Nenhum concorrente direto em 800m — possível mercado inexplorado"

---

## 6. Nomes dos Concorrentes

Quando a análise está ativa com Google Places, o sistema também retorna os **nomes reais**
dos primeiros concorrentes encontrados (via campo `name` da API). Eles aparecem como
chips/tags abaixo do insight na interface, permitindo identificar as marcas presentes.

Exemplo para nicho Fitness: `Smart Fit`, `Bio Ritmo`, `Bodytech`

---

## 7. Limitações

- O raio de 800m é fixo — pode não capturar concorrentes em avenidas adjacentes
- A API retorna no máximo 20 resultados por tipo (limitação do Google Places)
- Os dados refletem o cadastro do Google, que pode estar desatualizado
- A análise cobre apenas as **top-5 regiões** para economizar cota da API
- Sem a chave `GOOGLE_API_KEY` configurada no `.env`, esta seção não é exibida

---

## 8. Onde aparece na interface

Após rodar uma análise com o toggle **"Análise de mercado real (Google Places)"** ativado
no passo 3 do formulário, o componente **Análise de Mercado por Região** aparece
entre o mapa e a estratégia, exibindo:

- Badge de saturação colorido por região
- Cards com os três números (Concorrentes / Sinergias / Âncoras)
- Insight textual
- Chips com nomes dos concorrentes reais

---

*Módulo implementado em `src/market_analysis.py` — configurações em `src/config.py`*
