import logging
import unittest

from config import load_config
from exchanges import exchange


def get_ex():
    config = load_config("configs/config.toml")
    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    return ex


class TestMethods(unittest.TestCase):
    def test_client(self):
        ex = get_ex()
        # position take profit or stop loss for ex client
        # order = ex.client.mix_place_PositionsTPSL(
        #     ex.market_symbol(symbol="XRP/USDT:USDT"),
        #     marginCoin="USDT",
        #     planType="pos_loss",
        #     triggerPrice="0.51",
        #     triggerType="market_price",
        #     holdSide="short",
        # )
        # print(order)
        # order = ex.client.mix_place_PositionsTPSL(
        #     ex.market_symbol(symbol="XRP/USDT:USDT"),
        #     marginCoin="USDT",
        #     planType="pos_profit",
        #     triggerPrice="0.41",
        #     triggerType="market_price",
        #     holdSide="short",
        # )
        # print(order)
        # order = ex.client.mix_modify_stop_order(
        #     ex.market_symbol(symbol="XRP/USDT:USDT"),
        #     marginCoin="USDT",
        #     orderId="1085677258583646209",
        #     triggerPrice="0.42",
        #     planType="pos_profit",
        # )
        # print(order)

        # ex.place_position_tpsl("XRP/USDT:USDT", "pos_loss", 0.52, "short")
        # ex.place_position_tpsl("XRP/USDT:USDT", "pos_profit", 0.42, "short")
