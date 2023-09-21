import os
from typing import Literal
from exchanges.bitget import BitgetExchange
from core.logger import logger
from core.logger import setup_datalogger
from collections import OrderedDict

used_cache = OrderedDict()
cache_size = 128
# symbol, price, short_qty, short_entry_price, short_realised, short_upnl, long_qty, long_entry_price, long_realised, long_upnl
position_logger = setup_datalogger("position.csv", "data")


def set_used_cache(key, value, cache_type=""):
    key = f"{cache_type}_{key}"
    used_cache[key] = value
    if len(used_cache) > cache_size:
        # 去除最旧的键值
        used_cache.popitem(last=False)


def get_used_cache(key, cache_type=""):
    key = f"{cache_type}_{key}"
    return used_cache.get(key)


def signal_to_side(signal):
    if signal == "buy":
        return "long"
    elif signal == "sell":
        return "short"
    else:
        return None


def handle_take_profit(last, ex: BitgetExchange, symbol, position):
    tp = os.getenv("TAKE_PROFIT", "false") == "true"
    if not tp:
        return False

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
                return ex.close_position(symbol, order_side, close_amount)
    return False


def handle_stop_loss(last, ex: BitgetExchange, symbol, position):
    sl = os.getenv("STOP_LOSS", "false") == "true"
    if not sl:
        return False

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
                return ex.close_position(symbol, order_side, close_amount)
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
                    return ex.close_position(symbol, order_side, close_amount)
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
                    return ex.close_position(symbol, order_side, close_amount)
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
                    return ex.close_position(symbol, order_side, close_amount)
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
                    return ex.close_position(symbol, order_side, close_amount)
    return False


# create_order condition: price loss urate
def create_order_condition_price_loss_urate(
    hold_side: Literal["short", "long"], entry_price, price, default_urate=0
):
    # no position
    if entry_price == 0:
        return True
    loss_urate = float(
        os.getenv("CREATE_ORDER_CONDITION_PRICE_LOSS_URATE", default_urate)
    )
    if loss_urate == 0:
        return True
    floating_urate = round(abs(entry_price - price) / entry_price, 3)

    if floating_urate >= loss_urate:
        if (hold_side == "long" and price < entry_price) or (
            hold_side == "short" and price > entry_price
        ):
            return True

    logger.warning(
        f"not satisfied create_order_condition_price_loss_urate[{hold_side}]: {floating_urate} >= {loss_urate} and price: {price} {'<' if hold_side == 'long' else '>'} entry_price: {entry_price}"
    )
    return False


def create_order_market(
    ex: BitgetExchange,
    symbol: str,
    side: Literal["buy", "sell"],
    amount: float,
    price: float,
    entry_price=0.0,
):
    hold_side = signal_to_side(side)
    open_price = entry_price if entry_price > 0 else price

    if create_order_condition_price_loss_urate(hold_side, open_price, price) is False:
        return False

    stop_loss_urate = float(os.getenv("POSITION_STOP_LOSS_URATE", 0.1))
    stop_loss_trigger_price = (
        open_price * (1 + stop_loss_urate)
        if side == "sell"
        else open_price * (1 - stop_loss_urate)
    )
    take_profit_urate = float(os.getenv("POSITION_TAKE_PROFIT_URATE", 0.1))
    take_profit_trigger_price = (
        open_price * (1 + take_profit_urate)
        if side == "buy"
        else open_price * (1 - take_profit_urate)
    )

    logger.info(
        f"open {side}: {price}, amount: {amount}, stop_loss: {stop_loss_trigger_price}, take_profit: {take_profit_trigger_price}"
    )
    ex.create_order_market(symbol, side, amount, price)
    # position tpsl
    ex.place_position_tpsl(symbol, "pos_loss", stop_loss_trigger_price, hold_side)
    ex.place_position_tpsl(symbol, "pos_profit", take_profit_trigger_price, hold_side)

    return True


# handle tpsl
def handle_tpsl(last, last_date, ex: BitgetExchange, symbol, position):
    # take profit
    if get_used_cache(last_date, "take_profit") != 1:
        if handle_take_profit(last, ex, symbol, position):
            set_used_cache(last_date, 1, "take_profit")
    # take profit fix upnl
    if get_used_cache(last_date, "take_profit_fix_upnl") != 1:
        if handle_take_profit_fix_upnl(last, ex, symbol, position):
            set_used_cache(last_date, 1, "take_profit_fix_upnl")
    # take profit fix price urate
    if get_used_cache(last_date, "take_profit_fix_price_urate") != 1:
        if handle_take_profit_fix_price_urate(last, ex, symbol, position):
            set_used_cache(last_date, 1, "take_profit_fix_price_urate")
    # stop loss
    if get_used_cache(last_date, "stop_loss") != 1:
        if handle_stop_loss(last, ex, symbol, position):
            set_used_cache(last_date, 1, "stop_loss")
    # stop loss fix upnl
    if get_used_cache(last_date, "stop_loss_fix_upnl") != 1:
        if handle_stop_loss_fix_upnl(last, ex, symbol, position):
            set_used_cache(last_date, 1, "stop_loss_fix_upnl")
    # stop loss fix price urate
    if get_used_cache(last_date, "stop_loss_fix_price_urate") != 1:
        if handle_stop_loss_fix_price_urate(last, ex, symbol, position):
            set_used_cache(last_date, 1, "stop_loss_fix_price_urate")


