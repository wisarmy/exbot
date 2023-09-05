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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="exbot backtesting for python")
    parser.add_argument(
        "-c", "--config", type=str, required=True, help="config file path"
    )
    parser.add_argument(
        "--symbol", type=str, required=True, help="The trading symbol to use"
    )
    parser.add_argument("--strategy", type=str, default="", help="The strategy to use")
    parser.add_argument(
        "--days", type=int, default=7, help="download data for given number of days"
    )
    parser.add_argument(
        "-t",
        "--timeframe",
        type=str,
        required=True,
        help="timeframe: 1m 5m 15m 30m 1h 4h 1d 1w 1M",
    )
    # add arg verbose
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        pd.set_option("display.max_rows", None)

    logger.info("exbot backtesting ...")

    config = load_config(args.config)
    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    logger.info(f"exchange: {ex.id()}, args: {args}")
    # 获取图表实时数据
    df = chart.get_charting(ex, args.symbol, args.timeframe, args.days)
    df = with_strategy(args.strategy, ex, df, args, False)
    logger.info(df)
