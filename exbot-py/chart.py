import argparse
import logging
import pandas as pd
from config import load_config
import numpy as np

from exchanges import exchange
from strategies import ichiv1
import mplfinance as mpf
from download import download_candles


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='exbot for python')
    parser.add_argument('-c', '--config', type=str, required=True, help='config file path')
    parser.add_argument('--symbol', type=str, required=True, help='The trading symbol to use')
    parser.add_argument('-t', '--timeframe', type=str, required=True, help='timeframe: 1m 5m 15m 30m 1h 4h 1d 1w 1M')
    # add arg verbose
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info('exbot charting ....')

    config = load_config(args.config)
    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    print(ex.id())

    ohlcv = download_candles(ex, args.symbol, args.timeframe)

    df = pd.DataFrame(ohlcv, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True).dt.tz_convert('Asia/Shanghai')

    df.set_index('date', inplace=True)
    # df = df.sort_index(ascending=True)
    apds = []
    mpf.plot(df, addplot=apds, type='candle', mav=(3,6,9), volume=True, style='yahoo', title=args.symbol)
    
