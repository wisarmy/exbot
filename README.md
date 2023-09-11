# Exbot
[![MIT](https://img.shields.io/github/license/wisarmy/exbot)](https://github.com/wisarmy/exbot/blob/main/LICENSE)
[![Rust](https://img.shields.io/github/actions/workflow/status/wisarmy/exbot/rust.yml)](https://github.com/wisarmy/exbot/actions)
[![Code](https://img.shields.io/github/languages/code-size/wisarmy/exbot)](https://github.com/wisarmy/exbot)

## What is Exbot?

Exbot is a blockchain exchange bot written in rust that contains trading, charts, strategies, and alerts. As many ex/dex as possible support.

# Exobt for python

## Quick Start
First change to the directory
```bash
cd exbot-py
```
### Installation
```bash
pip install -r requirements.txt
```

## Exchange Support
[![bitget](https://user-images.githubusercontent.com/1294454/195989417-4253ddb0-afbe-4a1c-9dea-9dbcd121fa5d.jpg)](https://partner.bitget.com/bg/QAEL40)

## Chart
Run chart.py
```bash
python chart.py -c configs/config.toml -t 1m --strategy macd -i 10
```
![Chart Sample Image](resources/images/chart.png)

## Strategy
Run bot.py
```bash
# amount is the number of symbol
python bot.py -c configs/config.toml --symbol NEAR/USDT:USDT -t 15m --strategy macd --amount 100 --amount_max=100 -i 10
# uamount is the number of usdt
python bot.py -c configs/config.toml --symbol NEAR/USDT:USDT -t 15m --strategy ichiv1 --uamount 100 --uamount_max=1000 -i 10
```
### Position chart
```bash
python charts/position.py
```
![Positoin Chart Sample Image](resources/images/chart_position.png)

## Backtesting
Run Backtesting.py
```
python backtesting.py -c configs/config.toml --symbol NEAR/USDT:USDT --strategy ichiv1 -t 15m --days 30
```


