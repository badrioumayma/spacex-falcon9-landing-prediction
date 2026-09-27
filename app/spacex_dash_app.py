"""Interactive dashboard of SpaceX Falcon 9 launch outcomes by site and payload."""
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "spacex_launch_dash.csv"
ALL_SITES = "All Sites"

spacex_df = pd.read_csv(DATA_PATH)
spacex_df["Outcome"] = spacex_df["class"].map({1: "Success", 0: "Failure"})
min_payload = spacex_df["Payload Mass (kg)"].min()
max_payload = spacex_df["Payload Mass (kg)"].max()

site_options = [{"label": ALL_SITES, "value": ALL_SITES}] + [
    {"label": site, "value": site} for site in sorted(spacex_df["Launch Site"].unique())
]

app = Dash(__name__, title="SpaceX Launch Dashboard")
server = app.server

app.layout = html.Div(
    style={"maxWidth": "1100px", "margin": "0 auto", "padding": "16px", "fontFamily": "sans-serif"},
    children=[
        html.H1("SpaceX Launch Records Dashboard", style={"textAlign": "center", "color": "#1f2d3d"}),
        html.P(
            "Falcon 9 first-stage landing outcomes by launch site and payload mass.",
            style={"textAlign": "center", "color": "#5a6b7b"},
        ),
        dcc.Dropdown(id="site-dropdown", options=site_options, value=ALL_SITES, clearable=False, searchable=True),
        dcc.Graph(id="success-pie-chart"),
        html.P("Payload range (kg):"),
        dcc.RangeSlider(
            id="payload-slider",
            min=0,
            max=10000,
            step=500,
            marks={i: f"{i} kg" for i in range(0, 10001, 2500)},
            value=[min_payload, max_payload],
        ),
        dcc.Graph(id="success-payload-scatter-chart"),
    ],
)


def filter_site(site):
    return spacex_df if site == ALL_SITES else spacex_df[spacex_df["Launch Site"] == site]


@app.callback(Output("success-pie-chart", "figure"), Input("site-dropdown", "value"))
def update_pie_chart(site):
    if site == ALL_SITES:
        return px.pie(
            spacex_df[spacex_df["class"] == 1],
            names="Launch Site",
            title="Share of successful landings by launch site",
        )
    return px.pie(
        filter_site(site),
        names="Outcome",
        color="Outcome",
        color_discrete_map={"Success": "#2ca02c", "Failure": "#d62728"},
        title=f"Landing outcomes at {site}",
    )


@app.callback(
    Output("success-payload-scatter-chart", "figure"),
    Input("site-dropdown", "value"),
    Input("payload-slider", "value"),
)
def update_scatter_chart(site, payload_range):
    low, high = payload_range
    data = filter_site(site)
    data = data[data["Payload Mass (kg)"].between(low, high)]
    return px.scatter(
        data,
        x="Payload Mass (kg)",
        y="class",
        color="Booster Version Category",
        hover_data=["Launch Site", "Outcome"],
        title=f"Payload vs. landing outcome ({site})",
        labels={"class": "Landing success (1 = yes)"},
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
