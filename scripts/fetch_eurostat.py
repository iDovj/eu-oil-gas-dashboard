from __future__ import annotations

import itertools
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pycountry
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import DATA_DIR, EU27, YEAR_MAX, YEAR_MIN  # noqa: E402

API_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

DATASETS = {
    "oil": {
        "dataset": "nrg_ti_oil",
        "filters": {
            "freq": "A",
            "unit": "THS_T",
            # SIEC: Crude oil
            "siec": "O4100_TOT",
        },
        "factor": 1000.0,  # thousand tonnes -> million tonnes (Mt)
        "display_unit": "Mt",
        "filename": "oil_imports.parquet",
    },
    "gas": {
        "dataset": "nrg_ti_gas",
        "filters": {
            "freq": "A",
            "unit": "MIO_M3",
            # SIEC: Natural gas
            "siec": "G3000",
        },
        "factor": 1000.0,  # million m3 -> billion m3 (bcm)
        "display_unit": "bcm",
        "filename": "gas_imports.parquet",
    },
}

EU27_CODES = set(EU27)


def session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "eu-energy-dashboard/0.1"})
    return s


def _ordered_codes(category: dict) -> list[str]:
    idx = category.get("index", {})
    if isinstance(idx, list):
        return idx
    return [code for code, _ in sorted(idx.items(), key=lambda kv: kv[1])]


def jsonstat_to_frame(payload: dict) -> pd.DataFrame:
    dims = payload["id"]
    sizes = payload["size"]
    dim_codes: dict[str, list[str]] = {}
    dim_labels: dict[str, dict[str, str]] = {}

    for dim in dims:
        category = payload["dimension"][dim]["category"]
        dim_codes[dim] = _ordered_codes(category)
        dim_labels[dim] = category.get("label", {})

    values = payload.get("value", [])
    if isinstance(values, dict):
        value_items = ((int(k), v) for k, v in values.items() if v is not None)
    else:
        value_items = ((i, v) for i, v in enumerate(values) if v is not None)

    rows = []
    for flat_index, value in value_items:
        coords = np.unravel_index(flat_index, sizes)
        row = {dim: dim_codes[dim][coords[i]] for i, dim in enumerate(dims)}
        row["value"] = value
        for dim in dims:
            code = row[dim]
            row[f"{dim}_label"] = dim_labels[dim].get(code, code)
        rows.append(row)

    return pd.DataFrame(rows)


def is_country_code(code: str) -> bool:
    # Eurostat uses a few non-ISO aliases.
    if code in {"UK", "EL", "XK"}:
        return True
    if not re.fullmatch(r"[A-Z]{2}", str(code)):
        return False
    if code in {"EU", "EA"}:
        return False
    return pycountry.countries.get(alpha_2=code) is not None


