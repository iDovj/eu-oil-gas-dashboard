from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go


# =========================================================
# HTML
# =========================================================

HTML = """
<div class="sankey-click-root">
    <div class="sankey-plot"></div>
    <div class="sankey-label-layer"></div>
</div>
"""


# =========================================================
# CSS
# =========================================================

CSS = """
.sankey-click-root {
    position: relative;
    width: 100%;
    min-width: 0;
    overflow: visible;
}

.sankey-plot {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
}

.sankey-label-layer {
    position: absolute;
    inset: 0;
    z-index: 10;
    pointer-events: none;
}

.sankey-side-label {
    position: absolute;

    pointer-events: auto;

    cursor: pointer;

    user-select: none;

    white-space: nowrap;

    max-width: 235px;

    overflow: hidden;

    text-overflow: ellipsis;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    line-height: 1.1;

    transition:
        opacity 120ms ease;
}

.sankey-side-label:hover {
    opacity: 0.62;
}

.sankey-country-name {
    color: #111827;
    font-weight: 650;
    font-size: 11px;
}

.sankey-country-stats {
    color: #6B7280;
    font-size: 10px;
    font-weight: 400;
}

.sankey-color-dot {
    display: inline-block;

    width: 7px;
    height: 7px;

    margin-right: 5px;

    border-radius: 1px;

    vertical-align: 1px;
}

.sankey-header {
    position: absolute;

    color: #111827;

    font-size: 11px;

    font-weight: 750;

    white-space: nowrap;
}

.sankey-header-left {
    transform:
        translateX(-100%);

    text-align: right;
}

.sankey-header-right {
    text-align: left;
}

.sankey-label-dense
.sankey-country-name {
    font-size: 10px;
}

.sankey-label-dense
.sankey-country-stats {
    font-size: 9px;
}

.sankey-label-very-dense
.sankey-country-name {
    font-size: 9px;
}

.sankey-label-very-dense
.sankey-country-stats {
    font-size: 8px;
}
"""


# =========================================================
# JAVASCRIPT
# =========================================================

