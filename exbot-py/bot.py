import argparse
import datetime
import logging
import time
from config import load_config
from core import chart
from exchanges import exchange
import pandas as pd
from core.logger import logger
from strategies.manager import with_strategy

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)


def update(ex, args):
    # 获取图表实时数据
    df = chart.get_charting(ex, args.symbol, args.timeframe)
    df = with_strategy(args.strategy, ex, df, args)
    logger.debug(df)
    logger.info(
        f"symbol: {args.symbol}, updated: {datetime.datetime.fromtimestamp(chart.data_updated)}, [{df.index[-1]} {df['close'].iloc[-1]}]"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="exbot for python")
    parser.add_argument(
        "-c", "--config", type=str, required=True, help="config file path"
    )
    parser.add_argument(
        "--symbol", type=str, required=True, help="The trading symbol to use"
    )
    parser.add_argument("--strategy", type=str, default="", help="The strategy to use")
    parser.add_argument(
        "--amount_type",
        type=str,
        default="quantity",
        choices=["quantity", "usdt"],
        help="The amount type to trade",
    )
    parser.add_argument(
        "--amount", type=float, default=1, help="The symbol amount to trade"
    )
    parser.add_argument(
        "--amount_max",
        type=float,
        default=1,
        help="The symbol amount max limit to trade",
    )
    parser.add_argument("--reversals", action="store_true", help="reversals")
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
    # add arg verbose
    parser.add_argument("-vv", "--verbose2", action="store_true", help="verbose mode")
    # add debug
    parser.add_argument("--debug", action="store_true", help="debug mode")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    if args.verbose2:
        logger.setLevel(logging.DEBUG)
        pd.set_option("display.max_rows", None)

    logger.info("exbot starting ...")

    config = load_config(args.config)
    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    logger.info(f"exchange: {ex.id()}, args: {args}")

    while True:
        try:
            update(ex, args)
        except Exception as e:
            logger.exception(f"An unknown error occurred in update(): {e}")
        time.sleep(args.interval)
