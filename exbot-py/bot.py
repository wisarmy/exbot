import argparse
import logging
import pandas as pd
from config import load_config
import numpy as np
from download import download_candles

from exchanges import exchange
from strategies import ichiv1
import mplfinance as mpf


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

    logging.info('exbot start')

    logging.info(args.config)

    config = load_config(args.config)

    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()

    print(args)
    print(ex.id())
    print(ex.get_balance('USDT'))
    ohlcv = download_candles(ex, args.symbol, args.timeframe)
    df = pd.DataFrame(ohlcv, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True).dt.tz_convert('Asia/Shanghai')
    s = ichiv1.ichiv1()
    print(df)
    df = s.populate_indicators(df)
    print(df)
    df = s.populate_buy_trend(df)
    print(df)
    df = s.populate_sell_trend(df)
    print(df)
    # df.to_csv('test.csv')

    df.set_index('date', inplace=True)
    # df = df.sort_index(ascending=True)
    apds = []
    buy_points = np.where(df['buy'] == 1.0, df['close'], np.nan)
    sell_points = np.where(df['sell'] == 1.0, df['close'], np.nan)
    print(buy_points)
    print(sell_points)

    if np.count_nonzero(~np.isnan(buy_points)) > 0:
        apds.append(mpf.make_addplot(buy_points, type='scatter', markersize=200, marker='^', color='r'))
    if np.count_nonzero(~np.isnan(sell_points)) > 0:
        apds.append(mpf.make_addplot(sell_points, type='scatter', markersize=200, marker='v', color='g'))

    mpf.plot(df, addplot=apds, type='candle', mav=(3,6,9), volume=True, style='yahoo', title=args.symbol)
    
