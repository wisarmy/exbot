import argparse
import logging
import pandas as pd
from config import load_config
import numpy as np

from exchanges import exchange
from download import download_candles
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

app = Dash(__name__)

app.layout = html.Div([
    dcc.Interval(id='update', interval=5*1000, n_intervals=0),
    dcc.Graph(id="graph"),
])

pd.set_option('display.max_rows', 10)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='exbot for python')
    parser.add_argument('-c', '--config', type=str, required=True, help='config file path')
    parser.add_argument('--symbol', type=str, required=True, help='The trading symbol to use')
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

    ohlcv = download_candles(ex, args.symbol, args.timeframe)

    df = pd.DataFrame(ohlcv, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True).dt.tz_convert('Asia/Shanghai')
    # get last 200 rows
    df = df.tail(200).reset_index(drop=True)
    print(df)
    @app.callback(
        Output("graph", "figure"),
        Input("update", "n_intervals")
    )
    def display_candlestick(n):
        global df
        # last_date_timestamp = int(df.iloc[-1]['date'].timestamp()*1000)
        last_date = df.iloc[-1]['date']
        # 只获取最新的蜡烛图，会导致最终的蜡烛图没更新到最新就切换到下一个蜡烛图了，造成数据不准确
        # 所以获取最后两根蜡烛图去修复上一根蜡烛图的数据
        last_candles: list = ex.get_candles(args.symbol, args.timeframe, None, 2)

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
        print(df)

        fig = go.Figure(go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], showlegend=True))
        fig.add_trace(go.Scatter(x=[df['date'].iloc[0], df['date'].iloc[-1]], y=[df['close'].iloc[-1],df['close'].iloc[-1]], mode='lines', name='Current Price',line=dict(dash='dash')))
        # 添加价格注释
        fig.add_annotation(x=df['date'].iloc[-1], y=df['close'].iloc[-1],
                   text=f'Current Price: {df["close"].iloc[-1]:.4f}',
                   showarrow=False,
                   arrowhead=0,
                   xanchor='left',
                    )

        fig.update_layout(
            height=800,
            title=args.symbol,
            xaxis_rangeslider_visible=False
        )
        fig.update_traces(
            visible=True,
            opacity=0.9,
        )

        return fig

    app.run_server(debug=True)



    
