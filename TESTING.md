# 🧪 Guia de Testes - Smart Sale Fortaleza

Este documento descreve a estrutura de testes unitários e de integração do projeto.

## 📂 Estrutura de Testes

```
tests/
├── __init__.py              # Inicialização do pacote
├── test_nlp.py              # Testes do módulo NLP
├── test_data_loader.py      # Testes do carregador de dados
├── test_map.py              # Testes de geração de mapas
├── test_integration.py      # Testes de integração
└── run_tests.py             # Script para rodar todos os testes
```

## 🚀 Executando os Testes

### Opção 1: Usando unittest (nativo)

```bash
# Rodar todos os testes
python tests/run_tests.py

# Rodar teste específico
python -m unittest tests.test_nlp

# Rodar classe específica
python -m unittest tests.test_nlp.TestIdentificarNicho

# Rodar teste único
python -m unittest tests.test_nlp.TestIdentificarNicho.test_nicho_fitness
```

### Opção 2: Usando pytest (recomendado)

```bash
# Instalar pytest
pip install pytest pytest-cov

# Rodar todos os testes
pytest

# Rodar com verbosidade
pytest -v

# Rodar teste específico
pytest tests/test_nlp.py

# Rodar com cobertura
pytest --cov=src --cov-report=html

# Rodar apenas testes rápidos (pular lentos)
pytest -m "not slow"
```

### Opção 3: PowerShell

```powershell
# Rodar todos os testes
cd "c:\Users\nicol\Downloads\TCC-Project-dev nov\TCC-Project-dev"
python -m pytest tests/ -v

# Com cobertura
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## 📊 Cobertura de Testes

Para gerar relatório de cobertura:

```bash
# Gerar cobertura e relatório HTML
pytest --cov=src --cov-report=html

# Abrir relatório no navegador
# O relatório estará em htmlcov/index.html
```

## 🧪 Tipos de Testes

### 1. Testes Unitários

#### `test_nlp.py` - Análise de Produto
- ✅ Identificação de nichos (8+ nichos)
- ✅ Sugestão de POIs por nicho
- ✅ Cálculo de pesos por classe social
- ✅ Análise completa de produto
- ✅ Geração de estratégia comercial
- ✅ Fallback quando OpenAI não disponível
- ✅ Mock de chamadas OpenAI

**Casos testados:**
- Fitness: whey, creatina, suplementos
- Infantil: fraldas, mamadeiras
- Escolar: cadernos, mochilas
- Alimentação: biscoitos, refrigerantes
- Farmácia: remédios, vitaminas
- Beleza: shampoo, perfumes
- Pet: ração, coleiras
- Eletrônicos: celulares, fones

#### `test_data_loader.py` - Carregamento de Dados
- ✅ Normalização de cabeçalhos
- ✅ Mapeamento de colunas
- ✅ Validação de colunas obrigatórias
- ✅ Limpeza de coordenadas
- ✅ Correção de coordenadas × 1.000.000
- ✅ Normalização de classe social
- ✅ Pipeline completo de limpeza

#### `test_map.py` - Geração de Mapas
- ✅ Geração de mapa com regiões
- ✅ Mapa vazio (fallback)
- ✅ Cálculo de centro baseado em regiões
- ✅ Tratamento de diferentes tipos de coordenadas

### 2. Testes de Integração

#### `test_integration.py`
- ✅ Fluxo completo: análise → estratégia → mapa
- ✅ Diferentes nichos end-to-end
- ✅ Aplicação de filtros
- ✅ Cenários sem regiões
- ✅ Consistência entre módulos

## 📈 Estatísticas de Cobertura

| Módulo | Cobertura Esperada | Descrição |
|--------|-------------------|-----------|
| `nlp.py` | > 90% | Análise de produto e NLP |
| `data_loader.py` | > 95% | Carregamento e limpeza |
| `map.py` | > 85% | Visualização de mapas |
| `main.py` | > 80% | Orquestração |

## 🔍 Exemplos de Testes

### Teste Simples
```python
def test_nicho_fitness(self):
    """Testa identificação de produtos fitness"""
    self.assertEqual(identificar_nicho("whey protein"), "Fitness")
```

### Teste com Mock
```python
@patch('nlp.OpenAI')
def test_estrategia_com_openai_mock(self, mock_openai):
    """Testa geração com OpenAI mockada"""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Estratégia IA"
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client
    
    estrategia = gerar_estrategia_comercial(...)
    self.assertEqual(estrategia, "Estratégia IA")
```

### Teste de Integração
```python
def test_fluxo_completo(self):
    """Testa fluxo end-to-end"""
    analise = analisar_produto_completo("whey protein")
    regioes = [(-3.7319, -38.5267, "Aldeota")]
    mapa = gerar_mapa(regioes)
    estrategia = gerar_estrategia_comercial(...)
    
    self.assertIsInstance(mapa, folium.Map)
    self.assertGreater(len(estrategia), 100)
```

## 🐛 Debugging de Testes

### Rodar teste específico com debug
```bash
pytest tests/test_nlp.py::TestIdentificarNicho::test_nicho_fitness -v -s
```

### Ver print statements
```bash
pytest -s  # Não captura stdout
```

### Parar no primeiro erro
```bash
pytest -x
```

### Ver traceback completo
```bash
pytest --tb=long
```

## ✅ Checklist de Testes

Antes de fazer commit/push:

- [ ] Todos os testes passam (`pytest`)
- [ ] Cobertura > 80% (`pytest --cov`)
- [ ] Sem warnings (`pytest --disable-warnings`)
- [ ] Testes de integração passam
- [ ] Mock de APIs externas funcionando

## 🔄 CI/CD

Para integração contínua, adicione ao GitHub Actions:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.8
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 📚 Recursos

- [Documentação pytest](https://docs.pytest.org/)
- [unittest Python](https://docs.python.org/3/library/unittest.html)
- [Coverage.py](https://coverage.readthedocs.io/)

---

💡 **Dica:** Execute os testes regularmente durante o desenvolvimento para detectar bugs cedo!
