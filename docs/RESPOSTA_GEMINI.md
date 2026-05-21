# Resposta do Gemini Deep Search — Validação Científica

> Documento gerado a partir de deep search no Gemini com base em
> [SINTESE_CIENTIFICA.md](SINTESE_CIENTIFICA.md). Serve como referência
> bibliográfica e justificativa metodológica para o TCC.

## Sumário das recomendações aplicadas

| # | Recomendação | Status | Onde |
|---|---|---|---|
| Q1 | Mapeamento de tipos Google Places v1 (9 nichos) | Pronto p/ Fase 2 | `NICHOS_PLACES_V1_MAPPING` em `src/config.py` |
| Q3 | Raio 800m (Calthorpe TOD 1993, "10-minute city") | ✅ Aplicado | `MARKET_ANALYSIS_RADIUS = 800` |
| Q8 | `transit_station` (substitui `subway_station`+`bus_station`) | ✅ Aplicado (Fase 1) | `ANCHOR_TYPES` em `src/config.py` |
| — | Saúde: adicionar `medical_clinic`, `medical_lab` (v1 only) | ⏳ Fase 2 | preparado em `NICHOS_PLACES_V1_MAPPING` |
| — | Alimentação: `fast_food_restaurant` (v1 only) + `bar`/`meal_takeaway` (Legacy) | ✅ parcial | Legacy aplicado; v1 preparado |

## Plano de migração para Places API v1 (Fase 2)

### Mudanças técnicas

1. **Endpoint**: `GET /maps/api/place/nearbysearch/json` → `POST /v1/places:searchNearby`
2. **Headers obrigatórios**:
   - `X-Goog-Api-Key: <chave>`
   - `X-Goog-FieldMask: places.id,places.displayName,places.types,places.rating,places.userRatingCount,places.businessStatus`
3. **Body JSON**:
   ```json
   {
     "includedTypes": ["pharmacy", "medical_clinic"],
     "maxResultCount": 20,
     "locationRestriction": {
       "circle": {
         "center": {"latitude": -3.7327, "longitude": -38.5267},
         "radius": 800
       }
     }
   }
   ```
4. **Limites v1**:
   - `maxResultCount` máximo = 20 (sem paginação via `next_page_token`)
   - Para >20 resultados: migrar para `searchByText` (POST `/v1/places:searchText`)
5. **Filtros recomendados pós-resposta**:
   - Excluir `businessStatus != "OPERATIONAL"` (limpa fechados/temporários)
   - Considerar `userRatingCount > 5` para evitar negócios sem tração

### Pricing (USD por 1000 requisições)

| SKU | Campos incluídos | Preço |
|---|---|---|
| Basic | id, displayName, types, businessStatus | $25 |
| Advanced (Pro) | + rating, userRatingCount, priceLevel | $28 |

### Arquivos a alterar (Fase 2)

- `src/clustering_pipeline.py` → `nearby_count()`, `nearby_names()` (POST + FieldMask)
- `src/market_analysis.py` → adaptar consumo de retornos
- `src/config.py` → trocar `PLACES_API_CONFIG.base_url` para v1

## Justificativas científicas-chave

- **Raio 800m**: Calthorpe (1993), TCRP Report 102 (2004), Cervero & Kockelman (1997).
  Distância caminhável de ~10 min, mediana de captação para varejo de bairro.
- **`transit_station`** (em vez de `subway_station`+`bus_station`): no contexto de
  Fortaleza, o sistema VLT/Metrofor + terminais integrados aparecem rotulados
  como `transit_station` no Google. Reduz subcontagem de âncoras.
- **`userRatingCount` como peso**: aproximação de fluxo (proxy de movimento real),
  conforme literatura de geomarketing baseada em POIs (Liu et al. 2017).
