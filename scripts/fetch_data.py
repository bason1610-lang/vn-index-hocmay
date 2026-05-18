"""
fetch_data.py
-------------
Tải dữ liệu cổ phiếu **VCB.VN** từ Yahoo Finance bằng thư viện ``yfinance`` và
lưu thành ``data/vcb_stock.csv`` ở định dạng đa khung thời gian (1d + 1h).

Cách dùng:
    python scripts/fetch_data.py
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import yfinance as yf


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = PROJECT_ROOT / "data" / "vcb_stock.csv"
SYMBOL = "VCB.VN"   # Vietcombank trên Yahoo Finance


def _flatten(df: pd.DataFrame) -> pd.DataFrame:
    """Đôi khi yfinance trả về MultiIndex columns — ta làm phẳng."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    return df


def download(symbol: str = SYMBOL) -> pd.DataFrame:
    daily = yf.download(symbol, period="max", interval="1d",
                        auto_adjust=False, progress=False)
    daily = _flatten(daily).reset_index()
    daily["Interval"] = "1d"

    hourly = yf.download(symbol, period="730d", interval="1h",
                         auto_adjust=False, progress=False)
    hourly = _flatten(hourly).reset_index()
    hourly = hourly.rename(columns={"Datetime": "Date"})
    hourly["Interval"] = "1h"

    keep = ["Date", "Close", "High", "Low", "Open", "Volume", "Interval"]
    df = pd.concat([daily[keep], hourly[keep]], ignore_index=True)
    df["Ticker"] = "VCB"
    df["Symbol"] = symbol
    df = df.dropna(subset=["Close"]).sort_values(["Interval", "Date"])
    return df


def main() -> int:
    print(f"Đang tải dữ liệu {SYMBOL} từ Yahoo Finance...")
    df = download()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Đã lưu {len(df):,} dòng vào {OUT_PATH}")
    print(df.groupby("Interval").size().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
