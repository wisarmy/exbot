import datetime
from exchanges.bitget import BitgetExchange
import pytz


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

    print(
        f"df_last_date: {df_last_date}, ref_time: {ref_time}, elapsed_seconds: {elapsed_seconds}, timeframe_seconds: {timeframe_seconds}, threshold: {threshold}, index: {index}"
    )

    return df.iloc[index], df.index[index]


# 数量限制
def amount_limit(ex: BitgetExchange, df, symbol, amount, amount_max_limit):
    side = None
    last, last_date = get_signal_record(df)
    # 获取当前仓位
    position = ex.fetch_position(symbol)
    # print(f"position: {position}")

    side = "buy" if last["buy"] == 1 else "sell" if last["sell"] == 1 else None
    if side is None:
        return side

    print(f"strategy [{side}] signal: [{last_date} {last['close']}]")
    # 如果有新的信号，先取消所有订单
    ex.cancel_orders(symbol)

    try:
        # 判断是否有买入信号
        if side == "buy":
            # 判断是否有空仓
            if position["short"]["qty"] > 0:
                # 平空
                print(
                    f"close short: {last['close']}, profit: {position['short']['upnl']}"
                )
                ex.close_position(symbol, "buy", amount)
                # 如果全部平仓，反向开单
                if amount == position["short"]["qty"]:
                    # 开多
                    print(
                        f"all short position have been closed. open long: {last['close']}"
                    )
                    ex.create_order_limit(symbol, "buy", amount, last["close"])

            else:
                if position["long"]["qty"] < amount_max_limit:
                    # 开多
                    print(f"open long: {last['close']}")
                    ex.create_order_limit(symbol, "buy", amount, last["close"])
                else:
                    # 超出最大仓位
                    print(f"long position is max: {position['long']['qty']}")
                    # 如果是盈利的，平仓
                    if position["long"]["upnl"] > 0:
                        print(
                            f"close long: {last['close']}, profit: {position['long']['upnl']}"
                        )
                        ex.close_position(symbol, "sell", position["long"]["qty"])

        elif side == "sell":
            # 判断是否有多仓
            if position["long"]["qty"] > 0:
                # 平多
                print(
                    f"close long: {last['close']}, profit: {position['long']['upnl']}"
                )
                ex.close_position(symbol, "sell", amount)
                # 如果全部平仓，反向开单
                if amount == position["long"]["qty"]:
                    # 开多
                    print(
                        f"all long position have been closed. open short: {last['close']}"
                    )
                    ex.create_order_limit(symbol, "sell", amount, last["close"])
            else:
                if position["short"]["qty"] < amount_max_limit:
                    # 开空
                    print(f"open short: {last['close']}")
                    ex.create_order_limit(symbol, "sell", amount, last["close"])
                else:
                    # 超出最大仓位
                    print(f"short position is max: {position['short']['qty']}")
                    # 如果是盈利的，平仓
                    if position["short"]["upnl"] > 0:
                        print(
                            f"close short: {last['close']}, profit: {position['short']['upnl']}"
                        )
                        ex.close_position(symbol, "buy", position["short"]["qty"])

    except Exception as e:
        print(f"An unknown error occurred in amount_limit(): {e}")
    return side
