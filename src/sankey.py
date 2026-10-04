from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from src.colors import rgba, supplier_color


NEUTRAL_IMPORTER = "#D9DEE7"
NEUTRAL_BORDER = "#AAB2C0"


def _stack_positions(
    values: list[float],
    gap: float,
) -> list[float]:
    """
    Calculate vertical centres of Sankey nodes.

    Plotly Sankey coordinates:
        y = 0 -> top
        y = 1 -> bottom
    """

    if not values:
        return []

    total = sum(values)

    if total <= 0:
        return [
            (i + 0.5) / len(values)
            for i in range(len(values))
        ]

    n = len(values)

    total_gap = (
        gap * max(0, n - 1)
    )

    usable_height = max(
        0.45,
        1.0 - total_gap,
    )

    positions: list[float] = []

    cursor = 0.0

    for value in values:

        node_height = (
            usable_height
            * value
            / total
        )

        centre = (
            cursor
            + node_height / 2
        )

        positions.append(
            min(
                0.995,
                max(
                    0.005,
                    centre,
                ),
            )
        )

        cursor += (
            node_height
            + gap
        )

    return positions


def build_sankey(
    df: pd.DataFrame,
    title: str,
    unit: str,
) -> go.Figure:

    # =====================================================
    # EMPTY DATA
    # =====================================================

    if df.empty:

        fig = go.Figure()

        fig.add_annotation(
            text=(
                "Нет данных для "
                "выбранных фильтров"
            ),
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(
                size=20,
            ),
        )

        fig.update_layout(
            height=450,
            paper_bgcolor="white",
        )

        return fig


    # =====================================================
    # BILATERAL FLOWS
    # =====================================================

    links = (
        df.groupby(
            [
                "exporter_code",
                "exporter_name",
                "importer_code",
                "importer_name",
            ],
            as_index=False,
        )
        .agg(
            volume=(
                "volume",
                "sum",
            ),
            share_importer=(
                "share_importer",
                "sum",
            ),
            share_exporter_eu=(
                "share_exporter_eu",
                "sum",
            ),
            share_eu=(
                "share_eu",
                "sum",
            ),
        )
        .sort_values(
            "volume",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


    # =====================================================
    # EXPORTER TOTALS
    # =====================================================

    exporter_totals = (
        links.groupby(
            [
                "exporter_code",
                "exporter_name",
            ],
            as_index=False,
        )["volume"]
        .sum()
        .sort_values(
            "volume",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


    # =====================================================
    # IMPORTER TOTALS
    # =====================================================

    importer_totals = (
        links.groupby(
            [
                "importer_code",
                "importer_name",
            ],
            as_index=False,
        )["volume"]
        .sum()
        .sort_values(
            "volume",
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )


    # =====================================================
    # NODE IDS
    # =====================================================

    exporter_ids = [
        f"exp:{code}"
        for code
        in exporter_totals[
            "exporter_code"
        ]
    ]

    importer_ids = [
        f"imp:{code}"
        for code
        in importer_totals[
            "importer_code"
        ]
    ]

    node_ids = (
        exporter_ids
        + importer_ids
    )

    node_index = {
        node_id: i
        for i, node_id
        in enumerate(node_ids)
    }


    # =====================================================
    # NODE POSITIONS
    # =====================================================

    exporter_y = _stack_positions(
        exporter_totals[
            "volume"
        ].tolist(),
        gap=0.006,
    )

    importer_y = _stack_positions(
        importer_totals[
            "volume"
        ].tolist(),
        gap=0.010,
    )

    node_x = (
        [0.01]
        * len(exporter_totals)
        +
        [0.99]
        * len(importer_totals)
    )

    node_y = (
        exporter_y
        + importer_y
    )


    # =====================================================
    # NODE COLORS
    # =====================================================

    exporter_colors = [
        supplier_color(code)
        for code
        in exporter_totals[
            "exporter_code"
        ]
    ]

    node_colors = (
        exporter_colors
        +
        [NEUTRAL_IMPORTER]
        * len(importer_totals)
    )


    # =====================================================
    # NODE CUSTOMDATA
    #
    # 0 name
    # 1 code
    # 2 type
    # 3 volume
    # 4 role label
    # =====================================================

    node_customdata: list[list] = []

    for row in exporter_totals.itertuples():

        node_customdata.append(
            [
                row.exporter_name,
                row.exporter_code,
                "exporter",
                row.volume,
                "Поставщик",
            ]
        )

    for row in importer_totals.itertuples():

        node_customdata.append(
            [
                row.importer_name,
                row.importer_code,
                "importer",
                row.volume,
                "Страна ЕС",
            ]
        )


    # =====================================================
    # LINKS
    # =====================================================

    sources = [
        node_index[
            f"exp:{code}"
        ]
        for code
        in links["exporter_code"]
    ]

    targets = [
        node_index[
            f"imp:{code}"
        ]
        for code
        in links["importer_code"]
    ]

    values = (
        links[
            "volume"
        ].tolist()
    )

    link_colors = [
        rgba(
            supplier_color(code),
            0.62,
        )
        for code
        in links["exporter_code"]
    ]


    # =====================================================
    # LINK CUSTOMDATA
    #
    # 0 exporter name
    # 1 importer name
    # 2 exporter code
    # 3 importer code
    # 4 importer share
    # 5 exporter EU share
    # 6 EU share
    # 7 event marker
    # =====================================================

    link_customdata = links[
        [
            "exporter_name",
            "importer_name",
            "exporter_code",
            "importer_code",
            "share_importer",
            "share_exporter_eu",
            "share_eu",
        ]
    ].copy()

    link_customdata[
        "event_type"
    ] = "flow"

    link_customdata = (
        link_customdata
        .to_numpy()
    )


    # =====================================================
    # RELIABLE SIDE LABEL METADATA
    #
    # IMPORTANT:
    # We send country identity and Y position directly
    # to JavaScript.
    #
    # We do NOT try to infer country names from the
    # ordering of Plotly SVG nodes.
    # =====================================================

    visible_total = (
        links[
            "volume"
        ].sum()
    )

    label_meta = {
        "unit": unit,
        "exporters": [],
        "importers": [],
    }


    for i, row in exporter_totals.iterrows():

        if visible_total > 0:

            share = (
                row["volume"]
                / visible_total
                * 100
            )

        else:

            share = 0.0


        label_meta[
            "exporters"
        ].append(
            {
                "name":
                    row[
                        "exporter_name"
                    ],

                "code":
                    row[
                        "exporter_code"
                    ],

                "type":
                    "exporter",

                "volume":
                    float(
                        row["volume"]
                    ),

                "share":
                    float(share),

                "y":
                    float(
                        exporter_y[i]
                    ),

                "color":
                    supplier_color(
                        row[
                            "exporter_code"
                        ]
                    ),
            }
        )


    for i, row in importer_totals.iterrows():

        if visible_total > 0:

            share = (
                row["volume"]
                / visible_total
                * 100
            )

        else:

            share = 0.0


        label_meta[
            "importers"
        ].append(
            {
                "name":
                    row[
                        "importer_name"
                    ],

                "code":
                    row[
                        "importer_code"
                    ],

                "type":
                    "importer",

                "volume":
                    float(
                        row["volume"]
                    ),

                "share":
                    float(share),

                "y":
                    float(
                        importer_y[i]
                    ),

                "color":
                    NEUTRAL_IMPORTER,
            }
        )


    # =====================================================
    # FIGURE
    # =====================================================

    fig = go.Figure(
        go.Sankey(

            arrangement="fixed",

            valueformat=".3f",

            valuesuffix=(
                f" {unit}"
            ),

            node=dict(

                pad=7,

                thickness=16,

                line=dict(
                    color=(
                        NEUTRAL_BORDER
                    ),
                    width=0.6,
                ),

                # Labels are rendered
                # by sankey_click.py
                label=[
                    ""
                    for _
                    in node_ids
                ],

                x=node_x,

                y=node_y,

                color=node_colors,

                customdata=(
                    node_customdata
                ),

                hovertemplate=(
                    "<b>"
                    "%{customdata[0]}"
                    "</b>"
                    "<br>"
                    "%{customdata[4]}"
                    "<br>"
                    f"Объём: "
                    f"%{{customdata[3]:,.3f}} "
                    f"{unit}"
                    "<extra></extra>"
                ),
            ),

            link=dict(

                source=sources,

                target=targets,

                value=values,

                color=link_colors,

                customdata=(
                    link_customdata
                ),

                hovertemplate=(
                    "<b>"
                    "%{customdata[0]}"
                    " → "
                    "%{customdata[1]}"
                    "</b>"

                    "<br><br>"

                    f"Объём: "
                    f"%{{value:,.3f}} "
                    f"{unit}"

                    "<br>"

                    "Доля импорта страны: "
                    "%{customdata[4]:.2f}%"

                    "<br>"

                    "Доля поставок "
                    "экспортёра в ЕС: "
                    "%{customdata[5]:.2f}%"

                    "<br>"

                    "Доля импорта ЕС: "
                    "%{customdata[6]:.3f}%"

                    "<extra></extra>"
                ),
            ),
        )
    )


    # =====================================================
    # HEIGHT
    # =====================================================

    max_nodes = max(
        len(exporter_totals),
        len(importer_totals),
    )


    if max_nodes <= 10:

        height = 510

    elif max_nodes <= 15:

        height = 570

    elif max_nodes <= 25:

        height = 680

    elif max_nodes <= 40:

        height = 820

    else:

        height = min(
            1100,
            620
            + max_nodes * 12,
        )


    # =====================================================
    # LAYOUT
    # =====================================================

    fig.update_layout(

        # Used by our custom JS labels.
        meta={
            "sankey_labels":
                label_meta,
        },

        title=dict(
            text=title,
            x=0.0,
        ),

        font=dict(
            size=12,
            color="#111827",
        ),

        # Space for labels outside
        # the actual Sankey.
        margin=dict(
            l=250,
            r=260,
            t=38,
            b=18,
        ),

        height=height,

        paper_bgcolor="white",

        plot_bgcolor="white",

        hoverlabel=dict(
            bgcolor="white",
            bordercolor="#D1D5DB",
            font=dict(
                size=13,
                color="#111827",
            ),
        ),
    )

    return fig