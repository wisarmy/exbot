from pandas import DataFrame
import talib
import pandas as pd  # noqa
pd.options.mode.chained_assignment = None  # default='warn'
from functools import reduce
import numpy as np

class macd():

    # NOTE: settings as of the 25th july 21
    # Buy hyperspace params:
    buy_params = {
    }

    # Sell hyperspace params:
    # NOTE: was 15m but kept bailing out in dryrun
    sell_params = {
    }

    # Stoploss:
    stoploss = -0.275

    startup_candle_count = 96
    process_only_new_candles = False

    trailing_stop = False
    #trailing_stop_positive = 0.002
    #trailing_stop_positive_offset = 0.025
    #trailing_only_offset_is_reached = True

    use_sell_signal = True
    sell_profit_only = False

    def populate_indicators(self, dataframe: DataFrame) -> DataFrame:

        # heikinashi = qtpylib.heikinashi(dataframe)
        # dataframe['open'] = heikinashi['open']
        # dataframe['close'] = heikinashi['close']
        # dataframe['high'] = heikinashi['high']
        # dataframe['low'] = heikinashi['low']

        close_prices = dataframe['close'].values  # 获取收盘价的数据
        fast_period = 12
        slow_period = 26
        signal_period = 9
        macd, signal, hist = talib.MACD(close_prices, fast_period, slow_period, signal_period)
        
        dataframe['dif'] = np.around(macd, decimals=6)
        dataframe['dea'] = np.around(signal, decimals=6)
        dataframe['macd'] = np.around(hist, decimals=6)
        # golden cross
        dataframe['cross'] = np.where((dataframe['dif'] > dataframe['dea']) & (dataframe['dif'].shift(1) < dataframe['dea'].shift(1)), 1, 0)
        # dead cross
        dataframe['cross'] = np.where((dataframe['dif'] < dataframe['dea']) & (dataframe['dif'].shift(1) > dataframe['dea'].shift(1)), -1, dataframe['cross'])

        return dataframe


    def populate_buy_trend(self, dataframe: DataFrame) -> DataFrame:

        conditions = []

        conditions.append(dataframe['cross'] == 1)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'buy'] = 1

        return dataframe


    def populate_sell_trend(self, dataframe: DataFrame) -> DataFrame:

        conditions = []
        conditions.append(dataframe['cross'] == -1)

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                'sell'] = 1

        return dataframe
