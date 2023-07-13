import logging
import ccxt
import json
import time
from ccxt.base.errors import RateLimitExceeded


class BitgetExchange:
    def __init__(self, exchange: ccxt.bitget):
        self.exchange: ccxt.bitget = exchange

    def load_markets(self):
        self.exchange.load_markets()

    def id(self):
        return self.exchange.id

    def timeframes(self):
        return self.exchange.timeframes

    def rateLimit(self):
        return self.exchange.rateLimit

    def get_balance(self, quote, account_type='futures'):
        if account_type == 'futures':
            if self.exchange.has['fetchBalance']:
                # Fetch the balance
                balance = self.exchange.fetch_balance(params={'type': 'swap'})

                for currency_balance in balance['info']:
                    if currency_balance['marginCoin'] == quote:
                        return float(currency_balance['equity'])
        else:
            # Handle other account types or fallback to default behavior
            pass
    def get_open_orders(self, symbol: str) -> list:
        open_orders = []
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            print(f"Raw orders: {json.dumps(orders, indent=4)}")
            for order in orders:
                if "info" in order:
                    info = order["info"]
                    if "state" in info and info["state"] == "new":  # Change "status" to "state"
                        order_data = {
                            "id": info.get("orderId", ""),  # Change "order_id" to "orderId"
                            "price": info.get("price", 0.0),  # Use the correct field name
                            "qty": info.get("size", 0.0),  # Change "qty" to "size"
                            "side": info.get("side", ""),
                            "reduce_only": info.get("reduceOnly", False),
                        }
                        open_orders.append(order_data)
        except Exception as e:
            logging.warning(f"An unknown error occurred in get_open_orders_debug(): {e}")
        return open_orders

    def get_current_candle(self, symbol: str, timeframe='1m', retries=3, delay=60):
        for _ in range(retries):
            try:
                # Fetch the most recent 2 candles
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=2)

                # The last element in the list is the current (incomplete) candle
                current_candle = ohlcv[-1]

                return current_candle

            except RateLimitExceeded:
                print("Rate limit exceeded... sleeping for {} seconds".format(delay))
                time.sleep(delay)

        raise RateLimitExceeded("Failed to fetch candle data after {} retries".format(retries))
    def get_candles(self, symbol: str, timeframe='1m', since=None, limit=10, retries=3, delay=60):
        for _ in range(retries):
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
                return ohlcv

            except RateLimitExceeded:
                print("Rate limit exceeded... sleeping for {} seconds".format(delay))
                time.sleep(delay)

        raise RateLimitExceeded("Failed to fetch candle data after {} retries".format(retries))
    # get all candles from since to now
    def get_all_candles(self, symbol, timeframe, since=None):
        candles = []
        limit = 1000
        while True:
            if since is None:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            else:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit, since=since)
            candles.extend(ohlcv)
            if len(ohlcv) < limit:
                break
            since = ohlcv[-1][0]
        return candles
