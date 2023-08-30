from exchanges.bitget import BitgetExchange


# 数量限制
def amount_limit(ex: BitgetExchange, df, symbol, amount, amount_max_limit):
    side = None
    # 获取最后一个变化的数据
    changing = df.iloc[-1]
    # 获取最后一个稳定的数据
    last = df.iloc[-2]
    last_date = df.index[-2]
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
                print(f"close short: {last['close']}")
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
                print(f"close long: {last['close']}")
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
