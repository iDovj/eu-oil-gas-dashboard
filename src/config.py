from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "processed"

YEAR_MIN = 2000
YEAR_MAX = 2024

# We keep a constant current EU-27 set for the full 2000-2024 history.
# That makes year-to-year Sankey comparisons consistent even before some
# of these countries joined the EU.
EU27 = {
    "AT": "Austria",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DK": "Denmark",
    "EE": "Estonia",
    "FI": "Finland",
    "FR": "France",
    "DE": "Germany",
    "EL": "Greece",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LV": "Latvia",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MT": "Malta",
    "NL": "Netherlands",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "SK": "Slovakia",
    "SI": "Slovenia",
    "ES": "Spain",
    "SE": "Sweden",
}

PRODUCTS = {
    "Нефть": {
        "dataset": "oil_imports.parquet",
        "unit": "Mt",
        "unit_long": "млн тонн",
        "title": "Сырая нефть",
    },
    "Газ": {
        "dataset": "gas_imports.parquet",
        "unit": "bcm",
        "unit_long": "млрд м³",
        "title": "Природный газ",
    },
}
