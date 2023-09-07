import datetime
import os
from exchanges.bitget import BitgetExchange
import pytz
from core.logger import logger
from core.logger import setup_datalogger
from collections import OrderedDict

used_cache = OrderedDict()
cache_size = 128
# symbol, price, short_qty, short_entry_price, short_realised, short_upnl, long_qty, long_entry_price, long_realised, long_upnl
position_logger = setup_datalogger("position.csv")


def set_used_cache(key, value, cache_type=""):
    key = f"{cache_type}_{key}"
    used_cache[key] = value
    if len(used_cache) > cache_size:
        # 去除最旧的键值
        used_cache.popitem(last=False)


def get_used_cache(key, cache_type=""):
    key = f"{cache_type}_{key}"
    return used_cache.get(key)


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


def signal_to_side(signal):
    if signal == "buy":
        return "long"
    elif signal == "sell":
        return "short"
    else:
        return None


def handle_take_profit(last, ex: BitgetExchange, symbol, position):
    input_amount = float(os.getenv("CLOSE_AMOUNT", 0))
    hold_side = signal_to_side(last["take_profit"])
    if hold_side is None:
        return False

    for side in ["short", "long"]:
        position_amount = position[side]["qty"]
        close_amount = min(
            input_amount if input_amount > 0 else position_amount,
            position_amount,
        )
        if close_amount > 0:
            upnl = position[side]["upnl"]
            profit = upnl * (close_amount / position_amount)
            if hold_side == side:
                order_side = "buy" if hold_side == "short" else "sell"
                logger.info(
                    f"take_profit {side}: {last['close']}, amount: [{close_amount}/{position_amount}], profit: {profit}"
                )
                ex.close_position(symbol, order_side, close_amount)
                return True
    return False


def handle_stop_loss(last, ex: BitgetExchange, symbol, position):
    input_amount = float(os.getenv("CLOSE_AMOUNT", 0))
    hold_side = signal_to_side(last["stop_loss"])
    if hold_side is None:
        return False

    for side in ["short", "long"]:
        position_amount = position[side]["qty"]
        close_amount = min(
            input_amount if input_amount > 0 else position_amount,
            position_amount,
        )
        if close_amount > 0:
            upnl = position[side]["upnl"]
            profit = upnl * (close_amount / position_amount)
            if hold_side == side:
                order_side = "buy" if hold_side == "short" else "sell"
                logger.info(
                    f"stop_loss {side}: {last['close']}, amount: [{close_amount}/{position_amount}], profit: {profit}"
                )
                ex.close_position(symbol, order_side, close_amount)
                return True
    return False


def handle_take_profit_fix_upnl(last, ex: BitgetExchange, symbol, position):
    fix_upnl = float(os.getenv("TAKE_PROFIT_FIX_UPNL", 0))
    input_amount = float(os.getenv("CLOSE_AMOUNT", 0))
    if fix_upnl > 0:
        for side in ["short", "long"]:
            position_amount = position[side]["qty"]
            close_amount = min(
                input_amount if input_amount > 0 else position_amount,
                position_amount,
            )
            if close_amount > 0:
                upnl = position[side]["upnl"]
                if upnl > fix_upnl:
                    profit = upnl * (close_amount / position_amount)
                    logger.info(
                        f"take_profit_fix_upnl {side}: {last['close']}, amount: [{close_amount}/{position_amount}], profit: [{profit}/{upnl}], TP: {fix_upnl}"
                    )
                    order_side = "buy" if side == "short" else "sell"
                    ex.close_position(symbol, order_side, close_amount)
                    return True
    return False


def handle_stop_loss_fix_upnl(last, ex: BitgetExchange, symbol, position):
    fix_upnl = float(os.getenv("STOP_LOSS_FIX_UPNL", 0))
    input_amount = float(os.getenv("CLOSE_AMOUNT", 0))
    if fix_upnl < 0:
        for side in ["short", "long"]:
            position_amount = position[side]["qty"]
            close_amount = min(
                input_amount if input_amount > 0 else position_amount,
                position_amount,
            )
            if close_amount > 0:
                upnl = position[side]["upnl"]
                if upnl < fix_upnl:
                    profit = upnl * (close_amount / position_amount)
                    logger.info(
                        f"stop_loss_fix_upnl {side}: {last['close']}, amount: [{close_amount}/{position_amount}], profit: [{profit}/{upnl}], SL: {fix_upnl}"
                    )
                    order_side = "buy" if side == "short" else "sell"
                    ex.close_position(symbol, order_side, close_amount)
                    return True
    return False


