#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the full Taiwan stock seed list for the autocomplete index.

Data source: the `twstock` package's bundled security catalog, which is a
snapshot of the official TWSE ISIN registry (isin.twse.com.tw) covering both
TWSE (上市) and TPEX (上櫃) boards. Refresh by upgrading the package
(`pip install -U twstock`) and re-running this script, then re-generate
`apps/dsa-web/public/stocks.index.json` via scripts/generate_index_from_csv.py.

Output: scripts/stock_index_seeds/stock_list_tw.csv
        (ts_code,symbol,name,enname,aliases — same schema as the JP/KR seeds)

Inclusion rules:
  - 股票 / 創新板 with 4-digit codes -> included (上市* -> .TW, 上櫃 -> .TWO)
  - ETF with 4-digit codes -> included (0050, 0056, ...)
  - 5-digit ETFs (e.g. 00878) are EXCLUDED: bare 5-digit codes carry HK
    semantics repo-wide (00878 resolves to 00878.HK), so indexing them would
    hijack existing HK bare-code behavior. They remain analyzable via the
    full `.TW` suffix.
  - 特別股 / 權證 / TDR / ETN / 受益證券 are excluded (non-common-stock or
    codes outside the supported 4-5 digit numeric form).

Primary `name` is Simplified Chinese (converted via OpenCC) to match the
bundled index convention; the official Traditional name is kept as an alias
so Traditional-script searches still hit.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, List, NamedTuple

DEFAULT_OUTPUT = Path(__file__).parent / "stock_index_seeds" / "stock_list_tw.csv"

# Types from the TWSE ISIN registry that map to common stocks / index ETFs.
_STOCK_TYPES = {"股票", "創新板"}
_ETF_TYPE = "ETF"

# Hand-maintained extra aliases (English trade names, legacy search terms).
# twstock's catalog has no English names, so popular English identifiers and
# well-known long-form names live here.
CURATED_EXTRA_ALIASES: Dict[str, List[str]] = {
    "2330": ["TSMC", "台湾积体电路"],
    "2317": ["Foxconn", "富士康"],
    "2454": ["MediaTek", "联发科技"],
    "2308": ["Delta"],
    "2382": ["Quanta"],
    "2412": ["CHT", "中華電信", "中华电信"],
    "2881": ["Fubon"],
    "2882": ["Cathay"],
    "2603": ["Evergreen"],
    "3008": ["Largan"],
    "0050": ["台灣50", "台湾50"],
    "6488": ["GlobalWafers"],
    "8069": ["E Ink", "EInk"],
}


class CatalogEntry(NamedTuple):
    """Normalized view of one TWSE ISIN registry row."""

    code: str
    name: str
    market: str
    type: str


def _yahoo_suffix(market: str) -> str | None:
    """Map an ISIN board label to the Yahoo Finance suffix, or None to skip."""
    normalized = (market or "").strip()
    if normalized.startswith("上市"):
        return "TW"
    if normalized.startswith("上櫃"):
        return "TWO"
    return None


def _include(entry: CatalogEntry) -> bool:
    code = (entry.code or "").strip()
    if not (code.isdigit() and len(code) == 4):
        return False
    return entry.type in _STOCK_TYPES or entry.type == _ETF_TYPE


def build_seed_rows(
    entries: Iterable[CatalogEntry],
    to_simplified: Callable[[str], str],
) -> List[Dict[str, str]]:
    """Build seed CSV rows from catalog entries.

    Filters to 4-digit common stocks / innovation-board stocks / ETFs,
    maps boards to Yahoo suffixes, converts names to Simplified Chinese and
    keeps the Traditional original plus curated extras as aliases.
    """
    rows: Dict[str, Dict[str, str]] = {}
    for entry in entries:
        if not _include(entry):
            continue
        suffix = _yahoo_suffix(entry.market)
        if suffix is None:
            continue
        code = entry.code.strip()
        if code in rows:
            continue

        traditional = (entry.name or "").strip()
        if not traditional:
            continue
        simplified = to_simplified(traditional).strip() or traditional

        aliases: List[str] = []
        if traditional != simplified:
            aliases.append(traditional)
        for extra in CURATED_EXTRA_ALIASES.get(code, []):
            if extra != simplified and extra not in aliases:
                aliases.append(extra)

        ts_code = f"{code}.{suffix}"
        rows[code] = {
            "ts_code": ts_code,
            "symbol": ts_code,
            "name": simplified,
            "enname": "",
            "aliases": "|".join(aliases),
        }

    return [rows[code] for code in sorted(rows)]


def load_twstock_entries() -> List[CatalogEntry]:
    """Load catalog entries from the twstock package."""
    try:
        import twstock
    except ImportError:
        print("[Error] twstock not available; install with: pip install twstock")
        raise SystemExit(1)

    return [
        CatalogEntry(code=info.code, name=info.name, market=info.market, type=info.type)
        for info in twstock.codes.values()
    ]


def make_simplifier() -> Callable[[str], str]:
    """Return a Traditional->Simplified converter."""
    try:
        from opencc import OpenCC
    except ImportError:
        print(
            "[Error] OpenCC not available; install with: "
            "pip install opencc-python-reimplemented"
        )
        raise SystemExit(1)

    return OpenCC("t2s").convert


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the Taiwan stock seed CSV")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    entries = load_twstock_entries()
    rows = build_seed_rows(entries, make_simplifier())
    if not rows:
        print("[Error] no Taiwan stock rows produced; catalog empty or filtered out")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ts_code", "symbol", "name", "enname", "aliases"])
        writer.writeheader()
        writer.writerows(rows)

    twse = sum(1 for r in rows if r["ts_code"].endswith(".TW"))
    tpex = len(rows) - twse
    print(f"Wrote {len(rows)} rows to {args.output} (TWSE .TW: {twse}, TPEX .TWO: {tpex})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
