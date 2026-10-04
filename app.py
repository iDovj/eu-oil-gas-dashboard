from __future__ import annotations

import streamlit as st

from src.config import (
    PRODUCTS,
    YEAR_MAX,
    YEAR_MIN,
)

from src.data_loader import (
    load_trade_data,
)

from src.filters import (
    apply_selection,
    prepare_year_scope,
)

from src.metrics import (
    country_import_table,
    overview_metrics,
    supplier_destination_table,
)

from src.sankey import (
    build_sankey,
)

from src.sankey_click import (
    render_clickable_sankey,
)


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title=(
        "EU Oil & Gas Trade Explorer"
    ),
    page_icon="🌍",
    layout="wide",
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1850px;
        padding-top: 0.45rem;
        padding-bottom: 2rem;
    }

    section[data-testid="stSidebar"] {
        width: 310px !important;
    }

    h1 {
        margin-top: 0;
        margin-bottom: 0;
        font-size: 2.25rem !important;
    }

    h2,
    h3 {
        margin-top: 0.3rem;
        margin-bottom: 0.25rem;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.55rem;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 0.82rem;
    }

    div[data-testid="stMetric"] {
        padding-top: 0.15rem;
        padding-bottom: 0.15rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SESSION STATE
# =========================================================

if "year" not in st.session_state:

    st.session_state.year = (
        YEAR_MAX
    )


if (
    "importer_filter"
    not in st.session_state
):

    st.session_state.importer_filter = (
        "Все страны ЕС"
    )


if (
    "exporter_filter"
    not in st.session_state
):

    st.session_state.exporter_filter = (
        "Все поставщики"
    )


if (
    "commodity_filter"
    not in st.session_state
):

    st.session_state.commodity_filter = (
        "Нефть"
    )


# =========================================================
# CALLBACKS
# =========================================================

def previous_year():

    st.session_state.year = max(
        YEAR_MIN,
        st.session_state.year - 1,
    )


def next_year():

    st.session_state.year = min(
        YEAR_MAX,
        st.session_state.year + 1,
    )


def reset_focus():

    st.session_state.importer_filter = (
        "Все страны ЕС"
    )

    st.session_state.exporter_filter = (
        "Все поставщики"
    )


def handle_sankey_selection():

    component_state = (
        st.session_state.get(
            "trade_sankey"
        )
    )


    if component_state is None:

        return


    if isinstance(
        component_state,
        dict,
    ):

        selection = (
            component_state.get(
                "selection"
            )
        )

    else:

        selection = getattr(
            component_state,
            "selection",
            None,
        )


    if not selection:

        return


    kind = selection.get(
        "kind"
    )


    # -----------------------------------------------------
    # COUNTRY
    # -----------------------------------------------------

    if kind == "country":

        country_type = (
            selection.get(
                "type"
            )
        )

        country_name = (
            selection.get(
                "name"
            )
        )


        if not country_name:

            return


        if country_type == "importer":

            st.session_state[
                "importer_filter"
            ] = country_name


            st.session_state[
                "exporter_filter"
            ] = "Все поставщики"


        elif country_type == "exporter":

            st.session_state[
                "exporter_filter"
            ] = country_name


            st.session_state[
                "importer_filter"
            ] = "Все страны ЕС"


    # -----------------------------------------------------
    # FLOW
    # -----------------------------------------------------

    elif kind == "flow":

        exporter_name = (
            selection.get(
                "exporter_name"
            )
        )

        importer_name = (
            selection.get(
                "importer_name"
            )
        )


        if exporter_name:

            st.session_state[
                "exporter_filter"
            ] = exporter_name


        if importer_name:

            st.session_state[
                "importer_filter"
            ] = importer_name


# =========================================================
# COMPACT HEADER
# =========================================================

header_left, header_right = (
    st.columns(
        [4.3, 1.15],
        vertical_alignment="bottom",
    )
)


with header_left:

    st.title(
        "EU Oil & Gas Trade Explorer"
    )

    st.caption(
        "Страна происхождения → "
        "страна-импортёр EU-27 · "
        "Eurostat · 2000–2024"
    )


with header_right:

    commodity = (
        st.segmented_control(
            "Товар",
            options=[
                "Нефть",
                "Газ",
            ],
            key="commodity_filter",
            selection_mode="single",
            label_visibility="collapsed",
        )
    )


if commodity is None:

    commodity = "Нефть"


# =========================================================
# LOAD DATA
# =========================================================

try:

    df = load_trade_data(
        commodity
    )

except FileNotFoundError as exc:

    st.error(
        str(exc)
    )

    st.code(
        "pip install -r requirements.txt\n"
        "python scripts/fetch_eurostat.py\n"
        "streamlit run app.py",
        language="bash",
    )

    st.stop()


# =========================================================
# COMPACT YEAR CONTROL
# =========================================================

year_left, year_slider, year_right = (
    st.columns(
        [0.45, 8.5, 0.45],
        vertical_alignment="center",
    )
)


with year_left:

    st.button(
        "◀",
        key="year_previous",
        on_click=previous_year,
        disabled=(
            st.session_state.year
            <= YEAR_MIN
        ),
        use_container_width=True,
    )


with year_slider:

    st.slider(
        "Год",
        min_value=YEAR_MIN,
        max_value=YEAR_MAX,
        step=1,
        key="year",
        label_visibility="collapsed",
    )


with year_right:

    st.button(
        "▶",
        key="year_next",
        on_click=next_year,
        disabled=(
            st.session_state.year
            >= YEAR_MAX
        ),
        use_container_width=True,
    )


year = (
    st.session_state.year
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header(
        "Фильтры"
    )


    scope = st.radio(
        "Происхождение поставок",
        options=[
            "Только вне ЕС",
            "Все страны",
        ],
        index=0,
    )


    extra_eu_only = (
        scope
        == "Только вне ЕС"
    )


    # -----------------------------------------------------
    # CURRENT YEAR DATA
    # -----------------------------------------------------

    base = prepare_year_scope(
        df,
        year,
        extra_eu_only=(
            extra_eu_only
        ),
    )


    # -----------------------------------------------------
    # IMPORTERS
    # -----------------------------------------------------

    importer_lookup = (
        base[
            [
                "importer_code",
                "importer_name",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            "importer_name"
        )
    )


    importer_options = (
        [
            "Все страны ЕС"
        ]
        +
        importer_lookup[
            "importer_name"
        ].tolist()
    )


    if (
        st.session_state.importer_filter
        not in importer_options
    ):

        st.session_state.importer_filter = (
            "Все страны ЕС"
        )


    importer_name = (
        st.selectbox(
            "Страна ЕС",
            options=(
                importer_options
            ),
            key="importer_filter",
        )
    )


    importer_code = None


    if (
        importer_name
        != "Все страны ЕС"
    ):

        match = (
            importer_lookup.loc[
                importer_lookup[
                    "importer_name"
                ].eq(
                    importer_name
                )
            ]
        )


        if not match.empty:

            importer_code = (
                match[
                    "importer_code"
                ].iloc[0]
            )


    # -----------------------------------------------------
    # EXPORTERS
    # -----------------------------------------------------

    exporter_lookup = (
        base[
            [
                "exporter_code",
                "exporter_name",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            "exporter_name"
        )
    )


    exporter_options = (
        [
            "Все поставщики"
        ]
        +
        exporter_lookup[
            "exporter_name"
        ].tolist()
    )


    if (
        st.session_state.exporter_filter
        not in exporter_options
    ):

        st.session_state.exporter_filter = (
            "Все поставщики"
        )


    exporter_name = (
        st.selectbox(
            "Поставщик",
            options=(
                exporter_options
            ),
            key="exporter_filter",
        )
    )


    exporter_code = None


    if (
        exporter_name
        != "Все поставщики"
    ):

        match = (
            exporter_lookup.loc[
                exporter_lookup[
                    "exporter_name"
                ].eq(
                    exporter_name
                )
            ]
        )


        if not match.empty:

            exporter_code = (
                match[
                    "exporter_code"
                ].iloc[0]
            )


    # -----------------------------------------------------
    # RESET
    # -----------------------------------------------------

    if (
        importer_code is not None
        or exporter_code is not None
    ):

        st.button(
            "← Вернуться к EU-27",
            on_click=reset_focus,
            use_container_width=True,
        )


    st.divider()


    # -----------------------------------------------------
    # FLOW FILTER
    # -----------------------------------------------------

    min_share = st.slider(
        "Минимальная доля поставщика "
        "в импорте страны, %",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.1,
        help=(
            "Скрывает мелкие потоки "
            "только на диаграмме. "
            "KPI и таблицы остаются "
            "основаны на полных данных."
        ),
    )


# =========================================================
# FILTER DATA
# =========================================================

detail_scope = apply_selection(
    base,
    importer_code=(
        importer_code
    ),
    exporter_code=(
        exporter_code
    ),
    min_importer_share=0.0,
)


filtered = apply_selection(
    base,
    importer_code=(
        importer_code
    ),
    exporter_code=(
        exporter_code
    ),
    min_importer_share=(
        min_share
    ),
)


# =========================================================
# PRODUCT METADATA
# =========================================================

meta = PRODUCTS[
    commodity
]


# =========================================================
# CALCULATE KPI
# =========================================================

metrics = overview_metrics(
    detail_scope
)


total_volume = (
    metrics["total"]
)


if (
    importer_code
    and not exporter_code
):

    total_label = (
        f"Импорт: "
        f"{importer_name}"
    )


elif (
    exporter_code
    and not importer_code
):

    total_label = (
        f"Поставки: "
        f"{exporter_name}"
    )


elif (
    importer_code
    and exporter_code
):

    total_label = (
        "Двусторонний поток"
    )


else:

    total_label = (
        "Импорт EU-27"
    )


# =========================================================
# TOP DESTINATION
# =========================================================

top_destination = "—"

top_destination_share = 0.0


if (
    exporter_code
    and not detail_scope.empty
):

    destinations = (
        detail_scope
        .groupby(
            "importer_name",
            as_index=False,
        )["volume"]
        .sum()
        .sort_values(
            "volume",
            ascending=False,
        )
    )


    if not destinations.empty:

        top_destination = (
            destinations.iloc[0][
                "importer_name"
            ]
        )


        destination_total = (
            destinations[
                "volume"
            ].sum()
        )


        if destination_total > 0:

            top_destination_share = (
                destinations.iloc[0][
                    "volume"
                ]
                / destination_total
                * 100
            )


# =========================================================
# FOCUS TITLE
# =========================================================

if (
    importer_code
    and exporter_code
):

    focus_text = (
        f"{exporter_name}"
        f" → "
        f"{importer_name}"
    )


elif importer_code:

    focus_text = (
        f"все поставщики"
        f" → "
        f"{importer_name}"
    )


elif exporter_code:

    focus_text = (
        f"{exporter_name}"
        f" → "
        f"EU-27"
    )


else:

    focus_text = (
        "все поставщики"
        " → "
        "EU-27"
    )


st.subheader(
    f"{meta['title']}: "
    f"{year} — "
    f"{focus_text}"
)


st.caption(
    "Цвет = страна-поставщик · "
    "ширина = физический объём · "
    "нажмите на страну или поток для фильтрации."
)


# =========================================================
# SANKEY
# =========================================================

if filtered.empty:

    st.warning(
        "Для выбранных фильтров "
        "нет потоков."
    )


else:

    fig = build_sankey(
        filtered,
        title="",
        unit=(
            meta["unit"]
        ),
    )


    render_clickable_sankey(
        fig,
        key="trade_sankey",
        on_selection_change=(
            handle_sankey_selection
        ),
    )


    if min_share > 0:

        hidden_count = (
            len(detail_scope)
            - len(filtered)
        )


        st.caption(
            f"Скрыто мелких потоков: "
            f"{hidden_count:,}. "
            f"KPI и таблицы считаются "
            f"по полному набору."
        )


# =========================================================
# KPI — NOW BELOW THE SANKEY
# =========================================================

m1, m2, m3, m4 = (
    st.columns(4)
)


m1.metric(
    total_label,
    f"{total_volume:,.1f} "
    f"{meta['unit']}",
)


m2.metric(
    "Стран-импортёров",
    metrics["importers"],
)


m3.metric(
    "Стран-поставщиков",
    metrics["exporters"],
)


if exporter_code:

    m4.metric(
        "Главный рынок",
        top_destination,
        (
            f"{top_destination_share:.1f}%"
        ),
    )


else:

    m4.metric(
        "Крупнейший поставщик",
        metrics[
            "top_supplier"
        ],
        (
            f"{metrics['top_supplier_share']:.1f}%"
        ),
    )


# =========================================================
# TABLES
# =========================================================

st.divider()


# ---------------------------------------------------------
# IMPORTER
# ---------------------------------------------------------

if (
    importer_code
    and not exporter_code
):

    st.subheader(
        f"Поставщики "
        f"{importer_name} · "
        f"{year}"
    )


    table = country_import_table(
        base,
        importer_code,
    )


    table = table.rename(
        columns={
            "exporter_name":
                "Поставщик",

            "volume":
                f"Объём, "
                f"{meta['unit']}",

            "share_importer":
                "Доля импорта страны, %",

            "share_exporter_eu":
                "Доля поставок экспортёра "
                "в ЕС, %",

            "share_eu":
                "Доля импорта ЕС, %",
        }
    )


    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# EXPORTER
# ---------------------------------------------------------

elif (
    exporter_code
    and not importer_code
):

    st.subheader(
        f"Поставки "
        f"{exporter_name} "
        f"в ЕС · "
        f"{year}"
    )


    table = (
        supplier_destination_table(
            base,
            exporter_code,
        )
    )


    table = table.rename(
        columns={
            "importer_name":
                "Страна ЕС",

            "volume":
                f"Объём, "
                f"{meta['unit']}",

            "share_importer":
                "Доля импорта страны, %",

            "share_exporter_eu":
                "Доля поставок экспортёра "
                "в ЕС, %",

            "share_eu":
                "Доля импорта ЕС, %",
        }
    )


    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# BILATERAL
# ---------------------------------------------------------

elif (
    importer_code
    and exporter_code
):

    st.subheader(
        f"{exporter_name}"
        f" → "
        f"{importer_name}"
        f" · "
        f"{year}"
    )


    bilateral = (
        detail_scope[
            [
                "exporter_name",
                "importer_name",
                "volume",
                "share_importer",
                "share_exporter_eu",
                "share_eu",
            ]
        ]
        .copy()
    )


    bilateral = (
        bilateral.rename(
            columns={
                "exporter_name":
                    "Поставщик",

                "importer_name":
                    "Страна ЕС",

                "volume":
                    f"Объём, "
                    f"{meta['unit']}",

                "share_importer":
                    "Доля импорта страны, %",

                "share_exporter_eu":
                    "Доля поставок экспортёра "
                    "в ЕС, %",

                "share_eu":
                    "Доля импорта ЕС, %",
            }
        )
    )


    st.dataframe(
        bilateral,
        use_container_width=True,
        hide_index=True,
    )


# ---------------------------------------------------------
# EU OVERVIEW
# ---------------------------------------------------------

else:

    st.subheader(
        f"Крупнейшие потоки "
        f"EU-27 · {year}"
    )


    overview = (
        base[
            [
                "exporter_name",
                "importer_name",
                "volume",
                "share_importer",
                "share_eu",
            ]
        ]
        .sort_values(
            "volume",
            ascending=False,
        )
        .head(100)
        .rename(
            columns={
                "exporter_name":
                    "Поставщик",

                "importer_name":
                    "Страна ЕС",

                "volume":
                    f"Объём, "
                    f"{meta['unit']}",

                "share_importer":
                    "Доля импорта страны, %",

                "share_eu":
                    "Доля импорта ЕС, %",
            }
        )
    )


    st.dataframe(
        overview,
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# FOOTER
# =========================================================

st.caption(
    "Источник: Eurostat — "
    "nrg_ti_oil / nrg_ti_gas. "
    "Для 2000–2024 используется "
    "постоянный состав нынешнего EU-27."
)