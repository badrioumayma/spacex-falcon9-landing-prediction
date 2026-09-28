"""Interactive dashboard of SpaceX Falcon 9 launch outcomes by site and payload."""
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "spacex_launch_dash.csv"
ALL_SITES = "All Sites"

COLORS = {"Landed": "#16a34a", "Failed": "#dc2626"}
INK, MUTED, CARD_BG, PAGE_BG, ACCENT = "#0f172a", "#64748b", "#ffffff", "#f1f5f9", "#2563eb"
FONT = "Inter, 'Segoe UI', Roboto, sans-serif"

spacex_df = pd.read_csv(DATA_PATH)
spacex_df["Outcome"] = spacex_df["class"].map({1: "Landed", 0: "Failed"})
min_payload = spacex_df["Payload Mass (kg)"].min()
max_payload = spacex_df["Payload Mass (kg)"].max()

site_options = [{"label": ALL_SITES, "value": ALL_SITES}] + [
    {"label": site, "value": site} for site in sorted(spacex_df["Launch Site"].unique())
]

CARD = {
    "background": CARD_BG,
    "borderRadius": "14px",
    "padding": "20px",
    "boxShadow": "0 1px 3px rgba(15,23,42,.08), 0 4px 16px rgba(15,23,42,.04)",
}


def kpi(label, value_id):
    return html.Div(
        style={**CARD, "flex": "1 1 180px"},
        children=[
            html.Div(label, style={"color": MUTED, "fontSize": "13px", "textTransform": "uppercase",
                                   "letterSpacing": ".05em"}),
            html.Div(id=value_id, style={"color": INK, "fontSize": "30px", "fontWeight": 700, "marginTop": "6px"}),
        ],
    )


def chart_card(title, caption, graph_id):
    return html.Div(
        style={**CARD, "flex": "1 1 420px", "minWidth": 0},
        children=[
            html.H3(title, style={"margin": 0, "color": INK, "fontSize": "17px"}),
            html.P(caption, style={"margin": "4px 0 0", "color": MUTED, "fontSize": "14px"}),
            dcc.Graph(id=graph_id, config={"displayModeBar": False}, style={"height": "380px"}),
        ],
    )


app = Dash(__name__, title="SpaceX Launch Dashboard")
server = app.server

app.layout = html.Div(
    style={"background": PAGE_BG, "minHeight": "100vh", "fontFamily": FONT, "padding": "32px 16px"},
    children=html.Div(
        style={"maxWidth": "1200px", "margin": "0 auto", "display": "flex", "flexDirection": "column", "gap": "20px"},
        children=[
            html.Div([
                html.H1("🚀 SpaceX Falcon 9 Landing Dashboard",
                        style={"margin": 0, "color": INK, "fontSize": "30px"}),
                html.P("Did the first-stage booster land after launch? Explore 56 Falcon 9 launches (2010–2017) "
                       "by launch site and payload mass.",
                       style={"margin": "6px 0 0", "color": MUTED, "fontSize": "16px"}),
            ]),
            html.Div(
                style={**CARD, "display": "flex", "flexWrap": "wrap", "gap": "24px", "alignItems": "center"},
                children=[
                    html.Div(style={"flex": "1 1 260px"}, children=[
                        html.Label("Launch site", style={"fontWeight": 600, "color": INK, "fontSize": "14px"}),
                        dcc.Dropdown(id="site-dropdown", options=site_options, value=ALL_SITES,
                                     clearable=False, searchable=False, style={"marginTop": "6px"}),
                    ]),
                    html.Div(style={"flex": "2 1 420px"}, children=[
                        html.Label("Payload mass range (kg)", style={"fontWeight": 600, "color": INK, "fontSize": "14px"}),
                        dcc.RangeSlider(
                            id="payload-slider", min=0, max=10000, step=500,
                            marks={i: f"{i:,}" for i in range(0, 10001, 2500)},
                            value=[min_payload, max_payload],
                            tooltip={"placement": "bottom", "always_visible": False},
                        ),
                    ]),
                ],
            ),
            html.Div(
                style={"display": "flex", "flexWrap": "wrap", "gap": "20px"},
                children=[
                    kpi("Launches shown", "kpi-launches"),
                    kpi("Landing success rate", "kpi-rate"),
                    kpi("Successful landings", "kpi-landed"),
                    kpi("Average payload", "kpi-payload"),
                ],
            ),
            html.Div(
                style={"display": "flex", "flexWrap": "wrap", "gap": "20px"},
                children=[
                    chart_card("Success rate by launch site",
                               "Share of launches at each site whose booster landed. Longer bar = more reliable.",
                               "site-chart"),
                    chart_card("Payload vs. landing outcome",
                               "Each dot is one launch. Top row landed, bottom row failed. Colour = booster version.",
                               "success-payload-scatter-chart"),
                ],
            ),
            html.P("Data: IBM Applied Data Science Capstone · SpaceX API",
                   style={"color": MUTED, "fontSize": "13px", "textAlign": "center", "margin": 0}),
        ],
    ),
)


