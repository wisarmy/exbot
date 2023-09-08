import os
from core import chart
from strategies import ichiv1, macd, strategy
from core.logger import logger
import plotly.graph_objects as go


def with_strategy(strategy_name, ex, df, args, trade=True):
    """
    :param strategy_name: strategy name
    :param ex: exchange
    :param df: ohlcv dataframe
    :param args:
        symbol: symbol
        amount: amount
        amount_max_limit: amount max limit
        timeframe: timeframe
    :param fig: chart fig
    :return: dataframe
    """
    match strategy_name:
        case "macd":
            stgy = macd.macd()
            df = stgy.populate_indicators(df)

            df = stgy.populate_buy_trend(df)
            df = stgy.populate_sell_trend(df)
            df = stgy.populate_close_position(
                df,
                os.getenv("TAKE_PROFIT", "false") == "true",
                os.getenv("STOP_LOSS", "true") == "true",
            )
            if trade:
                side = strategy.amount_limit(
                    ex, df, args.symbol, args.amount, args.amount_max_limit
                )
        case "ichiv1":
            stgy = ichiv1.ichiv1()
            df = stgy.populate_indicators(df)

            df = stgy.populate_buy_trend(df)
            df = stgy.populate_sell_trend(df)
            if trade:
                side = strategy.amount_limit(
                    ex, df, args.symbol, args.amount, args.amount_max_limit
                )
        case _:
            logger.warning(f"strategy {strategy_name} not found")

    return df


def with_figure(strategy_name, ex, df, fig: go.Figure, args):
    df = df.tail(chart.chart_display_size)
    if fig is not None:
        match strategy_name:
            case "macd":
                stgy = macd.macd()
                # 获取多 timeframe 的数据
                dfs = {}
                timeframes = ["1m", "5m"]
                for timeframe in timeframes:
                    if args.timeframe != timeframe:
                        dfs[timeframe] = chart.get_charting(
                            ex, args.symbol, timeframe
                        ).tail(chart.chart_display_size)
                        dfs[timeframe] = stgy.populate_indicators(dfs[timeframe])
                    else:
                        df = stgy.populate_indicators(df)
                        dfs[timeframe] = df
                # 绘制交易信号
                display_yaxis_max = df["high"].max()
                display_yaxis_min = df["low"].min()
                display_yaxis_span = display_yaxis_max - display_yaxis_min
                for timeframe in reversed(timeframes):
                    fig = chart.draw_fig_cross_bg(
                        fig,
                        dfs[timeframe],
                        [
                            display_yaxis_max - 0.1 * display_yaxis_span,
                            display_yaxis_max,
                        ],
                    )
                    display_yaxis_max = display_yaxis_max - 0.1 * display_yaxis_span
    else:
        logger.debug("fig is None")

    return df
