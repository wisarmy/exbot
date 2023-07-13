import argparse
import logging
from typing import List, Any
from config import load_config
import json
import os
import datetime

from exchanges import exchange

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='exbot for python')
    parser.add_argument('-c', '--config', type=str, required=True, help='config file path')
    parser.add_argument('--symbol', type=str, required=True, help='The trading symbol to use')
    parser.add_argument('-t', '--timeframe', type=str, required=True, help='timeframe: 1m 5m 15m 30m 1h 4h 1d 1w 1M')
    parser.add_argument('--days', type=int, default=7, help='download data for given number of days')
    # add arg verbose
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info(f"load config: {args.config}")
    config = load_config(args.config)

    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()

    rootpath = os.getcwd()
    candles_path = os.path.join(rootpath, 'data', str(ex.id()), f"{args.symbol.replace('/','_')}_{args.timeframe}.json")
    # days to since 
    args.since = ex.exchange.milliseconds() - args.days * 24 * 60 * 60 * 1000

    # declare candles
    candles: List[Any] = []
    if not os.path.exists(candles_path):
        logging.info(f"download data to {candles_path}")
        os.makedirs(os.path.dirname(candles_path), exist_ok=True)
        candles = ex.get_all_candles(args.symbol, args.timeframe, since=args.since)
        with open(candles_path, 'w') as f:
            json.dump(candles, f)
        exit(0)
    else:
        logging.info(f"load data from {candles_path}")
        with open(candles_path, 'r') as f:
            candles = json.load(f)

    if candles:
        exist_start = candles[0][0]
        exist_end = candles[-1][0]
        if args.since < exist_start:
            # redownload all data
            # TODO download only missing data
            since = args.since
            candles = []
        else:
            # calculate since, +1 to avoid duplicate data
            since = exist_end + 1
    else:
        since = args.since

    logging.info(f"downloading new data for [{args.symbol} {args.timeframe}] from {datetime.datetime.fromtimestamp(since/1000).strftime('%Y-%m-%d %H:%M:%S')}")

    new_candles = ex.get_all_candles(args.symbol, args.timeframe, since=since)
    
    if len(new_candles) > 0:
        candles.extend(new_candles)
        with open(candles_path, 'w') as f:
            logging.info(f"downloaded data for [{args.symbol}] with length {len(new_candles)}")
            json.dump(candles, f)
    else:
        logging.info(f"no new data for [{args.symbol}]")
