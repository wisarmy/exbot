import argparse
from datetime import timedelta
import datetime
import logging
import pandas as pd
from config import load_config
from core import chart
from exchanges import exchange
from dash import Dash, State, dcc, html, Input, Output
from plotly.subplots import make_subplots
from core.logger import logger
from strategies.manager import with_figure

data_update_interval = 10

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="exbot for python")
    parser.add_argument(
        "-c", "--config", type=str, required=True, help="config file path"
    )
    parser.add_argument(
        "--symbol", type=str, required=True, help="The trading symbol to use"
    )
    parser.add_argument(
        "--strategy", type=str, default=None, help="The strategy to use"
    )
    parser.add_argument(
        "--amount", type=float, default=1, help="The symbol amount to trade"
    )
    parser.add_argument(
        "--amount_max_limit",
        type=float,
        default=1,
        help="The symbol amount max limit to trade",
    )
    parser.add_argument(
        "-t",
        "--timeframe",
        type=str,
        required=True,
        help="timeframe: 1m 5m 15m 30m 1h 4h 1d 1w 1M",
    )
    # add arg interval
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=10,
        help="data update interval seconds < timeframes interval",
    )
    # add arg verbose
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        pd.set_option("display.max_rows", None)

    logger.info("exbot charting ...")

    config = load_config(args.config)
    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    print(f"{ex.id()}, strategy: {args.strategy}")

    app = Dash(__name__, title=args.symbol)
    data_update_interval = args.interval
    app.layout = html.Div(
        [
            dcc.Interval(
                id="update", interval=data_update_interval * 1000, n_intervals=0
            ),
            dcc.Graph(
                id="graph",
                config={
                    "scrollZoom": True,  # 启用或禁用滚动缩放
                },
            ),
        ]
    )

    @app.callback(
        Output("graph", "figure"),
        Input("update", "n_intervals"),
        Input("graph", "clickData"),
        # Input('graph', 'hoverData'),
        State("graph", "relayoutData"),
    )
    def update_graph(n, click_data, relayout_data):
        symbol = args.symbol

        # 获取图表实时数据
        df = chart.get_charting(ex, symbol, args.timeframe)
        print(
            f"symbol: {symbol}, updated: {datetime.datetime.fromtimestamp(chart.data_updated)}, [{df.index[-1]} {df['close'].iloc[-1]}]"
        )
        # 组合图表
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.005,
            row_heights=[0.7, 0.3],
        )
        # 绘制蜡烛图
        fig_candle = chart.draw_fig_candle(df)
        # 加载策略
        df_display = with_figure(args.strategy, ex, df, fig_candle, args)
        # print(df_display)

        for trace in fig_candle.data:
            fig.add_trace(trace, row=1, col=1)
        for shape in fig_candle.layout.shapes:
            fig.add_shape(shape, row=1, col=1)
        for annotation in fig_candle.layout.annotations:
            fig.add_annotation(annotation)
        # 绘制MACD指标
        fig_macd, macd_yaxis_range = chart.draw_fig_macd(df)
        try:
            fig.add_trace(fig_macd.data[0], row=2, col=1)
            fig.add_trace(fig_macd.data[1], row=2, col=1)
            fig.add_trace(fig_macd.data[2], row=2, col=1)
        except IndexError:
            pass
        # 绘制鼠标位置垂直线
        chart.draw_fig_with_click_data(fig, click_data, df_display, macd_yaxis_range)
        # draw_fig_with_hover_data(fig, hover_data, df_display, macd_yaxis_range)
        # 绘制 EMA
        chart.draw_fig_emas(fig, df, [9, 22])

        fig.update_layout(
            height=860,
            title=symbol,
            xaxis=dict(
                rangeslider=dict(visible=False),
                range=[
                    df_display.index[0],
                    df_display.index[-1] + timedelta(minutes=60),
                ],
            ),
            yaxis=dict(
                side="right",
                range=[
                    df_display["low"].min() * 0.999,
                    df_display["high"].max() * 1.001,
                ],
            ),
            yaxis2=dict(
                title="MACD",
                side="right",
                range=macd_yaxis_range["range"],
            ),
            dragmode="pan",
        )
        # 设定图表到上次的位置
        chart.fig_relayout(fig, relayout_data)

        return fig

    app.run_server(debug=True)
