import argparse
import logging
from core.candle import get_candles
from core.logger import logger
from config import load_config
from exchanges import exchange

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="exbot for python")
    parser.add_argument(
        "-c", "--config", type=str, required=True, help="config file path"
    )
    parser.add_argument(
        "--symbol", type=str, required=True, help="The trading symbol to use"
    )
    parser.add_argument(
        "-t",
        "--timeframe",
        type=str,
        required=True,
        help="timeframe: 1m 5m 15m 30m 1h 4h 1d 1w 1M",
    )
    parser.add_argument(
        "--days", type=int, default=7, help="download data for given number of days"
    )
    # add arg verbose
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info(f"load config: {args.config}")
    config = load_config(args.config)

    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    get_candles(ex, args.symbol, args.timeframe, args.days)
