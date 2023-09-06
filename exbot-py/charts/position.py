import numpy as np
import pandas as pd
from dash import Dash, dcc, html
import plotly.graph_objects as go

data_update_interval = 10

if __name__ == "__main__":
    df = pd.read_csv(
        "data/position.csv",
        names=[
            "date",
            "ms",
            "symbol",
            "price",
            "short_qty",
            "short_entry_price",
            "short_realised",
            "short_upnl",
            "long_qty",
            "long_entry_price",
            "long_realised",
            "long_upnl",
        ],
        index_col=0,
    )
    print(df)
    fig = go.Figure()
    fig.layout.height = 760
    fig.layout.dragmode = "pan"
    # add -0.382 line
    for refline in [-0.236, -0.382, 0.618, 0.786, 1]:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=np.full(len(df), refline),
                mode="lines",
                line=dict(dash="dash", width=1),
                showlegend=False,
            )
        )

    for name, group in df.groupby("symbol"):
        fig.add_trace(
            go.Scatter(
                x=group.index,
                y=group["short_upnl"],
                mode="lines",
                name=name + "_short_upnl",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=group.index,
                y=group["long_upnl"],
                mode="lines",
                name=name + "_long_upnl",
            )
        )
    app = Dash()
    app.layout = html.Div([dcc.Graph(figure=fig)])

    app.run_server(debug=True, use_reloader=False)
