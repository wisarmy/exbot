use std::marker::PhantomData;

use serde::{Deserialize, Serialize};
use serde_json::{from_value, Value};

use crate::{client::binance, error::ExbotError};

/// Kline response item
#[derive(Debug, Default, Serialize, Deserialize)]
pub struct Kline<Client> {
    /// k线开盘时间
    pub open_time: u64,
    /// 开盘价
    pub open_price: String,
    /// 最高价
    pub high_price: String,
    /// 最低价
    pub low_price: String,
    /// 收盘价(当前K线未结束的即为最新价)
    pub close_price: String,
    /// 成交量
    pub volume: String,
    /// k线收盘时间
    pub close_time: u64,
    /// 成交额
    pub asset_volume: String,
    /// 成交笔数
    pub trades_number: u64,
    /// 主动买入成交量
    pub taker_buy_volume: String,
    /// 主动买入成交额
    pub taker_buy_asset_volume: String,
    _marker: PhantomData<Client>,
}

impl TryFrom<Vec<Value>> for Kline<binance::Client> {
    type Error = ExbotError;
    fn try_from(value: Vec<Value>) -> Result<Self, Self::Error> {
        Ok(Self {
            open_time: from_value(value.get(0).unwrap_or(&Value::Null).clone()).unwrap_or_default(),
            open_price: from_value(value.get(1).unwrap_or(&Value::Null).clone())
                .unwrap_or_default(),
            high_price: from_value(value.get(2).unwrap_or(&Value::Null).clone())
                .unwrap_or_default(),
            low_price: from_value(value.get(3).unwrap_or(&Value::Null).clone()).unwrap_or_default(),
            close_price: from_value(value.get(4).unwrap_or(&Value::Null).clone())
                .unwrap_or_default(),
            volume: from_value(value.get(5).unwrap_or(&Value::Null).clone()).unwrap_or_default(),
            close_time: from_value(value.get(6).unwrap_or(&Value::Null).clone())
                .unwrap_or_default(),
            asset_volume: from_value(value.get(7).unwrap_or(&Value::Null).clone())
                .unwrap_or_default(),
            trades_number: from_value(value.get(8).unwrap_or(&Value::Null).clone())
                .unwrap_or_default(),
            taker_buy_volume: from_value(value.get(9).unwrap_or(&Value::Null).clone())
                .unwrap_or_default(),
            taker_buy_asset_volume: from_value(value.get(10).unwrap_or(&Value::Null).clone())
                .unwrap_or_default(),
            _marker: PhantomData::default(),
        })
    }
}
