import argparse
import numpy as np
import pandas as pd
from dash import Dash, dcc, html, Output, Input
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def fig_position_upnl(df):
    fig = go.Figure()
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
    return fig


def fig_position_price(df):
    fig = go.Figure()
    take_profit_urate = 0.00786
    stop_loss_urate = 0.00382
    # short
    df["short_take_profit_close_price"] = df["short_entry_price"] * (
        1 - take_profit_urate
    )
    df["short_stop_loss_close_price"] = df["short_entry_price"] * (1 + stop_loss_urate)
    # long
    df["long_take_profit_close_price"] = df["long_entry_price"] * (
        1 + take_profit_urate
    )
    df["long_stop_loss_close_price"] = df["long_entry_price"] * (1 - stop_loss_urate)

    df["entry_price"] = np.where(
        df["short_qty"] > 0,
        df["short_entry_price"],
        df["long_entry_price"],
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
                x=df.index,
                y=df["entry_price"],
                mode="lines",
                line=dict(dash="dash", color="grey", width=1),
                name=name + "_entry_price",
            )
        )
        fig.add_annotation(
            xref="paper",
            yref="y",
            x=1.052,
            y=df["entry_price"].iloc[-1],
            text="{:.5f}".format(df["entry_price"].iloc[-1]),
            showarrow=False,
            font=dict(
                size=12,
                color="White",
            ),
            bgcolor="grey",
            bordercolor="grey",
            borderwidth=1,
        )

        fig.add_trace(
            go.Scatter(
                x=group.index,
                y=group["take_profit_close_price"],
                mode="lines",
                line=dict(dash="dash", color="green", width=1),
                name=name + "_take_profit_close_price",
            )
        )
        fig.add_annotation(
            xref="paper",
            yref="y",
            x=1.052,
            y=df["take_profit_close_price"].iloc[-1],
            text="{:.5f}".format(df["take_profit_close_price"].iloc[-1]),
            showarrow=False,
            font=dict(
                size=12,
                color="White",
            ),
            bgcolor="green",
            bordercolor="green",
            borderwidth=1,
        )
        fig.add_trace(
            go.Scatter(
                x=group.index,
                y=group["stop_loss_close_price"],
                mode="lines",
                line=dict(dash="dash", color="red", width=1),
                name=name + "_stop_loss_close_price",
            )
        )
        fig.add_annotation(
            xref="paper",
            yref="y",
            x=1.052,
            y=df["stop_loss_close_price"].iloc[-1],
            text="{:.5f}".format(df["stop_loss_close_price"].iloc[-1]),
            showarrow=False,
            font=dict(
                size=12,
                color="White",
            ),
            bgcolor="red",
            bordercolor="red",
            borderwidth=1,
        )

    return fig


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
                id="graph1",
                config={
                    "scrollZoom": True,  # 启用或禁用滚动缩放
                },
            ),
            dcc.Graph(
                id="graph2",
                config={
                    "scrollZoom": True,  # 启用或禁用滚动缩放
                },
            ),
        ]
    )

    @app.callback(
        [Output("graph1", "figure"), Output("graph2", "figure")],
        Input("symbol-dropdown", "value"),
    )
    def update_graph(symbol):
        global df_symbols
        df = df_symbols[df_symbols["symbol"].str.strip() == symbol].copy()
        fig_upnl = fig_position_upnl(df)
        fig_price = fig_position_price(df)
        fig_upnl.update_layout(
            height=500,
            dragmode="pan",
        )
        fig_price.update_layout(
            height=500,
            dragmode="pan",
        )
        return fig_price, fig_upnl

    app.run_server(debug=True, use_reloader=False)
