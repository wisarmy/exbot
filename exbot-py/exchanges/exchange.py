import ccxt
import os
import config
from exchanges.bitget import BitgetExchange


class Exchange:
    def __init__(self, config: config.Exchange):
        self.config = config
        self.init_exchange()

    def init_exchange(self):
        exchange_class = getattr(ccxt, self.config.name)
        params = {}
        params['apiKey'] = self.config.key
        params['secret'] = self.config.secret
        if self.config.passphrase:
            params['password'] = self.config.passphrase

        http_proxy = os.environ.get('HTTP_PROXY')
        https_proxy = os.environ.get('HTTPS_PROXY')
        if http_proxy and https_proxy:
            params["proxies"] = {
                    'http': http_proxy,
                    'https': https_proxy,
                    }
        if self.config.name == 'bitget':
            self.exchange_bitget = BitgetExchange(exchange_class(params))
        else:
            raise Exception('not support exchange: {}'.format(self.config.name))
    def get(self):
            return self.exchange_bitget