def fetch_dataset(kind: str) -> pd.DataFrame:
    cfg = DATASETS[kind]
    url = f"{API_BASE}/{cfg['dataset']}"

    frames = []
    s = session()

    countries = list(EU27.keys())

    print(
        f"Downloading {kind}: {cfg['dataset']} "
        f"{YEAR_MIN}-{YEAR_MAX}"
    )

    for i, geo_code in enumerate(countries, start=1):
        country_name = EU27[geo_code]

        print(
            f"[{i:02d}/{len(countries)}] "
            f"{country_name} ({geo_code}) ..."
        )

        params = [
            ("format", "JSON"),
            ("lang", "EN"),
            ("sinceTimePeriod", YEAR_MIN),
            ("untilTimePeriod", YEAR_MAX),
            ("geo", geo_code),
        ]

        params += list(cfg["filters"].items())

        try:
            r = s.get(
                url,
                params=params,
                timeout=(20, 120),
            )
            r.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed downloading {kind} for "
                f"{country_name} ({geo_code}): {exc}"
            ) from exc

        payload = r.json()

        if "error" in payload:
            raise RuntimeError(
                f"Eurostat error for {geo_code}: "
                f"{payload['error']}"
            )

        part = jsonstat_to_frame(payload)

        if part.empty:
            print("    no observations")
            continue

        frames.append(part)

        print(
            f"    received {len(part):,} observations"
        )

    if not frames:
        raise RuntimeError(
            f"Eurostat returned no observations "
            f"for {cfg['dataset']}."
        )

    print("Combining downloaded countries ...")

    df = pd.concat(
        frames,
        ignore_index=True,
    )

    df.columns = [c.lower() for c in df.columns]

    required = {"geo", "partner", "time", "value"}
    missing = required - set(df.columns)

    if missing:
        raise RuntimeError(
            f"Missing expected dimensions: "
            f"{sorted(missing)}. "
            f"Got {df.columns.tolist()}"
        )

    df = df[df["geo"].isin(EU27_CODES)].copy()

    # Keep only actual countries as suppliers.
    # This removes TOTAL, EU aggregates, etc.
    df = df[
        df["partner"].map(is_country_code)
    ].copy()

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    df = df[
        df["value"].fillna(0).gt(0)
    ].copy()

    df["year"] = pd.to_numeric(
        df["time"],
        errors="raise",
    ).astype(int)

    df["raw_value"] = df["value"]

    # Eurostat:
    # oil: thousand tonnes -> million tonnes
    # gas: million m3 -> billion m3
    df["volume"] = (
        df["raw_value"] / cfg["factor"]
    )

    df = df.rename(
        columns={
            "geo": "importer_code",
            "geo_label": "importer_name",
            "partner": "exporter_code",
            "partner_label": "exporter_name",
        }
    )

    df["is_extra_eu"] = ~df[
        "exporter_code"
    ].isin(EU27_CODES)

    df["commodity"] = kind
    df["unit"] = cfg["display_unit"]

    keep = [
        "year",
        "commodity",
        "importer_code",
        "importer_name",
        "exporter_code",
        "exporter_name",
        "volume",
        "unit",
        "raw_value",
        "is_extra_eu",
    ]

    out = (
        df[keep]
        .groupby(
            [
                "year",
                "commodity",
                "importer_code",
                "importer_name",
                "exporter_code",
                "exporter_name",
                "unit",
                "is_extra_eu",
            ],
            as_index=False,
        )[["volume", "raw_value"]]
        .sum()
        .sort_values(
            [
                "year",
                "importer_code",
                "volume",
            ],
            ascending=[True, True, False],
        )
    )

    return out


    cfg = DATASETS[kind]
    url = f"{API_BASE}/{cfg['dataset']}"

    params: list[tuple[str, str | int]] = [
        ("format", "JSON"),
        ("lang", "EN"),
        ("sinceTimePeriod", YEAR_MIN),
        ("untilTimePeriod", YEAR_MAX),
    ]
    params += list(cfg["filters"].items())
    params += [("geo", code) for code in EU27_CODES]

    print(f"Downloading {kind}: {cfg['dataset']} {YEAR_MIN}-{YEAR_MAX} ...")
    r = session().get(url, params=params, timeout=180)
    r.raise_for_status()
    payload = r.json()

    if "error" in payload:
        raise RuntimeError(payload["error"])

    print("Dimensions:", payload.get("id"))
    df = jsonstat_to_frame(payload)
    if df.empty:
        raise RuntimeError(
            f"Eurostat returned no observations for {cfg['dataset']}. "
            "Check SIEC/unit codes in DATASETS."
        )

    df.columns = [c.lower() for c in df.columns]
    required = {"geo", "partner", "time", "value"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing expected dimensions: {sorted(missing)}. Got {df.columns.tolist()}")

    df = df[df["geo"].isin(EU27_CODES)].copy()
    df = df[df["partner"].map(is_country_code)].copy()
    df = df[pd.to_numeric(df["value"], errors="coerce").fillna(0).gt(0)].copy()

    df["year"] = pd.to_numeric(df["time"], errors="raise").astype(int)
    df["raw_value"] = pd.to_numeric(df["value"], errors="coerce")
    df["volume"] = df["raw_value"] / cfg["factor"]

    df = df.rename(
        columns={
            "geo": "importer_code",
            "geo_label": "importer_name",
            "partner": "exporter_code",
            "partner_label": "exporter_name",
        }
    )

    # Ultimate-origin partner country according to Eurostat energy-trade methodology.
    df["is_extra_eu"] = ~df["exporter_code"].isin(EU27_CODES)
    df["commodity"] = kind
    df["unit"] = cfg["display_unit"]

    keep = [
        "year",
        "commodity",
        "importer_code",
        "importer_name",
        "exporter_code",
        "exporter_name",
        "volume",
        "unit",
        "raw_value",
        "is_extra_eu",
    ]
    out = (
        df[keep]
        .groupby(
            [
                "year",
                "commodity",
                "importer_code",
                "importer_name",
                "exporter_code",
                "exporter_name",
                "unit",
                "is_extra_eu",
            ],
            as_index=False,
        )[["volume", "raw_value"]]
        .sum()
        .sort_values(["year", "importer_code", "volume"], ascending=[True, True, False])
    )
    return out


def validate(df: pd.DataFrame, kind: str) -> None:
    years = sorted(df["year"].unique())
    if years[0] > YEAR_MIN or years[-1] < YEAR_MAX:
        print(f"WARNING: {kind} coverage is {years[0]}-{years[-1]}, expected {YEAR_MIN}-{YEAR_MAX}")
    print(
        f"{kind}: {len(df):,} bilateral rows, "
        f"{df['importer_code'].nunique()} importers, "
        f"{df['exporter_code'].nunique()} partner countries, "
        f"years {years[0]}-{years[-1]}"
    )


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for kind, cfg in DATASETS.items():
        df = fetch_dataset(kind)
        validate(df, kind)
        target = DATA_DIR / cfg["filename"]
        df.to_parquet(target, index=False)
        print(f"Saved: {target}\n")


if __name__ == "__main__":
    main()
