import ccxt
from core.logger import logger
import time
from ccxt.base.errors import RateLimitExceeded
from typing import Literal


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

    def get_balance(self, quote, account_type="futures"):
        if account_type == "futures":
            if self.exchange.has["fetchBalance"]:
                # Fetch the balance
                balance = self.exchange.fetch_balance(params={"type": "swap"})

                for currency_balance in balance["info"]:
                    if currency_balance["marginCoin"] == quote:
                        return float(currency_balance["equity"])
        else:
            # Handle other account types or fallback to default behavior
            pass

    def get_open_orders(self, symbol: str) -> list:
        open_orders = []
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            # print(f"Raw orders: {json.dumps(orders, indent=4)}")
            for order in orders:
                if "info" in order:
                    info = order["info"]
                    if (
                        "state" in info and info["state"] == "new"
                    ):  # Change "status" to "state"
                        order_data = {
                            "id": info.get(
                                "orderId", ""
                            ),  # Change "order_id" to "orderId"
                            "price": info.get(
                                "price", 0.0
                            ),  # Use the correct field name
                            "qty": info.get("size", 0.0),  # Change "qty" to "size"
                            "side": info.get("side", ""),
                            "reduce_only": info.get("reduceOnly", False),
                        }
                        open_orders.append(order_data)
        except Exception as e:
            logger.exception(
                f"An unknown error occurred in get_open_orders_debug(): {e}"
            )
        return open_orders

    def create_order_limit(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: float,
        price: float,
        params: dict = {},
    ):
        return self.exchange.create_order(symbol, "limit", side, amount, price, params)

    def create_order_market(
        self,
        symbol: str,
        side: Literal["buy", "sell"],
        amount: float,
        price: float,
        params: dict = {},
    ):
        return self.exchange.create_order(symbol, "market", side, amount, None, params)

    def cancel_orders(self, symbol: str):
        try:
            get_open_orders = self.get_open_orders(symbol)
            if len(get_open_orders) == 0:
                logger.info("No open orders to cancel.")
                return
            ids = []
            for order in get_open_orders:
                ids.append(order["id"])
                # print(f"Canceling order: {order}")
                # self.exchange.cancel_order(order['id'], symbol)
            logger.info(f"Canceling orders: {ids}")
            self.exchange.cancel_orders(ids, symbol)
        except Exception as e:
            logger.exception(f"An unknown error occurred in cancel_orders(): {e}")

    # 平仓
    def close_position(self, symbol: str, side: Literal["buy", "sell"], amount: float):
        try:
            self.exchange.create_market_order(
                symbol, side, amount, params={"reduceOnly": True}
            )
        except Exception as e:
            logger.exception(f"An unknown error occurred in close_position(): {e}")

    def get_current_candle(self, symbol: str, timeframe="1m", retries=3, delay=60):
        for _ in range(retries):
            try:
                # Fetch the most recent 2 candles
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=2)

                # The last element in the list is the current (incomplete) candle
                current_candle = ohlcv[-1]

                return current_candle

            except RateLimitExceeded:
                logger.exception(
                    "Rate limit exceeded... sleeping for {} seconds".format(delay)
                )
                time.sleep(delay)

        raise RateLimitExceeded(
            "Failed to fetch candle data after {} retries".format(retries)
        )

    def get_candles(
        self, symbol: str, timeframe="1m", since=None, limit=10, retries=3, delay=60
    ):
        for _ in range(retries):
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, timeframe, since=since, limit=limit
                )
                return ohlcv

            except RateLimitExceeded:
                logger.exception(
                    "Rate limit exceeded... sleeping for {} seconds".format(delay)
                )
                time.sleep(delay)

        raise RateLimitExceeded(
            "Failed to fetch candle data after {} retries".format(retries)
        )

    # get all candles from since to now
    def get_all_candles(self, symbol, timeframe, since=None):
        candles = []
        limit = 1000
        while True:
            if since is None:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            else:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol, timeframe, limit=limit, since=since
                )
            candles.extend(ohlcv)
            if len(ohlcv) < limit:
                break
            since = ohlcv[-1][0]
        return candles

    def fetch_position(self, symbol):
        values = {
            "long": {
                "qty": 0.0,
                "price": 0.0,
                "realised": 0,
                "cum_realised": 0,
                "upnl": 0,
                "upnl_pct": 0,
                "liq_price": 0,
                "entry_price": 0,
            },
            "short": {
                "qty": 0.0,
                "price": 0.0,
                "realised": 0,
                "cum_realised": 0,
                "upnl": 0,
                "upnl_pct": 0,
                "liq_price": 0,
                "entry_price": 0,
            },
        }
        try:
            position = self.exchange.fetch_position(symbol)
            logger.debug(f"fetch_position: {position}")
            # 判断是否有持仓
            if position["entryPrice"] is None:
                return values
            side = position["side"]
            values[side]["qty"] = float(
                position["contracts"]
            )  # Use "contracts" instead of "contractSize"
            values[side]["price"] = float(position["entryPrice"])
            values[side]["realised"] = round(
                float(position["info"]["achievedProfits"]), 4
            )
            values[side]["upnl"] = round(float(position["unrealizedPnl"]), 4)
            if position["liquidationPrice"] is not None:
                values[side]["liq_price"] = float(position["liquidationPrice"])
            else:
                logger.warning(f"Warning: liquidationPrice is None for {side} position")
                values[side]["liq_price"] = None
            values[side]["entry_price"] = float(position["entryPrice"])
        except Exception as e:
            logger.exception(f"An unknown error occurred in fetch_position: {e}")
            return None
        return values
