import datetime
import unittest
import chart
from config import load_config
from exchanges import exchange
import pandas as pd

from strategies.strategy import get_signal_record


def get_ex():
    config = load_config("configs/config.toml")
    ex = exchange.Exchange(config.exchange).get()
    ex.load_markets()
    print(ex.id())
    return ex


def update_ohlcv():
    df = chart.get_charting("NEAR/USDT:USDT", "1m", get_ex())
    # save df to file
    df.to_json("tests/ohlcv.json")


def get_df():
    return pd.read_json("tests/ohlcv.json")


class TestDataframeMethods(unittest.TestCase):
    def test_time_deltas(self):
        df = get_df()
        assert len(df) > 2
        timedeltas = df.index.to_series().diff().min()
        assert timedeltas.total_seconds() == 60
        timedeltas = df.index[-1] - df.index[-2]
        assert timedeltas.total_seconds() == 60

    def test_get_signal_record(self):
        df = get_df()
        assert len(df) > 2
        # < threshold
        testtime = datetime.datetime.strptime(
            "2023-08-31 02:09:49.158214", "%Y-%m-%d %H:%M:%S.%f"
        )
        last, last_date = get_signal_record(df, ref_time=testtime)
        assert last_date == df.index[-2]
        # > threshold
        testtime = datetime.datetime.strptime(
            "2023-08-31 02:09:51.158214", "%Y-%m-%d %H:%M:%S.%f"
        )
        last, last_date = get_signal_record(df, ref_time=testtime)
        assert last_date == df.index[-1]


if __name__ == "__main__":
    unittest.main()
