"""
Análise de mercado por região via Google Places API.

Para cada região (lat, lon) calcula 4 métricas usando os POIs ao redor:
- competitors: concorrentes diretos do nicho
- synergies: negócios complementares que atraem o mesmo público
- anchors: âncoras de tráfego (shoppings, supermercados, transporte)
- density: densidade comercial geral (proxy de fluxo)

E deriva insights interpretáveis (saturação, oportunidade, sinergia).

Reutiliza o cache parquet de Places do clustering_pipeline para evitar
chamadas redundantes à API.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd
import requests

from config import (
    ANCHOR_TYPES,
    COMPETITOR_TYPES_BY_NICHE,
    MARKET_ANALYSIS_RADIUS,
    MARKET_ANALYSIS_TOP_N,
    SYNERGY_TYPES_BY_NICHE,
)


def _count_types(
    lat: float,
    lon: float,
    types: List[str],
    radius: int,
    cache_df: pd.DataFrame,
    session: requests.Session,
    nearby_count_fn,
    hkey_fn,
    cache_records: List[dict],
) -> int:
    """Soma POIs de uma lista de tipos, usando cache + API quando preciso."""
    import time as _t

    total = 0
    for tp in types:
        hk = hkey_fn(lat, lon, tp, radius)
        cached = cache_df.loc[cache_df["h"] == hk]
        if not cached.empty:
            total += int(cached.iloc[0]["count"])
            continue

        cnt = nearby_count_fn(lat, lon, tp, radius, session)
        total += int(cnt)
        cache_records.append({
            "h": hk,
            "lat": lat,
            "lon": lon,
            "type": tp,
            "radius": radius,
            "count": int(cnt),
            "ts": int(_t.time()),
        })
    return total


def _get_names(
    lat: float,
    lon: float,
    types: list,
    radius: int,
    session,
    nearby_names_fn,
    max_total: int = 5,
) -> list:
    """Busca nomes de estabelecimentos para o primeiro tipo da lista."""
    if not nearby_names_fn or not types:
        return []
    try:
        return nearby_names_fn(lat, lon, types[0], radius, session, max_total)
    except Exception:
        return []


def _classify_saturation(competitors: int) -> str:
    """Classifica nível de saturação a partir do nº de concorrentes."""
    if competitors == 0:
        return "vazio"
    if competitors <= 2:
        return "baixa"
    if competitors <= 5:
        return "media"
    return "alta"


def _build_insight(competitors: int, synergies: int, anchors: int, saturacao: str) -> str:
    """Monta uma frase curta interpretando os números."""
    if saturacao == "vazio":
        base = f"Nenhum concorrente direto em {MARKET_ANALYSIS_RADIUS}m — possível mercado inexplorado"
    elif saturacao == "baixa":
        base = f"Apenas {competitors} concorrente(s) próximo(s) — boa janela de entrada"
    elif saturacao == "media":
        base = f"{competitors} concorrentes próximos — competição moderada"
    else:
        base = f"{competitors} concorrentes em {MARKET_ANALYSIS_RADIUS}m — mercado saturado"

    if synergies >= 3:
        base += f"; forte sinergia ({synergies} negócios complementares)"
    if anchors >= 2:
        base += f"; região com âncoras de tráfego ({anchors})"
    return base


def analyze_region_market(
    lat: float,
    lon: float,
    nicho: str,
    cache_df: pd.DataFrame,
    session: requests.Session,
    nearby_count_fn,
    hkey_fn,
    cache_records: List[dict],
    radius: int = MARKET_ANALYSIS_RADIUS,
    nearby_names_fn=None,
) -> Dict:
    """
    Calcula métricas de mercado para uma única região.

    Args:
        nearby_count_fn: função (lat, lon, type, radius, session) -> int
        hkey_fn: função (lat, lon, type, radius) -> str (chave de cache)
        cache_records: lista mutável onde novos registros são acumulados

    Returns:
        dict com: competitors, synergies, anchors, density, saturacao, insight
    """
    competitor_types = COMPETITOR_TYPES_BY_NICHE.get(nicho, COMPETITOR_TYPES_BY_NICHE["Outro"])
    synergy_types = SYNERGY_TYPES_BY_NICHE.get(nicho, SYNERGY_TYPES_BY_NICHE["Outro"])

    competitors = _count_types(lat, lon, competitor_types, radius, cache_df, session, nearby_count_fn, hkey_fn, cache_records)
    synergies = _count_types(lat, lon, synergy_types, radius, cache_df, session, nearby_count_fn, hkey_fn, cache_records)
    anchors = _count_types(lat, lon, ANCHOR_TYPES, radius, cache_df, session, nearby_count_fn, hkey_fn, cache_records)

    density = competitors + synergies + anchors
    saturacao = _classify_saturation(competitors)
    insight = _build_insight(competitors, synergies, anchors, saturacao)
    competitor_names = _get_names(
        lat, lon,
        COMPETITOR_TYPES_BY_NICHE.get(nicho, COMPETITOR_TYPES_BY_NICHE["Outro"]),
        radius, session, nearby_names_fn,
    )

    return {
        "competitors": competitors,
        "synergies": synergies,
        "anchors": anchors,
        "density": density,
        "saturacao": saturacao,
        "raio_m": radius,
        "insight": insight,
        "competitor_names": competitor_names,
    }


def analyze_top_regions(
    regioes: List[dict],
    nicho: str,
    cache_df: pd.DataFrame,
    session: requests.Session,
    nearby_count_fn,
    hkey_fn,
    save_cache_fn,
    top_n: int = MARKET_ANALYSIS_TOP_N,
    nearby_names_fn=None,
) -> List[dict]:
    """
    Aplica `analyze_region_market` apenas nas top-N regiões (já ordenadas
    por score) e injeta o resultado no campo `analise_mercado` de cada uma.

    Para evitar análises duplicadas em pontos muito próximos, agrupa por
    coordenadas arredondadas a ~100m.

    Returns:
        A mesma lista de regiões com `analise_mercado` adicionado nas top-N.
    """
    if not regioes:
        return regioes

    # Agrupa coords próximas (~100m) para evitar repetir análise
    cache_local: Dict[tuple, Dict] = {}
    cache_records: List[dict] = []

    analisadas = 0
    for r in regioes:
        if analisadas >= top_n:
            break
        try:
            lat = float(r["lat"])
            lon = float(r["lon"])
        except (KeyError, ValueError, TypeError):
            continue

        key = (round(lat, 3), round(lon, 3))
        if key in cache_local:
            r["analise_mercado"] = cache_local[key]
        else:
            mercado = analyze_region_market(
                lat, lon, nicho,
                cache_df=cache_df,
                session=session,
                nearby_count_fn=nearby_count_fn,
                hkey_fn=hkey_fn,
                cache_records=cache_records,
                nearby_names_fn=nearby_names_fn,
            )
            cache_local[key] = mercado
            r["analise_mercado"] = mercado
        analisadas += 1

    # Persiste novos registros no cache do Places
    if cache_records:
        try:
            cache_df = pd.concat([cache_df, pd.DataFrame(cache_records)], ignore_index=True)
            save_cache_fn(cache_df)
        except Exception as exc:  # pragma: no cover
            print(f"⚠️ Falha ao salvar cache de mercado: {exc}")

    return regioes
