import datetime
import os
from exchanges.bitget import BitgetExchange
import pytz
from core.logger import logger
from collections import OrderedDict

used_cache = OrderedDict()
cache_size = 128


def set_used_cache(key, value):
    used_cache[key] = value
    if len(used_cache) > cache_size:
        # 去除最旧的键值
        used_cache.popitem(last=False)


# threshold 剩余多少 s 换线
def get_signal_record(df, threshold=None, ref_time=None):
    df_last = df.iloc[-1]
    df_last_date = df.index[-1]
    timeframe_seconds = df.index.to_series().diff().min().total_seconds()
    if threshold is None:
        if timeframe_seconds == 60:
            threshold = 10
        elif timeframe_seconds == 5 * 60:
            threshold = 15
        elif timeframe_seconds == 15 * 60:
            threshold = 20
        else:
            threshold = 30

    ref_time = (
        datetime.datetime.now(tz=pytz.timezone("Asia/Shanghai"))
        if ref_time is None
        else ref_time
    )
    elapsed_seconds = (ref_time - df_last_date).total_seconds()

    # 根据剩余换线的时间，来确定使用 -1 还是 -2
    index = -1 if timeframe_seconds - elapsed_seconds <= threshold else -2

    # logger.info(
    #     f"df_last_date: {df_last_date}, ref_time: {ref_time}, elapsed_seconds: {elapsed_seconds}, timeframe_seconds: {timeframe_seconds}, threshold: {threshold}, index: {index}"
    # )

    return df.iloc[index], df.index[index]


def handle_take_profit(last, ex: BitgetExchange, symbol, position):
    if last["take_profit"] == "sell":
        if position["short"]["qty"] > 0:
            logger.info(
                f"take_profit short: {last['close']}, profit: {position['short']['upnl']}"
            )
            ex.close_position(symbol, "buy", position["short"]["qty"])
            return True
    elif last["take_profit"] == "buy":
        if position["long"]["qty"] > 0:
            logger.info(
                f"take_profit long: {last['close']}, profit: {position['long']['upnl']}"
            )
            ex.close_position(symbol, "sell", position["long"]["qty"])
            return True

    return False


def handle_stop_loss(last, ex: BitgetExchange, symbol, position):
    if last["stop_loss"] == "sell":
        if position["short"]["qty"] > 0:
            logger.info(
                f"stop_loss short: {last['close']}, profit: {position['short']['upnl']}"
            )
            ex.close_position(symbol, "buy", position["short"]["qty"])
            return True
    elif last["stop_loss"] == "buy":
        if position["long"]["qty"] > 0:
            logger.info(
                f"stop_loss long: {last['close']}, profit: {position['long']['upnl']}"
            )
            ex.close_position(symbol, "sell", position["long"]["qty"])
            return True

    return False


def handle_take_profit_fix_upnl(last, ex: BitgetExchange, symbol, position):
    fix_upnl = float(os.getenv("TAKE_PROFIT_FIX_UPNL", 0))
    if fix_upnl > 0:
        for side in ["short", "long"]:
            if position[side]["qty"] > 0:
                upnl = position[side]["upnl"]
                if upnl > fix_upnl:
                    logger.info(
                        f"take_profit_fix_upnl {side}: {last['close']}, profit: {upnl}, TP: {fix_upnl}"
                    )
                    order_side = "buy" if side == "short" else "sell"
                    ex.close_position(symbol, order_side, position[side]["qty"])
        return True
    return False


def handle_stop_loss_fix_upnl(last, ex: BitgetExchange, symbol, position):
    fix_upnl = float(os.getenv("STOP_LOSS_FIX_UPNL", 0))
    if fix_upnl < 0:
        for side in ["short", "long"]:
            if position[side]["qty"] > 0:
                upnl = position[side]["upnl"]
                if upnl < fix_upnl:
                    logger.info(
                        f"stop_loss_fix_upnl {side}: {last['close']}, profit: {upnl}, SL: {fix_upnl}"
                    )
                    order_side = "buy" if side == "short" else "sell"
                    ex.close_position(symbol, order_side, position[side]["qty"])
        return True
    return False


