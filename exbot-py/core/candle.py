import datetime
import json
import os
from core.logger import logger


from typing import List, Any


def get_candles(ex, symbol, timeframe, days=7):
    """
    :param ex: exchange
    :param symbol: eg. BTC/USDT:USDT
    :param str timeframe: 1m 5m 15m 30m 1h 4h 1d 1w 1M
    :param int days: 7
    """
    rootpath = os.getcwd()
    candles_path = os.path.join(
        rootpath, "data", str(ex.id()), f"{symbol.replace('/','_')}_{timeframe}.json"
    )
    # days to since
    since = ex.exchange.milliseconds() - days * 24 * 60 * 60 * 1000

    # declare candles
    candles: List[Any] = []
    if not os.path.exists(candles_path):
        logger.debug(f"download data to {candles_path}")
        os.makedirs(os.path.dirname(candles_path), exist_ok=True)
        candles = ex.get_all_candles(symbol, timeframe, since=since)
        with open(candles_path, "w") as f:
            json.dump(candles, f)
        return candles
    else:
        logger.debug(f"load data from {candles_path}")
        with open(candles_path, "r") as f:
            candles = json.load(f)

    if candles:
        exist_start = candles[0][0]
        exist_end = candles[-1][0]
        if since < exist_start:
            # redownload all data
            # TODO download only missing data
            candles = []
        else:
            # calculate since, +1 to avoid duplicate data
            since = exist_end + 1

    logger.debug(
        f"downloading new data for [{symbol} {timeframe}] from {datetime.datetime.fromtimestamp(since/1000).strftime('%Y-%m-%d %H:%M:%S')}"
    )

    new_candles = ex.get_all_candles(symbol, timeframe, since=since)

    if len(new_candles) > 0:
        candles.extend(new_candles)
        with open(candles_path, "w") as f:
            logger.debug(
                f"downloaded data for [{symbol}] with length {len(new_candles)}"
            )
            json.dump(candles, f)
    else:
        logger.debug(f"no new data for [{symbol}]")

    return candles
