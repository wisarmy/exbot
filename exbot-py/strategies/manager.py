import os
from core import chart
from strategies import ichiv1, macd, strategy
from core.logger import logger
import plotly.graph_objects as go
from typing import Dict

from strategies.istrategy import IStrategy

TAKE_PROFIT = os.getenv("TAKE_PROFIT", "false") == "true"
STOP_LOSS = os.getenv("STOP_LOSS", "false") == "true"
REVERSALS = os.getenv("REVERSALS", "false") == "true"

strategys: Dict[str, IStrategy] = {
    "macd": macd.macd(),
    "ichiv1": ichiv1.ichiv1(),
}


def with_strategy(strategy_name, ex, df, args):
    """
    :param strategy_name: strategy name
    :param ex: exchange
    :param df: ohlcv dataframe
    :param args:
        symbol: symbol
        amount_type: amount_type
        amount: amount
        amount_max_limit: amount max limit
        reversals: reversals
    :param fig: chart fig
    :return: dataframe
    """
    if strategy_name not in strategys:
        raise ValueError(f"Invalid strategy name: {strategy_name}")
    stgy = strategys[strategy_name]
    df = stgy.run(df, ex, args)
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
