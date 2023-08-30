import argparse
import datetime
import logging
import time
from config import load_config

from exchanges import exchange
import chart


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s",
)


def update(ex, args):
    # 获取图表实时数据
    df = chart.get_charting(args.symbol, args.timeframe, ex)
    df_display = chart.with_strategy(ex, args.strategy, df, args)
    # print(df_display)
    print(
        f"symbol: {args.symbol}, updated: {datetime.datetime.fromtimestamp(chart.data_updated)}, [{df.index[-1]} {df['close'][-1]}]"
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
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info("exbot starting ...")

    config = load_config(args.config)
    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    print(f"{ex.id()}, strategy: {args.strategy}")

    while True:
        try:
            update(ex, args)
        except Exception as e:
            logging.warning(f"An unknown error occurred in update(): {e}")
        time.sleep(args.interval)
