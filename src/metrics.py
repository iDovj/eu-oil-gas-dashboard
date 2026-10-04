from __future__ import annotations

import pandas as pd


def overview_metrics(base: pd.DataFrame) -> dict:
    if base.empty:
        return {
            "total": 0.0,
            "importers": 0,
            "exporters": 0,
            "top_supplier": "—",
            "top_supplier_share": 0.0,
        }

    suppliers = (
        base.groupby(["exporter_code", "exporter_name"], as_index=False)["volume"]
        .sum()
        .sort_values("volume", ascending=False)
    )
    top = suppliers.iloc[0]
    total = float(base["volume"].sum())
    return {
        "total": total,
        "importers": int(base["importer_code"].nunique()),
        "exporters": int(base["exporter_code"].nunique()),
        "top_supplier": str(top["exporter_name"]),
        "top_supplier_share": float(top["volume"] / total * 100) if total else 0.0,
    }


def country_import_table(base: pd.DataFrame, importer_code: str) -> pd.DataFrame:
    out = base[base["importer_code"].eq(importer_code)].copy()
    cols = [
        "exporter_name",
        "volume",
        "share_importer",
        "share_exporter_eu",
        "share_eu",
    ]
    return out[cols].sort_values("volume", ascending=False).reset_index(drop=True)


def supplier_destination_table(base: pd.DataFrame, exporter_code: str) -> pd.DataFrame:
    out = base[base["exporter_code"].eq(exporter_code)].copy()
    cols = [
        "importer_name",
        "volume",
        "share_importer",
        "share_exporter_eu",
        "share_eu",
    ]
    return out[cols].sort_values("volume", ascending=False).reset_index(drop=True)
