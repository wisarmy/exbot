import argparse
import datetime
import logging
import time
from config import load_config
from core import chart
from exchanges import exchange
import pandas as pd
from core.logger import logger
from strategies.manager import with_strategy
from pandas import DataFrame

pd.set_option("display.max_columns", 1000)
pd.set_option("display.width", 1000)

fee_rate = 0.0012


# 计算收益
def cal_profit(hold_side, position_spend, position_amount, close_price):
    if hold_side == "buy":
        upnl = position_amount * close_price - position_spend
    else:
        upnl = position_spend - position_amount * close_price
    fee = position_spend * fee_rate
    net_profit = upnl - fee
    return net_profit, fee


def backtesting(
    df: DataFrame, reversals=False, uamount=5.5, uamount_max=5.5
) -> DataFrame:
    df["take_profit"] = pd.Series(dtype="str")
    df["stop_loss"] = pd.Series(dtype="str")
    # 持仓
    hold_side = None
    # 持仓花费
    position_spend = 0
    # 持仓数量
    position_amount = 0
    # 总收益
    total_profit = 0
    total_fee = 0
    # last_price
    last_price = 0

    for index, row in df.iterrows():
        last_price = row["close"]
        if pd.notnull(row["buy"]) or pd.notnull(row["sell"]):
            # logger.info(f"{row.name}, close: {row['close']}, {row['buy']} {row['sell']}")
            signal = "buy" if pd.notnull(row["buy"]) else "sell"
            per_amount = uamount / float(row["close"])
            if hold_side is None:
                hold_side = signal
                position_spend = float(row["close"]) * per_amount
                position_amount = per_amount
                logger.info(f"{row.name} open {signal} {row['close']} {per_amount}")
            else:
                if signal == hold_side:
                    # uamount max limit
                    if position_spend >= uamount_max:
                        logger.warning(
                            f"{row.name} skip, position_spend: {position_spend} >= uamount_max: {uamount_max}"
                        )
                        continue

                    average_price = position_spend / position_amount
                    position_spend += float(row["close"]) * per_amount
                    position_amount += per_amount
                    logger.info(
                        f"{row.name} add {signal} {row['close']} {per_amount}, avg_price: {average_price}"
                    )
                else:
                    profit, fee = cal_profit(
                        hold_side, position_spend, position_amount, row["close"]
                    )
                    total_profit += profit
                    total_fee += fee
                    logger.info(
                        f"{row.name} close {hold_side} {row['close']}, position_spend: {position_spend}, position_amount: {position_amount}, profit: {profit}, total profit: {total_profit}, total fee: {total_fee}"
                    )
                    # 反向开仓
                    if reversals:
                        hold_side = signal
                        position_spend = float(row["close"]) * per_amount
                        position_amount = per_amount
                        logger.info(
                            f"{row.name} open {signal} {row['close']} {per_amount}"
                        )
                    else:
                        hold_side = None

    profit, fee = cal_profit(hold_side, position_spend, position_amount, last_price)
    logger.info(
        f"unsettled position: position_spend: {position_spend}, position_amount: {position_amount}, profit: {profit}, fee: {fee}"
    )

    logger.info(f"backtesting total profit: {total_profit}")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="exbot backtesting for python")
    parser.add_argument(
        "-c", "--config", type=str, required=True, help="config file path"
    )
    parser.add_argument(
        "--symbol", type=str, required=True, help="The trading symbol to use"
    )
    parser.add_argument("--strategy", type=str, default="", help="The strategy to use")
    parser.add_argument(
        "--days", type=int, default=7, help="download data for given number of days"
    )
    parser.add_argument(
        "-t",
        "--timeframe",
        type=str,
        required=True,
        help="timeframe: 1m 5m 15m 30m 1h 4h 1d 1w 1M",
    )
    parser.add_argument("--reversals", action="store_true", help="reversals")
    # uamount
    parser.add_argument(
        "--uamount",
        type=float,
        default=5.5,
        help="The usdt amount to trade, > 5",
    )
    parser.add_argument(
        "--uamount_max",
        type=float,
        default=5.5,
        help="The usdt amount max limit to trade",
    )
    # add arg verbose
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    # add arg verbose
    parser.add_argument("-vv", "--verbose2", action="store_true", help="verbose mode")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    if args.verbose2:
        logger.setLevel(logging.DEBUG)
        pd.set_option("display.max_rows", None)

    logger.info("exbot backtesting ...")

    config = load_config(args.config)
    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    logger.info(f"exchange: {ex.id()}, args: {args}")
    # 获取图表实时数据
    df = chart.get_charting(ex, args.symbol, args.timeframe, args.days)
    df = with_strategy(args.strategy, ex, df, args, False)
    logger.info(df)
    backtesting(df, args.reversals, args.uamount, args.uamount_max)
