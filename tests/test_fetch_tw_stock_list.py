# -*- coding: utf-8 -*-
"""Offline tests for the Taiwan stock seed generator (scripts/fetch_tw_stock_list.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from fetch_tw_stock_list import CatalogEntry, build_seed_rows  # noqa: E402

_T2S = {"台積電": "台积电", "環球晶": "环球晶", "睿生光電": "睿生光电"}


def _fake_simplifier(text: str) -> str:
    return _T2S.get(text, text)


def test_build_seed_rows_filters_and_maps_boards() -> None:
    entries = [
        CatalogEntry("2330", "台積電", "上市", "股票"),
        CatalogEntry("6488", "環球晶", "上櫃", "股票"),
        CatalogEntry("2254", "巨鎧精密-創", "上市臺灣創新板", "創新板"),
        CatalogEntry("0050", "元大台灣50", "上市", "ETF"),
        # Excluded: 5-digit ETF (HK bare-code semantics), preferred share,
        # warrant, TDR, and a non-listed board.
        CatalogEntry("00878", "國泰永續高股息", "上市", "ETF"),
        CatalogEntry("2881A", "富邦特", "上市", "特別股"),
        CatalogEntry("030001", "某權證", "上市", "上市認購(售)權證"),
        CatalogEntry("9103", "美德醫療-DR", "上市", "臺灣存託憑證(TDR)"),
        CatalogEntry("1234", "興櫃股", "興櫃", "股票"),
    ]

    rows = build_seed_rows(entries, _fake_simplifier)
    by_code = {row["ts_code"]: row for row in rows}

    assert set(by_code) == {"2330.TW", "6488.TWO", "2254.TW", "0050.TW"}
    assert by_code["2330.TW"]["symbol"] == "2330.TW"
    assert by_code["6488.TWO"]["name"] == "环球晶"


def test_build_seed_rows_keeps_traditional_and_curated_aliases() -> None:
    entries = [
        CatalogEntry("2330", "台積電", "上市", "股票"),
        CatalogEntry("2382", "廣達", "上市", "股票"),
    ]

    rows = build_seed_rows(entries, _fake_simplifier)
    by_code = {row["ts_code"]: row for row in rows}

    aliases_2330 = by_code["2330.TW"]["aliases"].split("|")
    assert aliases_2330[0] == "台積電"  # Traditional original kept first
    assert "TSMC" in aliases_2330  # curated English alias merged
    # No conversion difference for 廣達 in the fake simplifier: alias only from curated map.
    assert "Quanta" in by_code["2382.TW"]["aliases"].split("|")


def test_build_seed_rows_dedupes_and_sorts_by_code() -> None:
    entries = [
        CatalogEntry("6488", "環球晶", "上櫃", "股票"),
        CatalogEntry("2330", "台積電", "上市", "股票"),
        CatalogEntry("2330", "重複列", "上市", "股票"),
    ]

    rows = build_seed_rows(entries, _fake_simplifier)

    assert [row["ts_code"] for row in rows] == ["2330.TW", "6488.TWO"]
    assert rows[0]["name"] == "台积电"  # first occurrence wins
