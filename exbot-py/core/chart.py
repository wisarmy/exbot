from datetime import timedelta
import time
import pandas as pd
import talib
from core.logger import logger
from core.candle import get_candles
import plotly.graph_objects as go

chartdata = {}
# display size in fig
chart_display_size = 200
data_update_interval = 10
data_updated = 0.0


def get_chart(ex, symbol, timeframe, days=7):
    ohlcv = get_candles(ex, symbol, timeframe, days)
    df = pd.DataFrame(ohlcv, columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"], unit="ms", utc=True).dt.tz_convert(
        "Asia/Shanghai"
    )
    # get last some rows
    df.set_index("date", inplace=True)
    if chartdata.get(symbol) is None:
        chartdata[symbol] = {}
    chartdata[symbol][timeframe] = df


# 绘制蜡烛图
def draw_fig_candle(df):
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df.index,
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
            )
        ]
    )
    current_price = df["close"].iloc[-1]
    color = "green" if current_price >= df["close"].iloc[-2] else "red"
    fig.add_shape(
        type="line",
        y0=current_price,
        y1=current_price,
        x0=df.index[0],
        x1=df.index[-1] + timedelta(days=1),
        line=dict(
            color=color,
            width=1,
            dash="dash",
        ),
    )
    # 在Y轴上显示当前价格
    fig.add_annotation(
        xref="paper",
        yref="y",
        x=1.035,
        y=current_price,
        text="{:.4f}".format(current_price),
        showarrow=False,
        font=dict(
            size=12,
            color="White",
        ),
        bgcolor=color,
        bordercolor=color,
        borderwidth=1,
    )
    cross_bgs = []
    cross_bg_default = dict(
        start=0,
        end=0,
        color="",
    )
    cross_bg = cross_bg_default
    for index, row in df.iterrows():
        if "buy_price" not in row:
            continue
        # price = row['buy_price']
        # date = row['date']
        # if price is not None:
        # xdate = date.strftime('%Y-%m-%d %H:%M:%S%z')
        # # fig 在买入点的价格位置添加一个向上的三角符号
        # fig.add_annotation(
        # dict(
        # x=xdate,
        # y=price,
        # text="▲",
        # showarrow=False,
        # font=dict(
        # family="Courier New, monospace",
        # size=11,
        # color="#ffffff"
        # ),
        # align="center",
        # arrowcolor="LightSeaGreen",
        # arrowsize=1,
        # arrowwidth=1,
        # bgcolor="LightSeaGreen",
        # opacity=0.8
        # )
        # )

    return fig


def draw_fig_cross_bg(fig, df, yaxis_range):
    # print(f'yaxis_range: {yaxis_range} {df["date"].iloc[0]} {df["date"].iloc[-1]}')
    cross_bgs = []
    cross_bg_default = dict(
        start=0,
        end=0,
        color="",
    )
    cross_bg = cross_bg_default
    for index, row in df.iterrows():
        if row["cross"] != 0:
            if cross_bg["start"] == 0:
                cross_bg["start"] = index
                cross_bg["color"] = (
                    "rgba(0, 255, 0, 0.2)"
                    if row["cross"] == 1
                    else "rgba(255, 0, 0, 0.2)"
                )
            else:
                cross_bg["end"] = index
                cross_bgs.append(cross_bg.copy())
                cross_bg = cross_bg_default
                cross_bg["start"] = index
                cross_bg["color"] = (
                    "rgba(0, 255, 0, 0.2)"
                    if row["cross"] == 1
                    else "rgba(255, 0, 0, 0.2)"
                )
    # 最后一个cross_bg
    if cross_bg["start"] != 0:
        cross_bg["end"] = df.index[-1]
        cross_bgs.append(cross_bg.copy())

    for cross_bg in cross_bgs:
        fig.add_shape(
            dict(
                type="rect",
                xref="x",
                yref="y",
                x0=cross_bg["start"],
                y0=yaxis_range[0],
                x1=cross_bg["end"],
                y1=yaxis_range[1],
                line=dict(
                    color=cross_bg["color"],
                    width=1,
                ),
                fillcolor=cross_bg["color"],
                opacity=0.5,
                layer="below",
                line_width=0,
            )
        )
    return fig


# 绘制MACD指标
def draw_fig_macd(df):
    close_prices = df["close"].values  # 获取收盘价的数据
    # 计算MACD指标
    # 设置参数
    fast_period = 12
    slow_period = 26
    signal_period = 9
    macd, signal, hist = talib.MACD(
        close_prices, fast_period, slow_period, signal_period
    )
    macd_y_min = min(
        hist[-chart_display_size:].min(),
        macd[-chart_display_size:].min(),
        signal[-chart_display_size:].min(),
    )
    macd_y_max = max(
        hist[-chart_display_size:].max(),
        macd[-chart_display_size:].max(),
        signal[-chart_display_size:].max(),
    )
    # 画MACD指标
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=macd,
            name="DIF",
            mode="lines",
            line=dict(color="orange", width=1),
            yaxis="y2",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=signal,
            name="DEA",
            mode="lines",
            line=dict(color="blue", width=1),
            yaxis="y2",
        )
    )
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=hist,
            name="MACD",
            marker=dict(color="grey"),
            yaxis="y2",
        )
    )

    return fig, dict(range=[macd_y_min, macd_y_max])