# 数量限制
def amount_limit(ex: BitgetExchange, df, symbol, amount, amount_max_limit):
    side = None
    last, last_date = get_signal_record(df)
    # 获取当前仓位
    position = ex.fetch_position(symbol)
    # logger.info(f"position: {position}")

    logger.warning(
        f"position: short profit: {position['short']['upnl']}, long profit: {position['long']['upnl']}"
    )

    # 记录已经使用过
    if used_cache.get(last_date) == 1:
        return side

    side = "buy" if last["buy"] == 1 else "sell" if last["sell"] == 1 else None
    if side is None:
        # 止盈止损信号
        if handle_take_profit(last, ex, symbol, position):
            set_used_cache(last_date, 1)
        elif handle_take_profit_fix_upnl(last, ex, symbol, position):
            set_used_cache(last_date, 1)

        if handle_stop_loss(last, ex, symbol, position):
            set_used_cache(last_date, 1)
        elif handle_stop_loss_fix_upnl(last, ex, symbol, position):
            set_used_cache(last_date, 1)

        return side

    set_used_cache(last_date, 1)

    logger.info(f"strategy [{side}] signal: [{last_date} {last['close']}]")
    # 如果有新的信号，先取消所有订单
    ex.cancel_orders(symbol)

    try:
        # 判断是否有买入信号
        if side == "buy":
            # 判断是否有空仓
            if position["short"]["qty"] > 0:
                # 平空
                logger.info(
                    f"close short: {last['close']}, profit: {position['short']['upnl']}"
                )
                ex.close_position(symbol, "buy", amount)
                # 如果全部平仓，反向开单
                if amount == position["short"]["qty"]:
                    # 开多
                    logger.info(
                        f"all short position have been closed. open long: {last['close']}"
                    )
                    ex.create_order_market(symbol, "buy", amount, last["close"])

            else:
                if position["long"]["qty"] < amount_max_limit:
                    # 开多
                    logger.info(f"open long: {last['close']}")
                    ex.create_order_market(symbol, "buy", amount, last["close"])
                else:
                    # 超出最大仓位
                    logger.info(f"long position is max: {position['long']['qty']}")
                    # 如果是盈利的，平仓 , 0.0006 * 2的手续费
                    if (
                        position["long"]["upnl"]
                        > position["long"]["qty"]
                        * position["long"]["price"]
                        * 0.0006
                        * 2
                    ):
                        logger.info(
                            f"close long: {last['close']}, profit: {position['long']['upnl']}"
                        )
                        ex.close_position(symbol, "sell", position["long"]["qty"])

        elif side == "sell":
            # 判断是否有多仓
            if position["long"]["qty"] > 0:
                # 平多
                logger.info(
                    f"close long: {last['close']}, profit: {position['long']['upnl']}"
                )
                ex.close_position(symbol, "sell", amount)
                # 如果全部平仓，反向开单
                if amount == position["long"]["qty"]:
                    # 开多
                    logger.info(
                        f"all long position have been closed. open short: {last['close']}"
                    )
                    ex.create_order_market(symbol, "sell", amount, last["close"])
            else:
                if position["short"]["qty"] < amount_max_limit:
                    # 开空
                    logger.info(f"open short: {last['close']}")
                    ex.create_order_market(symbol, "sell", amount, last["close"])
                else:
                    # 超出最大仓位
                    logger.info(f"short position is max: {position['short']['qty']}")
                    # 如果是盈利的，平仓 , 0.0006 * 2的手续费
                    if (
                        position["long"]["upnl"]
                        > position["long"]["qty"]
                        * position["long"]["price"]
                        * 0.0006
                        * 2
                    ):
                        logger.info(
                            f"close short: {last['close']}, profit: {position['short']['upnl']}"
                        )
                        ex.close_position(symbol, "buy", position["short"]["qty"])

    except Exception as e:
        logger.exception(f"An unknown error occurred in amount_limit(): {e}")
    return side