def handle_take_profit_fix_price_urate(last, ex: BitgetExchange, symbol, position):
    fix_urate = float(os.getenv("TAKE_PROFIT_FIX_PRICE_URATE", 0))
    input_amount = float(os.getenv("CLOSE_AMOUNT", 0))
    if fix_urate > 0:
        for side in ["short", "long"]:
            position_amount = position[side]["qty"]
            close_amount = min(
                input_amount if input_amount > 0 else position_amount,
                position_amount,
            )
            price = float(last["close"])
            open_price = float(position[side]["entry_price"])
            upnl = position[side]["upnl"]
            if close_amount > 0:
                close_price = (
                    open_price * (1 + fix_urate)
                    if side == "long"
                    else open_price * (1 - fix_urate)
                )
                logger.debug(
                    f"# take_profit_fix_price_urate {side}: close_price: {close_price}, close_amount: {close_amount}"
                )
                if (side == "long" and price > close_price) or (
                    side == "short" and price < close_price
                ):
                    profit = upnl * (close_amount / position_amount)
                    logger.info(
                        f"take_profit_fix_price_urate {side}: {price}, amount: [{close_amount}/{position_amount}], profit: [{profit}/{upnl}], urate: {fix_urate}"
                    )
                    order_side = "buy" if side == "short" else "sell"
                    ex.close_position(symbol, order_side, close_amount)
                    return True
    return False


def handle_stop_loss_fix_price_urate(last, ex: BitgetExchange, symbol, position):
    fix_urate = float(os.getenv("STOP_LOSS_FIX_PRICE_URATE", 0))
    input_amount = float(os.getenv("CLOSE_AMOUNT", 0))
    if fix_urate > 0:
        for side in ["short", "long"]:
            position_amount = position[side]["qty"]
            close_amount = min(
                input_amount if input_amount > 0 else position_amount,
                position_amount,
            )
            price = float(last["close"])
            open_price = float(position[side]["entry_price"])
            upnl = position[side]["upnl"]
            if close_amount > 0:
                close_price = (
                    open_price * (1 + fix_urate)
                    if side == "short"
                    else open_price * (1 - fix_urate)
                )
                logger.debug(
                    f"# stop_loss_fix_price_urate {side}: close_price: {close_price}, close_amount: {close_amount}"
                )
                if (side == "long" and price < close_price) or (
                    side == "short" and price > close_price
                ):
                    profit = upnl * (close_amount / position_amount)
                    logger.info(
                        f"stop_loss_fix_price_urate {side}: {price}, amount: [{close_amount}/{position_amount}], profit: [{profit}/{upnl}], urate: {fix_urate}"
                    )
                    order_side = "buy" if side == "short" else "sell"
                    ex.close_position(symbol, order_side, close_amount)
                    return True
    return False


