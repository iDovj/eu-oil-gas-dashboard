from __future__ import annotations

import argparse
import json

import requests

API_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", help="Example: nrg_ti_oil or nrg_ti_gas")
    parser.add_argument("--year", type=int, default=2024)
    args = parser.parse_args()

    url = f"{API_BASE}/{args.dataset}"
    r = requests.get(
        url,
        params={"format": "JSON", "lang": "EN", "time": args.year, "geo": "AT"},
        timeout=120,
    )
    r.raise_for_status()
    payload = r.json()

    print("Dimensions:", payload.get("id"))
    for dim in payload.get("id", []):
        cat = payload["dimension"][dim]["category"]
        print(f"\n[{dim}]")
        labels = cat.get("label", {})
        index = cat.get("index", {})
        if isinstance(index, dict):
            ordered = [k for k, _ in sorted(index.items(), key=lambda kv: kv[1])]
        else:
            ordered = index
        for code in ordered[:100]:
            print(f"  {code}: {labels.get(code, code)}")


if __name__ == "__main__":
    main()
