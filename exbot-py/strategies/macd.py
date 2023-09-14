import datetime
import os
from pandas import DataFrame
import pytz
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

    condition_dea = os.getenv("CONDITION_DEA", 0)

    def populate_indicators(self, df: DataFrame) -> DataFrame:
        close_prices = df["close"].values  # 获取收盘价的数据
        fast_period = 12
        slow_period = 26
        signal_period = 9
        macd, signal, hist = talib.MACD(
            close_prices, fast_period, slow_period, signal_period
        )

        df["dif"] = np.around(macd, decimals=6)
        df["dea"] = np.around(signal, decimals=6)
        df["macd"] = np.around(hist, decimals=6)
        # golden cross
        df["cross"] = np.where(
            (df["dif"] > df["dea"]) & (df["dif"].shift(1) < df["dea"].shift(1)),
            1,
            0,
        )
        # dead cross
        df["cross"] = np.where(
            (df["dif"] < df["dea"]) & (df["dif"].shift(1) > df["dea"].shift(1)),
            -1,
            df["cross"],
        )
        df["close_pct_change"] = df["close"].pct_change()
        return df

    def filter_timeframe_threshold(self, df, conditions):
        # 确认交叉信号
        timeframe_seconds = df.index.unique().to_series().diff().min().total_seconds()
        if timeframe_seconds == 60:
            threshold = 10
        elif timeframe_seconds == 5 * 60:
            threshold = 15
        elif timeframe_seconds == 15 * 60:
            threshold = 25
        else:
            threshold = 30
        last_date = df.index[-1]
        next_date = last_date + datetime.timedelta(seconds=timeframe_seconds)
        now_date = datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai"))
        # 如果距离下次没在 threshold 内，去除 last_date 的信号
        if next_date - now_date > datetime.timedelta(seconds=threshold):
            conditions.append(df.index < last_date)
            df.loc[df.index >= last_date, "signal_by"] = pd.Series(
                "removed_by_timeframe_threshold",
                index=df.index[df.index >= last_date],
            )

    def populate_buy_trend(self, df: DataFrame) -> DataFrame:
        if "signal" not in df:
            df["signal"] = pd.Series(dtype="str")
            df["signal_by"] = pd.Series(dtype="str")

        conditions = []
        conditions.append(df["cross"] == 1)
        if self.condition_dea == "true":
            conditions.append(df["dea"] < 0)
        self.filter_timeframe_threshold(df, conditions)

        if conditions:
            df.loc[reduce(lambda x, y: x & y, conditions), "buy"] = 1
            # update signals that prices have big rise
            conditions.append(df["close_pct_change"] <= 0.004)
            df.loc[reduce(lambda x, y: x & y, conditions), "signal"] = "buy"
            df["signal_by"] = np.where(
                (df["buy"] == 1) & (df["close_pct_change"] > 0.004),
                "removed_buy_rise",
                df["signal_by"],
            )

        return df

    def populate_sell_trend(self, df: DataFrame) -> DataFrame:
        if "signal" not in df:
            df["signal"] = pd.Series(dtype="str")
            df["signal_by"] = pd.Series(dtype="str")

        conditions = []
        conditions.append(df["cross"] == -1)
        if self.condition_dea == "true":
            conditions.append(df["dea"] > 0)
        self.filter_timeframe_threshold(df, conditions)

        if conditions:
            df.loc[reduce(lambda x, y: x & y, conditions), "sell"] = 1
            conditions.append(df["close_pct_change"] >= -0.004)
            df.loc[reduce(lambda x, y: x & y, conditions), "signal"] = "sell"
            # update signals that prices have big fall
            df["signal_by"] = np.where(
                (df["sell"] == 1) & (df["close_pct_change"] < -0.004),
                "removed_sell_fall",
                df["signal_by"],
            )

        return df

    def populate_close_position(
        self, df: DataFrame, take_profit=True, stop_loss=True
    ) -> DataFrame:
        df["take_profit"] = pd.Series(dtype="str")
        df["stop_loss"] = pd.Series(dtype="str")
        # macd三连跌止盈止损
        fall_nums = 0
        before_macd = 0
        # 开仓信号
        open_signal = None
        # 开仓价格
        open_price = 0
        # 平仓收益
        profit = 0
        # fee
        fee_rate = 0.0012
        fee = 0

        conditions = []
        self.filter_timeframe_threshold(df, conditions)

        for index, row in (
            df.loc[reduce(lambda x, y: x & y, conditions)].iterrows()
            if len(conditions) > 0
            else df.iterrows()
        ):
            # 如果发现信号，就重置计数器
            if pd.notnull(row["signal"]):
                # set open data
                open_signal = row["signal"]
                open_price = float(row["close"])
                fee = open_price * fee_rate
                fall_nums = 0
                before_macd = abs(row["macd"])
                continue
            if abs(row["macd"]) < before_macd:
                fall_nums += 1
            else:
                fall_nums = 0
            before_macd = abs(row["macd"])
            if fall_nums == 4:
                if open_signal == "buy":
                    profit = float(row["close"]) - open_price - fee
                elif open_signal == "sell":
                    profit = open_price - float(row["close"]) - fee
                logger.debug(
                    f"{'take profit' if profit > 0 else 'stop loss'} [macd_fall_4]: {index}, [{open_signal} {open_price} {row['close']}], {profit}"
                )
                if profit > 0:
                    if take_profit:
                        df.loc[index, "take_profit"] = open_signal
                        df.loc[index, "profit"] = profit
                else:
                    if stop_loss:
                        df.loc[index, "stop_loss"] = open_signal
                        df.loc[index, "profit"] = profit
        return df
