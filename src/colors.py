from __future__ import annotations

import colorsys
import hashlib

# Curated colors for the biggest / most common suppliers.
# The same exporter keeps the same color in every year and every importer view.
FIXED_SUPPLIER_COLORS = {
    "US": "#2563EB",
    "NO": "#F97316",
    "KZ": "#16A34A",
    "SA": "#DC2626",
    "LY": "#7C3AED",
    "IQ": "#92400E",
    "UK": "#EC4899",
    "AZ": "#0891B2",
    "RU": "#1D4ED8",
    "DZ": "#65A30D",
    "QA": "#9D174D",
    "NG": "#9333EA",
    "BR": "#A16207",
    "CA": "#DB2777",
    "AO": "#0F766E",
    "MX": "#BE185D",
    "AE": "#EF4444",
    "KW": "#CA8A04",
    "OM": "#64748B",
    "EG": "#06B6D4",
}


def supplier_color(code: str) -> str:
    if code in FIXED_SUPPLIER_COLORS:
        return FIXED_SUPPLIER_COLORS[code]

    # Stable fallback: derive a color from the country code.
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
    hue = int(digest[:8], 16) / 0xFFFFFFFF
    sat = 0.62 + (int(digest[8:10], 16) / 255) * 0.16
    light = 0.44 + (int(digest[10:12], 16) / 255) * 0.12
    r, g, b = colorsys.hls_to_rgb(hue, light, sat)
    return f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"


def rgba(hex_color: str, alpha: float = 0.58) -> str:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
