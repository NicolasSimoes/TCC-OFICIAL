# 🚀 Guia de Início Rápido - Smart Sale Fortaleza

## ⚡ Setup em 5 Minutos

### 1️⃣ Instale as Dependências

```powershell
# No diretório do projeto
pip install -r requirements.txt
```

### 2️⃣ Configure a API Key

```powershell
# Copie o template
Copy-Item .env.example .env

# Edite o arquivo .env e adicione sua chave Google
# notepad .env
```

No arquivo `.env`, substitua:
```env
GOOGLE_API_KEY=sua_chave_real_aqui
```

**Como obter a chave:**
1. Acesse https://console.cloud.google.com/
2. Crie/selecione projeto
3. Ative "Places API"
4. Crie credencial (API Key)
5. Copie e cole no `.env`

### 3️⃣ Verifique a Instalação

```powershell
python check_setup.py
```

Deve mostrar:
```
✅ OK       Python Version
✅ OK       Dependências
✅ OK       Arquivo .env
...
Resultado: 7/7 verificações passaram
```

### 4️⃣ Execute a Aplicação

```powershell
streamlit run src/interface.py
```

Abrirá automaticamente em: **http://localhost:8501**

---

## 📱 Usando a Interface

### Passo 1: Digite o Produto
Digite na caixa de busca, ex:
- "whey protein"
- "fraldas pampers"
- "caderno universitário"

### Passo 2: Configure Filtros (Opcional)
Na sidebar esquerda:
- **Classe Social:** A, B, C, D, E
- **Tipo Comercial:** Pequenos Regionais, Super Regionais, etc.
- **Bairros:** Aldeota, Meireles, Centro...

### Passo 3: Enviar
Clique no botão **"Send"** ➡️

### Passo 4: Visualizar Resultados
Você verá:
- ✅ Nicho identificado
- 📊 Métricas (POIs, Classe Focal)
- 🗺️ Mapa interativo com regiões ideais

---

## 🔧 Solução de Problemas Comuns

### ❌ "GOOGLE_API_KEY não encontrada"
**Solução:** Configure o arquivo `.env` corretamente

### ❌ "Nenhum arquivo de dados encontrado"
**Solução:** Certifique-se de ter `data/Projeto.xlsx` ou `data/clientes.csv`

### ❌ Erro ao importar módulos
**Solução:** Reinstale dependências
```powershell
pip install -r requirements.txt --force-reinstall
```

### ❌ "Port 8501 already in use"
**Solução:** Mate processo anterior ou use porta diferente
```powershell
streamlit run src/interface.py --server.port 8502
```

### ❌ Mapa não aparece
**Solução:** 
1. Verifique se há dados válidos após filtros
2. Verifique console do navegador (F12)
3. Limpe cache do Streamlit: `Ctrl + R`

---

## 📊 Exemplos de Uso

### Exemplo 1: Whey Protein (Fitness)
```
Produto: "whey protein isolado"
Filtros:
  - Classe: A, B
  - Bairros: Aldeota, Meireles, Papicu
  
Resultado:
  - Nicho: Fitness
  - Foco: Academias, áreas nobres
  - Top 3 regiões exibidas
```

### Exemplo 2: Fraldas (Infantil)
```
Produto: "fraldas descartáveis"
Filtros:
  - Classe: B, C
  - Tipo: Super Regionais
  
Resultado:
  - Nicho: Infantil
  - Foco: Escolas, supermercados
  - Distribuição equilibrada
```

### Exemplo 3: Material Escolar
```
Produto: "caderno universitário"
Filtros:
  - Bairros: Centro, Benfica, Montese
  
Resultado:
  - Nicho: Escolar
  - Foco: Universidades, bibliotecas
  - Regiões próximas a instituições de ensino
```

---

## 🎯 Dicas de Uso

### Para Melhores Resultados:

1. **Seja específico** no nome do produto
   - ✅ "proteína whey isolada"
   - ❌ "produto"

2. **Use filtros estrategicamente**
   - Classe A/B para produtos premium
   - Classe C para produtos populares
   - Sem filtros = análise geral

3. **Combine bairros relevantes**
   - Comerciais: Centro, Aldeota
   - Residenciais: Messejana, Montese

4. **Interprete o mapa**
   - Marcadores verdes = alta prioridade
   - Concentração de pontos = cluster forte
   - HeatMap = densidade por classe

### Atalhos:

- `Ctrl + R` - Recarregar app
- `Ctrl + Shift + R` - Limpar cache
- `F11` - Tela cheia

---

## 📈 Modo Avançado (CLI)

Para análises em lote ou automação:

```powershell
# Com enriquecimento de POIs (usa API)
python src/clustering_pipeline.py `
    --input data/clientes.csv `
    --usar_api true `
    --n_clusters 5 `
    --out_prefix analise_completa

# Apenas clustering (sem API)
python src/clustering_pipeline.py `
    --input data/clientes_enriquecidos.csv `
    --usar_api false `
    --n_clusters 3
```

### Saídas Geradas:
- `{prefix}_enriquecidos.csv` - Dados + POIs
- `{prefix}_clusterizados.csv` - Dados + clusters
- `{prefix}_mapa_clusters.html` - Mapa HTML

---

## 🆘 Precisa de Ajuda?

1. Execute `python check_setup.py`
2. Verifique os logs no terminal
3. Consulte o [README.md](README.md) completo
4. Veja o [CHANGELOG.md](CHANGELOG.md) para novidades

---

**💡 Primeira vez? Execute:**
```powershell
python check_setup.py
```

**🎉 Tudo OK? Inicie:**
```powershell
streamlit run src/interface.py
```
