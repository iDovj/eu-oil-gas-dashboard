# EU Oil & Gas Trade Explorer

Interactive Streamlit dashboard for crude-oil and natural-gas import flows into the current EU-27, 2000-2024.

## What v0.1 already does

- Oil / gas switch.
- Year slider 2000-2024.
- Sankey links keep the supplier color all the way to the EU importer.
- Absolute flow width.
- Hover: volume + importer share + supplier-to-EU share + EU-wide share.
- Filters for importer, supplier, external-only scope, and minimum importer share.
- Detail tables for a selected importer or supplier.

## Data sources

- Oil: Eurostat `nrg_ti_oil`, SIEC `O4100_TOT` (crude oil), unit `THS_T`.
- Gas: Eurostat `nrg_ti_gas`, SIEC `G3000` (natural gas), unit `MIO_M3`.
- Time range: 2000-2024.
- Import partner is the country of ultimate origin according to Eurostat energy-trade methodology.

The fetch script converts:

- thousand tonnes -> million tonnes (`Mt`)
- million cubic metres -> billion cubic metres (`bcm`)

## Run locally on Windows / VS Code

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/fetch_eurostat.py
streamlit run app.py
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

## Inspect Eurostat dimensions if a code changes

```powershell
python scripts/inspect_dataset.py nrg_ti_oil --year 2024
python scripts/inspect_dataset.py nrg_ti_gas --year 2024
```

## Deploy to Streamlit Community Cloud

1. Push the project to GitHub.
2. In Streamlit Community Cloud choose the repository.
3. Main file: `app.py`.
4. Keep the generated parquet files in `data/processed/` for fast startup.

## Next planned steps

1. Sankey node click -> filter to one importer/exporter.
2. Click on a link -> bilateral-flow card.
3. Historical chart for a selected country/supplier.
4. Play/pause year animation.
5. Data-quality / coverage panel.
6. Optional historical-EU-membership mode.
