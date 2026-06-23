# -*- coding: utf-8 -*-
"""Regression tests for Taiwan (.TW / .TWO) suffix-only market support."""

from unittest.mock import patch

import pandas as pd
from data_provider.base import BaseFetcher, DataFetchError, DataFetcherManager, normalize_stock_code
from data_provider.yfinance_fetcher import YfinanceFetcher
from src.core.trading_calendar import MARKET_EXCHANGE, MARKET_TIMEZONE, get_market_for_stock
from src.market_context import detect_market, get_market_guidelines
from src.services.stock_code_utils import is_code_like, normalize_code


class _FakeFetcher(BaseFetcher):
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.priority = 0 if name != "YfinanceFetcher" else 4
        self.calls = []
        self.should_fail = should_fail

    def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        raise NotImplementedError

    def _normalize_data(self, df: pd.DataFrame, stock_code: str) -> pd.DataFrame:
        raise NotImplementedError

    def get_daily_data(self, stock_code, start_date=None, end_date=None, days=30):
        self.calls.append(stock_code)
        if self.should_fail:
            raise DataFetchError(f"{self.name} should not be called for {stock_code}")
        return pd.DataFrame(
            {
                "date": [pd.Timestamp("2026-06-18")],
                "open": [1.0],
                "high": [1.0],
                "low": [1.0],
                "close": [1.0],
                "volume": [100],
                "amount": [100.0],
                "pct_chg": [0.0],
            }
        )


def test_normalize_and_detect_tw_suffix_codes() -> None:
    assert normalize_stock_code("2330.tw") == "2330.TW"
    assert normalize_stock_code("6488.two") == "6488.TWO"
    assert normalize_stock_code("00878.tw") == "00878.TW"

    assert detect_market("2330.TW") == "tw"
    assert detect_market("6488.TWO") == "tw"
    assert detect_market("00878.TW") == "tw"
    # Bare 4-digit codes have no suffix and remain A-share fallback.
    assert detect_market("2330") == "cn"

    assert get_market_for_stock("2330.TW") == "tw"
    assert get_market_for_stock("6488.TWO") == "tw"
    # Bare 4-digit codes are not a supported TW input; the phase detector only
    # maps 6-digit bare codes to "cn" and leaves shorter codes unrecognized
    # (fail-open), so it must not be misread as "tw".
    assert get_market_for_stock("2330") is None

    assert is_code_like("2330.TW") is True
    assert is_code_like("6488.TWO") is True
    assert normalize_code("2330.tw") == "2330.TW"


def test_market_guidelines_for_tw_exclude_a_share_specific_context() -> None:
    tw_guidelines = get_market_guidelines("2330.TW")

    assert "台股" in tw_guidelines
    assert "不要套用 A 股" in tw_guidelines
    assert "北向资金" in tw_guidelines
    assert "龙虎榜" in tw_guidelines


def test_yfinance_keeps_tw_suffix_codes_and_indices() -> None:
    fetcher = YfinanceFetcher()

    assert fetcher._convert_stock_code("2330.TW") == "2330.TW"
    assert fetcher._convert_stock_code("6488.TWO") == "6488.TWO"

    captured = []

    def fake_fetch(_yf, yf_code, name, return_code):
        captured.append((yf_code, name, return_code))
        return {"code": return_code, "name": name, "current": 1.0}

    fetcher._fetch_yf_ticker_data = fake_fetch  # type: ignore[method-assign]

    tw_indices = fetcher.get_main_indices("tw") or []

    assert {item["code"] for item in tw_indices} == {"TWII"}
    assert ("^TWII", "台湾加权指数", "TWII") in captured


def test_data_fetcher_manager_routes_tw_daily_only_to_yfinance() -> None:
    efinance = _FakeFetcher("EfinanceFetcher", should_fail=True)
    akshare = _FakeFetcher("AkshareFetcher", should_fail=True)
    yfinance = _FakeFetcher("YfinanceFetcher")
    manager = DataFetcherManager(fetchers=[efinance, akshare, yfinance])

    with patch("data_provider.base.record_provider_run_started"), patch("data_provider.base.record_provider_run"):
        tw_df, tw_source = manager.get_daily_data("2330.TW")
        two_df, two_source = manager.get_daily_data("6488.TWO")

    assert tw_source == "YfinanceFetcher"
    assert two_source == "YfinanceFetcher"
    assert not tw_df.empty and not two_df.empty
    assert efinance.calls == []
    assert akshare.calls == []
    assert yfinance.calls == ["2330.TW", "6488.TWO"]


def test_trading_calendar_registers_tw_exchange_and_timezone() -> None:
    assert MARKET_EXCHANGE["tw"] == "XTAI"
    assert MARKET_TIMEZONE["tw"] == "Asia/Taipei"