# 绘制鼠标点击的垂直线
def draw_fig_with_click_data(fig, click_data, df, macd_yaxis_range):
    if click_data is not None:
        if "x" in click_data["points"][0]:
            x = click_data["points"][0]["x"]
            xdate = (
                pd.to_datetime(x)
                .tz_localize("Asia/Shanghai")
                .strftime("%Y-%m-%d %H:%M:%S%z")
            )
            shape = dict(
                type="line",
                x0=xdate,
                y0=min(macd_yaxis_range["range"][0], df["low"].min()) * 0.8,
                x1=xdate,
                y1=max(macd_yaxis_range["range"][1], df["high"].max()) * 1.2,
                line=dict(
                    color="black",
                    width=1,
                    dash="dash",
                ),
            )
            fig.add_shape(shape, row=1, col=1)
            fig.add_shape(shape, row=2, col=1)


# 绘制鼠标悬停的垂直线
def draw_fig_with_hover_data(fig, hover_data, df, macd_yaxis_range):
    if hover_data is not None:
        if "x" in hover_data["points"][0]:
            x = hover_data["points"][0]["x"]
            xdate = (
                pd.to_datetime(x)
                .tz_localize("Asia/Shanghai")
                .strftime("%Y-%m-%d %H:%M:%S%z")
            )
            shape = dict(
                type="line",
                x0=xdate,
                y0=min(macd_yaxis_range["range"][0], df["low"].min()) * 0.8,
                x1=xdate,
                y1=max(macd_yaxis_range["range"][1], df["high"].max()) * 1.2,
                line=dict(
                    color="darkgrey",
                    width=1,
                    dash="dot",
                ),
            )
            fig.add_shape(shape, row=1, col=1)
            fig.add_shape(shape, row=2, col=1)


def fig_relayout(fig, relayout_data):
    if relayout_data:
        layout = fig["layout"]
        if "xaxis.range[0]" in relayout_data:
            layout["xaxis"]["range"] = [
                relayout_data["xaxis.range[0]"],
                relayout_data["xaxis.range[1]"],
            ]
        if "xaxis2.range[0]" in relayout_data:
            layout["xaxis2"]["range"] = [
                relayout_data["xaxis2.range[0]"],
                relayout_data["xaxis2.range[1]"],
            ]
        if "yaxis.range[0]" in relayout_data:
            layout["yaxis"]["range"] = [
                relayout_data["yaxis.range[0]"],
                relayout_data["yaxis.range[1]"],
            ]
        if "yaxis2.range[0]" in relayout_data:
            layout["yaxis2"]["range"] = [
                relayout_data["yaxis2.range[0]"],
                relayout_data["yaxis2.range[1]"],
            ]
        fig["layout"] = layout


def get_charting(ex, symbol, timeframe, days=7):
    if symbol not in chartdata or timeframe not in chartdata[symbol]:
        get_chart(ex, symbol, timeframe, days)
    df = chartdata[symbol][timeframe]
    # last_date_timestamp = int(df.iloc[-1]['date'].timestamp()*1000)
    last_date = df.index[-1]

    # 只获取最新的蜡烛图，会导致最终的蜡烛图没更新到最新就切换到下一个蜡烛图了，造成数据不准确
    # 所以获取最后两根蜡烛图去修复上一根蜡烛图的数据
    global data_updated
    current_timestamp = time.time()
    if round(current_timestamp - data_updated) >= data_update_interval:
        data_updated = current_timestamp
        logger.debug(f"update candles: {symbol}, {data_updated}")
        last_candles: list = ex.get_candles(symbol, timeframe, None, 2)
        df_last = pd.DataFrame(
            last_candles, columns=["date", "open", "high", "low", "close", "volume"]
        )
        df_last["date"] = pd.to_datetime(
            df_last["date"], unit="ms", utc=True
        ).dt.tz_convert("Asia/Shanghai")
        df_last.set_index("date", inplace=True)

        if last_date == df_last.index[-1]:
            df.loc[last_date] = dict(zip(df.columns, df_last.iloc[-1]))
        elif last_date < df_last.index[-1]:
            df.loc[df_last.index[-1]] = dict(zip(df.columns, df_last.iloc[-1]))
            # 添加新的蜡烛图后，需要把上一根蜡烛图的数据修复
            df.loc[df_last.index[-2]] = dict(zip(df.columns, df_last.iloc[-2]))
    return df


def draw_fig_emas(fig, df, emas=[9, 22]):
    for ema in emas:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["close"].ewm(span=ema, adjust=False).mean(),
                mode="lines",
                name="EMA" + str(ema),
            )
        )
