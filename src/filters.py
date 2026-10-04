from __future__ import annotations

import pandas as pd


def prepare_year_scope(
    df: pd.DataFrame,
    year: int,
    extra_eu_only: bool,
) -> pd.DataFrame:
    """Filter to year/scope and calculate shares before country selection."""
    base = df[df["year"].eq(year)].copy()
    if extra_eu_only:
        base = base[base["is_extra_eu"]].copy()

    if base.empty:
        return base

    base["importer_total"] = base.groupby("importer_code")["volume"].transform("sum")
    base["exporter_total_eu"] = base.groupby("exporter_code")["volume"].transform("sum")
    eu_total = float(base["volume"].sum())
    base["eu_total"] = eu_total

    base["share_importer"] = base["volume"] / base["importer_total"] * 100
    base["share_exporter_eu"] = base["volume"] / base["exporter_total_eu"] * 100
    base["share_eu"] = base["volume"] / eu_total * 100 if eu_total else 0.0
    return base


def apply_selection(
    base: pd.DataFrame,
    importer_code: str | None,
    exporter_code: str | None,
    min_importer_share: float,
) -> pd.DataFrame:
    out = base.copy()
    if importer_code:
        out = out[out["importer_code"].eq(importer_code)]
    if exporter_code:
        out = out[out["exporter_code"].eq(exporter_code)]
    if min_importer_share > 0:
        out = out[out["share_importer"].ge(min_importer_share)]
    return out
