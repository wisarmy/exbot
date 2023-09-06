import argparse
import numpy as np
import pandas as pd
from dash import Dash, dcc, html, Output, Input
import plotly.graph_objects as go

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="exbot backtesting for python")
    # add arg verbose
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    args = parser.parse_args()

    df_symbols = pd.read_csv(
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
    symbols = df_symbols["symbol"].str.strip().unique()
    app = Dash()
    app.layout = html.Div(
        [
            dcc.Dropdown(
                id="symbol-dropdown",
                options=[{"label": s, "value": s} for s in symbols],
                value="NEAR/USDT:USDT",
            ),
            dcc.Graph(
                id="graph",
                config={
                    "scrollZoom": True,  # 启用或禁用滚动缩放
                },
            ),
        ]
    )

    @app.callback(Output("graph", "figure"), Input("symbol-dropdown", "value"))
    def update_graph(selected_symbol):
        global df_symbols
        df = df_symbols[df_symbols["symbol"].str.strip() == selected_symbol].copy()

        fig = go.Figure()
        fig.layout.height = 700
        fig.layout.dragmode = "pan"

        take_profit_urate = 0.00786
        stop_loss_urate = 0.00382
        # short
        df["short_take_profit_close_price"] = df["short_entry_price"] * (
            1 - take_profit_urate
        )
        df["short_stop_loss_close_price"] = df["short_entry_price"] * (
            1 + stop_loss_urate
        )
        # long
        df["long_take_profit_close_price"] = df["long_entry_price"] * (
            1 + take_profit_urate
        )
        df["long_stop_loss_close_price"] = df["long_entry_price"] * (
            1 - stop_loss_urate
        )

        df["take_profit_close_price"] = np.where(
            df["short_qty"] > 0,
            df["short_take_profit_close_price"],
            df["long_take_profit_close_price"],
        )
        df["stop_loss_close_price"] = np.where(
            df["short_qty"] > 0,
            df["short_stop_loss_close_price"],
            df["long_stop_loss_close_price"],
        )
        for name, group in df.groupby("symbol"):
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["price"],
                    mode="lines",
                    name=name + "_price",
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=group.index,
                    y=group["take_profit_close_price"],
                    mode="lines",
                    line=dict(dash="dash", width=1),
                    name=name + "_take_profit_close_price",
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=group.index,
                    y=group["stop_loss_close_price"],
                    mode="lines",
                    line=dict(dash="dash", width=1),
                    name=name + "_stop_loss_close_price",
                )
            )

        return fig

    app.run_server(debug=True, use_reloader=False)
