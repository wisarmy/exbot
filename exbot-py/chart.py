import argparse
from datetime import timedelta
import logging
import pandas as pd
from config import load_config

from exchanges import exchange
from download import download_candles
import plotly.graph_objects as go
from dash import Dash, State, dcc, html, Input, Output

app = Dash(__name__)

app.layout = html.Div([
    dcc.Dropdown(['NEAR/USDT:USDT', 'BTC/USDT:USDT', 'ETH/USDT:USDT'], 'NEAR/USDT:USDT', id='symbol'),
    dcc.Interval(id='update', interval=5*1000, n_intervals=0),
    dcc.Graph(id="graph",
        config={
            'scrollZoom': True,  # 启用或禁用滚动缩放
        }
    ),
])

pd.set_option('display.max_rows', 10)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')


# candle data
chardata = {}


def get_chart(ex, symbol, timeframe, limit):
    ohlcv = download_candles(ex, symbol, timeframe)
    df = pd.DataFrame(ohlcv, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True).dt.tz_convert('Asia/Shanghai')
    # get last some rows
    df = df.tail(limit).reset_index(drop=True)
    chardata[symbol] = df


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='exbot for python')
    parser.add_argument('-c', '--config', type=str, required=True, help='config file path')
    # parser.add_argument('--symbol', type=str, required=True, help='The trading symbol to use')
    parser.add_argument('-t', '--timeframe', type=str, required=True, help='timeframe: 1m 5m 15m 30m 1h 4h 1d 1w 1M')
    # add arg verbose
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info('exbot charting ....')

    config = load_config(args.config)
    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    print(ex.id())

    @app.callback(
        Output("graph", "figure"),
        Input("update", "n_intervals"),
        Input("symbol", "value"),
        State("graph", "relayoutData")

    )
    def display_candlestick(n, symbol, relayout_data):
        print(f"symbol: {symbol}")
        if symbol not in chardata:
            get_chart(ex, symbol, args.timeframe, 2000)
        df = chardata[symbol] 
        # last_date_timestamp = int(df.iloc[-1]['date'].timestamp()*1000)
        last_date = df.iloc[-1]['date']
        # 只获取最新的蜡烛图，会导致最终的蜡烛图没更新到最新就切换到下一个蜡烛图了，造成数据不准确
        # 所以获取最后两根蜡烛图去修复上一根蜡烛图的数据
        last_candles: list = ex.get_candles(symbol, args.timeframe, None, 2)

        #print(last_candles)
        current_candle: list = last_candles[-1]
        last_candle: list = last_candles[-2]

        current_candle[0] = pd.Timestamp(current_candle[0], unit='ms', tz='Asia/Shanghai')
        last_candle[0] = pd.Timestamp(last_candle[0], unit='ms', tz='Asia/Shanghai')
        
        if last_date == current_candle[0]:
            df.iloc[-1] = current_candle
        elif last_date < current_candle[0]: 
            df.loc[len(df)] = current_candle
            # 添加新的蜡烛图后，需要把上一根蜡烛图的数据修复
            df.iloc[-2] = last_candle

        # 限制初始显示的数据范围为最后200条
        df_display = df.tail(200)
        print(df_display)

        fig =  go.Figure(data=[go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
        current_price = df['close'].iloc[-1]
        color = 'green' if current_price >= df['close'].iloc[-2] else 'red';
        fig.add_shape(
            type='line',
            y0=current_price, y1=current_price,
            x0=df['date'].iloc[0], x1=df['date'].iloc[-1]+timedelta(days=1),
            line=dict(
                color=color,
                width=1,
                dash='dash',
            ),
        )
        # 在Y轴上显示当前价格
        fig.add_annotation(
            xref='paper', yref='y',
            x=1.035, y=current_price,
            text="{:.4f}".format(current_price),
            showarrow=False,
            font=dict(
                size=12,
                color='White',
            ),
            bgcolor=color,
            bordercolor=color,
            borderwidth=1,
        )

        fig.update_layout(
            height=800,
            title=symbol,
            xaxis=dict(
                rangeslider=dict(
                    visible=False
                ),
                range=[df_display['date'].iloc[0], df_display['date'].iloc[-1]+timedelta(minutes=100)],
            ),
            yaxis=dict(
                side='right',
                range=[df_display['low'].min()*0.99, df_display['high'].max()*1.01],

            ),
            dragmode='pan',
        )
        if relayout_data:
            layout = fig['layout']
            if 'xaxis.range[0]' in relayout_data:
                layout['xaxis']['range'] = [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']]
            if 'yaxis.range[0]' in relayout_data:
                layout['yaxis']['range'] = [relayout_data['yaxis.range[0]'], relayout_data['yaxis.range[1]']]
            fig['layout'] = layout
        return fig

    app.run_server(debug=True)



    