# 数量限制
def amount_limit(ex: BitgetExchange, df, symbol, amount, amount_max_limit):
    side = None
    last, last_date = get_signal_record(df)
    real, real_date = df.iloc[-1], df.index[-1]
    # 获取当前仓位
    position = ex.fetch_position(symbol)
    # logger.debug(f"position: {position}")
    position_logger.info(
        f"{symbol}, {real['close']}, {position['short']['qty']}, {position['short']['entry_price']}, {position['short']['realised']}, {position['short']['upnl']}, {position['long']['qty']}, {position['long']['entry_price']}, {position['long']['realised']}, {position['long']['upnl']}"
    )

    logger.warning(
        f"position: short profit: {position['short']['upnl']}, long profit: {position['long']['upnl']}"
    )

    # 记录已经使用过
    if get_used_cache(last_date) == 1 or get_used_cache(real_date, "real") == 1:
        return side

    side = "buy" if last["buy"] == 1 else "sell" if last["sell"] == 1 else None
    if side is None:
        # 止盈止损信号
        if handle_take_profit(last, ex, symbol, position):
            set_used_cache(last_date, 1)
        elif handle_take_profit_fix_upnl(real, ex, symbol, position):
            set_used_cache(real_date, 1, "real")
        elif handle_take_profit_fix_price_urate(real, ex, symbol, position):
            set_used_cache(real_date, 1, "real")

        if handle_stop_loss(last, ex, symbol, position):
            set_used_cache(last_date, 1)
        elif handle_stop_loss_fix_upnl(real, ex, symbol, position):
            set_used_cache(real_date, 1, "real")
        elif handle_stop_loss_fix_price_urate(real, ex, symbol, position):
            set_used_cache(real_date, 1, "real")

        return side

    set_used_cache(last_date, 1)

    logger.info(f"strategy [{side}] signal: [{last_date} {last['close']}]")
    # 如果有新的信号，先取消所有订单
    ex.cancel_orders(symbol)

    try:
        close_amount = float(os.getenv("CLOSE_AMOUNT", 0))
        # 判断是否有买入信号
        if side == "buy":
            # 判断是否有空仓
            if position["short"]["qty"] > 0:
                close_amount = min(
                    close_amount if close_amount > 0 else amount,
                    amount,
                )
                # 平空
                logger.info(
                    f"close short: {last['close']}, amount:{close_amount}, profit: {position['short']['upnl']}"
                )
                ex.close_position(symbol, "buy", close_amount)
                # 如果全部平仓，反向开单
                if close_amount >= position["short"]["qty"]:
                    # 开多
                    logger.info(
                        f"all short position have been closed. open long: {last['close']}, amount:{amount}"
                    )
                    ex.create_order_market(symbol, "buy", amount, last["close"])

            else:
                if position["long"]["qty"] < amount_max_limit:
                    # 开多
                    logger.info(f"open long: {last['close']}, amount:{amount}")
                    ex.create_order_market(symbol, "buy", amount, last["close"])
                else:
                    # 超出最大仓位
                    logger.info(f"long position is max: {position['long']['qty']}")
                    # # 如果是盈利的，平仓 , 0.0006 * 2的手续费
                    # if (
                    #     position["long"]["upnl"]
                    #     > position["long"]["qty"]
                    #     * position["long"]["price"]
                    #     * 0.0006
                    #     * 2
                    # ):
                    #     logger.info(
                    #         f"close long: {last['close']}, profit: {position['long']['upnl']}"
                    #     )
                    #     ex.close_position(symbol, "sell", position["long"]["qty"])

        elif side == "sell":
            # 判断是否有多仓
            if position["long"]["qty"] > 0:
                close_amount = min(
                    close_amount if close_amount > 0 else amount,
                    amount,
                )
                # 平多
                logger.info(
                    f"close long: {last['close']}, amount:{close_amount}, profit: {position['long']['upnl']}"
                )
                ex.close_position(symbol, "sell", close_amount)
                # 如果全部平仓，反向开单
                if close_amount >= position["long"]["qty"]:
                    # 开多
                    logger.info(
                        f"all long position have been closed. open short: {last['close']}, amount:{amount}"
                    )
                    ex.create_order_market(symbol, "sell", amount, last["close"])
            else:
                if position["short"]["qty"] < amount_max_limit:
                    # 开空
                    logger.info(f"open short: {last['close']}, amount:{amount}")
                    ex.create_order_market(symbol, "sell", amount, last["close"])
                else:
                    # 超出最大仓位
                    logger.info(f"short position is max: {position['short']['qty']}")
                    # # 如果是盈利的，平仓 , 0.0006 * 2的手续费
                    # if (
                    #     position["long"]["upnl"]
                    #     > position["long"]["qty"]
                    #     * position["long"]["price"]
                    #     * 0.0006
                    #     * 2
                    # ):
                    #     logger.info(
                    #         f"close short: {last['close']}, profit: {position['short']['upnl']}"
                    #     )
                    #     ex.close_position(symbol, "buy", position["short"]["qty"])

    except Exception as e:
        logger.exception(f"An unknown error occurred in amount_limit(): {e}")
    return side