# handle side
def handle_side(
    ex: BitgetExchange,
    last,
    last_date,
    symbol,
    amount,
    amount_max_limit,
    position,
    side,
    reversals=False,
):
    last_price = float(last["close"])
    short_position_amount = position["short"]["qty"]
    long_position_amount = position["long"]["qty"]
    short_entry_price = position["short"]["entry_price"]
    long_entry_price = position["long"]["entry_price"]

    logger.info(f"strategy [{side}] signal: [{last_date} {last['close']}]")
    # 如果有新的信号，先取消所有订单
    ex.cancel_orders(symbol)

    try:
        # 判断是否有买入信号
        if side == "buy":
            # 判断是否有空仓
            if short_position_amount > 0:
                # 平空
                logger.info(
                    f"close short: {last_price}, profit: {position['short']['upnl']}"
                )
                if ex.close_position(symbol, "buy", short_position_amount):
                    logger.info(f"all short position have been closed.")
                else:
                    logger.warning(f"close short failed.")
                    return False
                # 反向开单
                if reversals:
                    if (
                        create_order_market(ex, symbol, "buy", amount, last_price)
                        is False
                    ):
                        return False

            else:
                if long_position_amount < amount_max_limit:
                    if (
                        create_order_market(
                            ex, symbol, "buy", amount, last_price, long_entry_price
                        )
                        is False
                    ):
                        return False
                else:
                    # 超出最大仓位
                    logger.info(f"long position is max: {long_position_amount}")

        elif side == "sell":
            # 判断是否有多仓
            if long_position_amount > 0:
                # 平多
                logger.info(
                    f"close long: {last_price}, profit: {position['long']['upnl']}"
                )
                if ex.close_position(symbol, "sell", long_position_amount):
                    logger.info(f"all long position have been closed.")
                else:
                    logger.warning(f"close long failed.")
                    return False
                # 反向开单
                if reversals:
                    if (
                        create_order_market(ex, symbol, "sell", amount, last_price)
                        is False
                    ):
                        return False
            else:
                if short_position_amount < amount_max_limit:
                    if (
                        create_order_market(
                            ex, symbol, "sell", amount, last_price, short_entry_price
                        )
                        is False
                    ):
                        return False
                else:
                    # 超出最大仓位
                    logger.info(f"short position is max: {short_position_amount}")

        return True
    except Exception as e:
        logger.exception(f"An unknown error occurred in handle_side: {e}")

    return False


# 数量限制
def amount_limit(
    ex: BitgetExchange, df, symbol, amount, amount_max_limit, reversals=False
):
    side = None
    last, last_date = df.iloc[-1], df.index[-1]
    # 获取当前仓位
    position = ex.fetch_position(symbol)
    if position is None:
        return side

    logger.debug(f"position: {position}")
    position_logger.info(
        f"{symbol}, {last['close']}, {position['short']['qty']}, {position['short']['entry_price']}, {position['short']['realised']}, {position['short']['upnl']}, {position['long']['qty']}, {position['long']['entry_price']}, {position['long']['realised']}, {position['long']['upnl']}"
    )

    logger.warning(
        f"position: short profit: {position['short']['upnl']}, long profit: {position['long']['upnl']}"
    )

    side = "buy" if last["buy"] == 1 else "sell" if last["sell"] == 1 else None
    if side is None:
        handle_tpsl(last, last_date, ex, symbol, position)
        return side

    # record has been used
    if get_used_cache(last_date) != 1:
        if handle_side(
            ex,
            last,
            last_date,
            symbol,
            amount,
            amount_max_limit,
            position,
            side,
            reversals,
        ):
            set_used_cache(last_date, 1)

    return side


# usdt数量限制
def uamount_limit(
    ex: BitgetExchange, df, symbol, uamount, uamount_max_limit, reversals=False
):
    last, _ = df.iloc[-1], df.index[-1]
    last_price = float(last["close"])
    amount = uamount / last_price
    amount_max_limit = uamount_max_limit / last_price
    return amount_limit(ex, df, symbol, amount, amount_max_limit, reversals)