JS = r"""
let plotlyPromise = null;


/* =======================================================
   LOAD PLOTLY
   ======================================================= */

function loadPlotly() {

    if (window.Plotly) {

        return Promise.resolve(
            window.Plotly
        );
    }


    if (plotlyPromise) {

        return plotlyPromise;
    }


    plotlyPromise =
        new Promise(
            (resolve, reject) => {

                const script =
                    document.createElement(
                        "script"
                    );


                script.src =
                    "https://cdn.plot.ly/plotly-3.1.0.min.js";


                script.onload =
                    () => resolve(
                        window.Plotly
                    );


                script.onerror =
                    () => reject(
                        new Error(
                            "Could not load Plotly.js"
                        )
                    );


                document.head.appendChild(
                    script
                );
            }
        );


    return plotlyPromise;
}


/* =======================================================
   HTML ESCAPING
   ======================================================= */

function escapeHtml(value) {

    const div =
        document.createElement(
            "div"
        );

    div.textContent =
        String(
            value ?? ""
        );

    return div.innerHTML;
}


/* =======================================================
   VOLUME FORMAT
   ======================================================= */

function formatVolume(value) {

    const number =
        Number(value);


    if (!Number.isFinite(number)) {
        return "";
    }


    let digits = 2;


    if (number >= 100) {
        digits = 1;
    }

    else if (number >= 10) {
        digits = 2;
    }

    else if (number >= 1) {
        digits = 2;
    }

    else if (number >= 0.1) {
        digits = 2;
    }

    else if (number >= 0.01) {
        digits = 3;
    }

    else {
        digits = 4;
    }


    return number.toLocaleString(
        "ru-RU",
        {
            minimumFractionDigits:
                digits,

            maximumFractionDigits:
                digits
        }
    );
}


/* =======================================================
   SHARE FORMAT
   ======================================================= */

function formatShare(value) {

    const number =
        Number(value);


    if (!Number.isFinite(number)) {
        return "";
    }


    if (
        number > 0
        &&
        number < 0.01
    ) {

        return "<0,01%";
    }


    if (number < 1) {

        return (
            number.toLocaleString(
                "ru-RU",
                {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                }
            )
            + "%"
        );
    }


    return (
        number.toLocaleString(
            "ru-RU",
            {
                minimumFractionDigits: 1,
                maximumFractionDigits: 1
            }
        )
        + "%"
    );
}


/* =======================================================
   COMPONENT
   ======================================================= */

export default function(component) {

    const {
        parentElement,
        data,
        setStateValue
    } = component;


    const root =
        parentElement.querySelector(
            ".sankey-click-root"
        );


    const plot =
        root.querySelector(
            ".sankey-plot"
        );


    const labelLayer =
        root.querySelector(
            ".sankey-label-layer"
        );


    const height =
        data.height ?? 700;


    root.style.height =
        `${height}px`;


    loadPlotly().then(
        (Plotly) => {


            const figure =
                JSON.parse(
                    data.figure_json
                );


            const config = {

                displaylogo: false,

                responsive: true,

                scrollZoom: false,

                displayModeBar: false
            };


            /* ===========================================
               SEND COUNTRY SELECTION TO STREAMLIT
               =========================================== */

            function emitCountry(
                type,
                name,
                code
            ) {

                setStateValue(
                    "selection",
                    {
                        kind:
                            "country",

                        type:
                            type,

                        name:
                            name,

                        code:
                            code,

                        event_id:
                            Date.now()
                    }
                );
            }


            /* ===========================================
               SPREAD SMALL LABELS
               =========================================== */

            function spreadLabels(
                items,
                topLimit,
                bottomLimit
            ) {

                if (
                    items.length === 0
                ) {

                    return [];
                }


                const available =
                    Math.max(
                        1,
                        bottomLimit
                        - topLimit
                    );


                let minGap = 21;


                if (items.length > 1) {

                    minGap =
                        Math.min(
                            21,
                            available
                            / (
                                items.length
                                - 1
                            )
                        );

                    minGap =
                        Math.max(
                            12,
                            minGap
                        );
                }


                const positioned =
                    items
                    .map(
                        (item) => ({
                            ...item,

                            desiredY:
                                item.pixelY,

                            displayY:
                                item.pixelY,
                        })
                    )
                    .sort(
                        (a, b) =>
                            a.desiredY
                            - b.desiredY
                    );


                positioned[0].displayY =
                    Math.max(
                        topLimit,
                        positioned[0]
                            .displayY
                    );


                for (
                    let i = 1;
                    i < positioned.length;
                    i++
                ) {

                    positioned[i].displayY =
                        Math.max(
                            positioned[i]
                                .displayY,

                            positioned[i - 1]
                                .displayY
                            + minGap
                        );
                }


                const overflow =
                    positioned[
                        positioned.length - 1
                    ].displayY
                    - bottomLimit;


                if (overflow > 0) {

                    for (
                        const item
                        of positioned
                    ) {

                        item.displayY -=
                            overflow;
                    }
                }


                for (
                    let i =
                        positioned.length - 2;

                    i >= 0;

                    i--
                ) {

                    positioned[i].displayY =
                        Math.min(
                            positioned[i]
                                .displayY,

                            positioned[i + 1]
                                .displayY
                            - minGap
                        );
                }


                const underflow =
                    topLimit
                    - positioned[0]
                        .displayY;


                if (underflow > 0) {

                    for (
                        const item
                        of positioned
                    ) {

                        item.displayY +=
                            underflow;
                    }
                }


                return positioned;
            }


            /* ===========================================
               LABELS
               =========================================== */

            function renderSideLabels() {

                labelLayer.innerHTML = "";


                const metadata =
                    figure
                    .layout
                    ?.meta
                    ?.sankey_labels;


                if (!metadata) {

                    return;
                }


                const exporters =
                    metadata.exporters
                    ?? [];


                const importers =
                    metadata.importers
                    ?? [];


                const unit =
                    metadata.unit
                    ?? "";


                const width =
                    root.clientWidth;


                const height =
                    root.clientHeight;


                const margin =
                    figure.layout.margin
                    ?? {};


                const marginLeft =
                    Number(
                        margin.l
                        ?? 250
                    );


                const marginRight =
                    Number(
                        margin.r
                        ?? 260
                    );


                const marginTop =
                    Number(
                        margin.t
                        ?? 38
                    );


                const marginBottom =
                    Number(
                        margin.b
                        ?? 18
                    );


                const plotHeight =
                    Math.max(
                        1,

                        height
                        - marginTop
                        - marginBottom
                    );


                const leftNodeX =
                    marginLeft;


                const rightNodeX =
                    width
                    - marginRight;


                function pixelY(item) {

                    return (
                        marginTop
                        +
                        Number(item.y)
                        * plotHeight
                    );
                }


                const exporterItems =
                    exporters.map(
                        (item) => ({
                            ...item,
                            pixelY:
                                pixelY(item)
                        })
                    );


                const importerItems =
                    importers.map(
                        (item) => ({
                            ...item,
                            pixelY:
                                pixelY(item)
                        })
                    );


                const topLimit =
                    marginTop + 10;


                const bottomLimit =
                    height
                    - marginBottom
                    - 10;


                const positionedExporters =
                    spreadLabels(
                        exporterItems,
                        topLimit,
                        bottomLimit
                    );


                const positionedImporters =
                    spreadLabels(
                        importerItems,
                        topLimit,
                        bottomLimit
                    );


                const maxCount =
                    Math.max(
                        exporters.length,
                        importers.length
                    );


                let densityClass = "";


                if (maxCount >= 35) {

                    densityClass =
                        " sankey-label-very-dense";
                }

                else if (maxCount >= 24) {

                    densityClass =
                        " sankey-label-dense";
                }


                function addLabel(item) {

                    const label =
                        document.createElement(
                            "div"
                        );


                    label.className =
                        "sankey-side-label"
                        + densityClass;


                    label.style.top =
                        `${item.displayY}px`;


                    if (
                        item.type
                        === "exporter"
                    ) {

                        label.style.left =
                            `${
                                leftNodeX - 14
                            }px`;


                        label.style.transform =
                            "translate(-100%, -50%)";


                        label.style.textAlign =
                            "right";
                    }

                    else {

                        label.style.left =
                            `${
                                rightNodeX + 14
                            }px`;


                        label.style.transform =
                            "translate(0, -50%)";


                        label.style.textAlign =
                            "left";
                    }


                    const dot =
                        item.type
                        === "exporter"

                        ? (
                            "<span "
                            + "class='sankey-color-dot' "
                            + "style='background:"
                            + escapeHtml(
                                item.color
                            )
                            + "'>"
                            + "</span>"
                        )

                        : "";


                    label.innerHTML =
                        "<span "
                        + "class='sankey-country-name'>"

                        + dot

                        + escapeHtml(
                            item.name
                        )

                        + "</span>"

                        + "<span "
                        + "class='sankey-country-stats'>"

                        + " · "

                        + formatVolume(
                            item.volume
                        )

                        + " "

                        + escapeHtml(
                            unit
                        )

                        + " · "

                        + formatShare(
                            item.share
                        )

                        + "</span>";


                    label.title =
                        item.name
                        + " — "
                        + formatVolume(
                            item.volume
                        )
                        + " "
                        + unit
                        + " — "
                        + formatShare(
                            item.share
                        )
                        + "\n"
                        + "Нажмите для фильтрации";


                    label.addEventListener(
                        "click",
                        (event) => {

                            event.preventDefault();

                            event.stopPropagation();


                            emitCountry(
                                item.type,
                                item.name,
                                item.code
                            );
                        }
                    );


                    labelLayer.appendChild(
                        label
                    );
                }


                positionedExporters.forEach(
                    addLabel
                );


                positionedImporters.forEach(
                    addLabel
                );


                /* =======================================
                   HEADERS
                   ======================================= */

                const leftHeader =
                    document.createElement(
                        "div"
                    );


                leftHeader.className =
                    "sankey-header "
                    + "sankey-header-left";


                leftHeader.textContent =
                    "СТРАНЫ-ПОСТАВЩИКИ";


                leftHeader.style.left =
                    `${
                        leftNodeX - 14
                    }px`;


                leftHeader.style.top =
                    "3px";


                labelLayer.appendChild(
                    leftHeader
                );


                const rightHeader =
                    document.createElement(
                        "div"
                    );


                rightHeader.className =
                    "sankey-header "
                    + "sankey-header-right";


                rightHeader.textContent =
                    "СТРАНЫ ЕС";


                rightHeader.style.left =
                    `${
                        rightNodeX + 14
                    }px`;


                rightHeader.style.top =
                    "3px";


                labelLayer.appendChild(
                    rightHeader
                );
            }


            /* ===========================================
               RENDER PLOT
               =========================================== */

            Plotly.react(
                plot,
                figure.data,
                figure.layout,
                config
            ).then(
                () => {

                    requestAnimationFrame(
                        renderSideLabels
                    );
                }
            );


            /* ===========================================
               REMOVE OLD CLICK HANDLERS
               =========================================== */

            if (
                typeof plot.removeAllListeners
                === "function"
            ) {

                plot.removeAllListeners(
                    "plotly_click"
                );
            }


            /* ===========================================
               PLOTLY CLICK
               =========================================== */

            plot.on(
                "plotly_click",
                (event) => {

                    if (
                        !event.points
                        ||
                        event.points.length === 0
                    ) {

                        return;
                    }


                    const point =
                        event.points[0];


                    const custom =
                        point.customdata;


                    /* ===================================
                       COUNTRY NODE
                       =================================== */

                    if (
                        Array.isArray(custom)
                        &&
                        custom.length >= 5
                        &&
                        (
                            custom[2]
                            === "exporter"

                            ||

                            custom[2]
                            === "importer"
                        )
                    ) {

                        emitCountry(
                            custom[2],
                            custom[0],
                            custom[1]
                        );


                        return;
                    }


                    /* ===================================
                       BILATERAL FLOW
                       =================================== */

                    if (
                        Array.isArray(custom)
                        &&
                        custom.length >= 8
                        &&
                        custom[7]
                        === "flow"
                    ) {

                        setStateValue(
                            "selection",
                            {
                                kind:
                                    "flow",

                                exporter_name:
                                    custom[0],

                                importer_name:
                                    custom[1],

                                exporter_code:
                                    custom[2],

                                importer_code:
                                    custom[3],

                                event_id:
                                    Date.now()
                            }
                        );
                    }
                }
            );


            /* ===========================================
               RESIZE
               =========================================== */

            if (
                root.__sankeyResizeObserver
            ) {

                root
                    .__sankeyResizeObserver
                    .disconnect();
            }


            const observer =
                new ResizeObserver(
                    () => {

                        Plotly.Plots.resize(
                            plot
                        );


                        requestAnimationFrame(
                            renderSideLabels
                        );
                    }
                );


            observer.observe(
                parentElement
            );


            root.__sankeyResizeObserver =
                observer;
        }
    );
}
"""


# =========================================================
# REGISTER COMPONENT
# =========================================================

_sankey_component = (
    st.components.v2.component(
        "eu_energy_sankey",
        html=HTML,
        css=CSS,
        js=JS,
    )
)


# =========================================================
# PYTHON WRAPPER
# =========================================================

def render_clickable_sankey(
    fig: go.Figure,
    *,
    key: str = "trade_sankey",
    on_selection_change=None,
):

    height = int(
        fig.layout.height
        or 700
    )


    result = _sankey_component(

        data={
            "figure_json":
                fig.to_json(),

            "height":
                height,
        },

        key=key,

        default={
            "selection":
                None,
        },

        on_selection_change=(
            on_selection_change
            or (lambda: None)
        ),
    )


    return result