def style_figure(fig):
    fig.update_layout(
        template="plotly_white",
        font={"family": FONT, "color": INK},
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend={"orientation": "h", "y": -0.2, "title": None},
    )
    return fig


def filtered(site, payload_range):
    low, high = payload_range
    data = spacex_df[spacex_df["Payload Mass (kg)"].between(low, high)]
    return data if site == ALL_SITES else data[data["Launch Site"] == site]


@app.callback(
    Output("kpi-launches", "children"),
    Output("kpi-rate", "children"),
    Output("kpi-landed", "children"),
    Output("kpi-payload", "children"),
    Input("site-dropdown", "value"),
    Input("payload-slider", "value"),
)
def update_kpis(site, payload_range):
    data = filtered(site, payload_range)
    if data.empty:
        return "0", "–", "0", "–"
    return (
        f"{len(data)}",
        f"{data['class'].mean():.0%}",
        f"{int(data['class'].sum())}",
        f"{data['Payload Mass (kg)'].mean():,.0f} kg",
    )


@app.callback(
    Output("site-chart", "figure"),
    Input("site-dropdown", "value"),
    Input("payload-slider", "value"),
)
def update_site_chart(site, payload_range):
    data = filtered(ALL_SITES, payload_range)
    rates = (data.groupby("Launch Site")["class"].agg(rate="mean", launches="size")
             .reset_index().sort_values("rate"))
    rates["highlight"] = rates["Launch Site"].eq(site) | (site == ALL_SITES)
    fig = px.bar(
        rates, x="rate", y="Launch Site", orientation="h",
        text=rates["rate"].map("{:.0%}".format),
        custom_data=["launches"],
        color="highlight", color_discrete_map={True: ACCENT, False: "#cbd5e1"},
    )
    fig.update_traces(textposition="outside",
                      hovertemplate="%{y}<br>Success rate: %{x:.0%}<br>Launches: %{customdata[0]}<extra></extra>")
    fig.update_xaxes(range=[0, 1.1], tickformat=".0%", title=None, showgrid=True)
    fig.update_yaxes(title=None)
    return style_figure(fig).update_layout(showlegend=False)


@app.callback(
    Output("success-payload-scatter-chart", "figure"),
    Input("site-dropdown", "value"),
    Input("payload-slider", "value"),
)
def update_scatter_chart(site, payload_range):
    data = filtered(site, payload_range)
    fig = px.scatter(
        data,
        x="Payload Mass (kg)",
        y="Outcome",
        color="Booster Version Category",
        category_orders={"Outcome": ["Landed", "Failed"]},
        hover_data={"Launch Site": True, "Payload Mass (kg)": ":,", "Outcome": True},
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig.update_traces(marker={"size": 13, "opacity": 0.8, "line": {"width": 1, "color": "white"}})
    fig.update_yaxes(title=None)
    fig.update_xaxes(title="Payload mass (kg)", tickformat=",")
    return style_figure(fig)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
