
import ccxt


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


