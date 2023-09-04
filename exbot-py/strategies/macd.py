from pandas import DataFrame
import talib
import pandas as pd  # noqa

pd.options.mode.chained_assignment = None  # default='warn'
from functools import reduce
import numpy as np
from core.logger import logger


class macd:
    # NOTE: settings as of the 25th july 21
    # Buy hyperspace params:
    buy_params = {}

    # Sell hyperspace params:
    # NOTE: was 15m but kept bailing out in dryrun
    sell_params = {}

    # Stoploss:
    stoploss = -0.275

    startup_candle_count = 96
    process_only_new_candles = False

    trailing_stop = False
    # trailing_stop_positive = 0.002
    # trailing_stop_positive_offset = 0.025
    # trailing_only_offset_is_reached = True

    use_sell_signal = True
    sell_profit_only = False

    def populate_indicators(self, dataframe: DataFrame) -> DataFrame:
        close_prices = dataframe["close"].values  # 获取收盘价的数据
        fast_period = 12
        slow_period = 26
        signal_period = 9
        macd, signal, hist = talib.MACD(
            close_prices, fast_period, slow_period, signal_period
        )

        dataframe["dif"] = np.around(macd, decimals=6)
        dataframe["dea"] = np.around(signal, decimals=6)
        dataframe["macd"] = np.around(hist, decimals=6)
        # golden cross
        dataframe["cross"] = np.where(
            (dataframe["dif"] > dataframe["dea"])
            & (dataframe["dif"].shift(1) < dataframe["dea"].shift(1)),
            1,
            0,
        )
        # dead cross
        dataframe["cross"] = np.where(
            (dataframe["dif"] < dataframe["dea"])
            & (dataframe["dif"].shift(1) > dataframe["dea"].shift(1)),
            -1,
            dataframe["cross"],
        )

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame) -> DataFrame:
        conditions = []

        conditions.append(dataframe["cross"] == 1)

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "buy"] = 1
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "signal"] = "buy"

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame) -> DataFrame:
        conditions = []
        conditions.append(dataframe["cross"] == -1)

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "sell"] = 1
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "signal"] = "sell"

        return dataframe

    def populate_close_position(
        self, df: DataFrame, take_profit=True, stop_loss=True
    ) -> DataFrame:
        # macd绝对值 三连跌止盈
        fall_nums = 0
        before_macd = 0
        # 开仓信号
        open_signal = None
        # 开仓价格
        open_price = 0
        # 是否已平仓
        is_closed = True
        # 平仓收益
        profit = 0
        # 总收益
        total_profit = 0
        # fee
        fee_rate = 0.0012
        fee = 0

        for index, row in df.iterrows():
            # 如果发现信号，就重置计数器
            if pd.notnull(row["signal"]):
                # 交叉平仓
                if is_closed == False:
                    if open_signal == "buy":
                        profit = float(row["close"]) - open_price - fee
                        total_profit += profit
                    elif open_signal == "sell":
                        profit = open_price - float(row["close"]) - fee
                        total_profit += profit
                    df.loc[index, "profit"] = profit
                    logger.debug(
                        f"{'take profit' if profit > 0 else 'stop loss'} [x]: {index}, [{open_signal} {open_price} {row['close']}], {profit}"
                    )
                    if profit > 0:
                        df.loc[index, "take_profit"] = open_signal
                        df.loc[index, "profit"] = profit
                    else:
                        df.loc[index, "stop_loss"] = open_signal
                        df.loc[index, "profit"] = profit

                # set open data
                open_signal = row["signal"]
                open_price = float(row["close"])
                fee = open_price * fee_rate
                is_closed = False
                fall_nums = 0
                before_macd = abs(row["macd"])
                continue
            if abs(row["macd"]) < before_macd:
                fall_nums += 1
            else:
                fall_nums = 0
            before_macd = abs(row["macd"])
            if fall_nums == 4:
                if is_closed == False:
                    if open_signal == "buy":
                        profit = float(row["close"]) - open_price - fee
                        total_profit += profit
                    elif open_signal == "sell":
                        profit = open_price - float(row["close"]) - fee
                        total_profit += profit
                    logger.debug(
                        f"{'take profit' if profit > 0 else 'stop loss'} [macd_fall_4]: {index}, [{open_signal} {open_price} {row['close']}], {profit}"
                    )
                    if profit > 0:
                        if take_profit:
                            df.loc[index, "take_profit"] = open_signal
                            df.loc[index, "profit"] = profit
                            is_closed = True
                    else:
                        if stop_loss:
                            df.loc[index, "stop_loss"] = open_signal
                            df.loc[index, "profit"] = profit
                            is_closed = True

        logger.info(f"backtesting total profit: {total_profit/open_price}")
        return df
