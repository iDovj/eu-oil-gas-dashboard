from __future__ import annotations

import pandas as pd
import streamlit as st

from src.config import DATA_DIR, PRODUCTS


@st.cache_data(show_spinner=False)
def load_trade_data(commodity: str) -> pd.DataFrame:
    path = DATA_DIR / PRODUCTS[commodity]["dataset"]
    if not path.exists():
        raise FileNotFoundError(
            f"Нет файла {path}. Сначала выполните: python scripts/fetch_eurostat.py"
        )

    df = pd.read_parquet(path)
    df["year"] = df["year"].astype(int)
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    return df.dropna(subset=["volume"])
