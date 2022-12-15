use crate::apis::{spot::Spot, ToUrl, API};
use anyhow::Result;

use super::{RequestData, RequestSigned};

#[derive(Clone, Debug)]
#[allow(dead_code)]
pub struct Client {
    host: String,
    api_key: String,
    secret_key: String,
}

impl Client {
    pub fn new(
        host: impl Into<String>,
        api_key: impl Into<String>,
        secret_key: impl Into<String>,
    ) -> Self {
        Self {
            host: host.into(),
            api_key: api_key.into(),
            secret_key: secret_key.into(),
        }
    }
}

impl Default for Client {
    fn default() -> Self {
        Self {
            host: "https://api.binance.com".into(),
            api_key: "".into(),
            secret_key: "".into(),
        }
    }
}

impl ToUrl for Client {
    fn to_url(&self, api: API) -> String {
        let api_url = String::from(match api {
            API::Spot(route) => match route {
                Spot::Ping => "/api/v3/ping",
                Spot::Time => "/api/v3/time",
                Spot::ExchangeInfo => "/api/v3/exchangeInfo",
                Spot::Depth => "/api/v3/depth",
                Spot::Trades => "/api/v3/trades",
                Spot::HistoricalTrades => "/api/v3/historicalTrades",
                Spot::AggTrades => "/api/v3/aggTrades",
                Spot::Klines => "/api/v3/klines",
                Spot::AvgPrice => "/api/v3/avgPrice",
                Spot::UiKlines => "/api/v3/uiKlines",
                Spot::Ticker24hr => "/api/v3/ticker/24hr",
                Spot::TickerPrice => "/api/v3/ticker/price",
                Spot::TickerBookTicker => "/api/v3/ticker/bookTicker",
                Spot::Ticker => "/api/v3/ticker",
                Spot::OrderTest => "/api/v3/order/test",
                Spot::Order => "/api/v3/order",
                Spot::OpenOrders => "/api/v3/openOrders",
                Spot::OrderCancelReplace => "/api/v3/orderCancelReplace",
                Spot::AllOrders => "/api/v3/allOrders",
                Spot::OrderOco => "/api/v3/order/oco",
                Spot::OrderList => "/api/v3/orderList",
                Spot::AllOrderList => "/api/v3/allOrderList",
                Spot::OpenOrderList => "/api/v3/openOrderList",
                Spot::Account => "/api/v3/account",
                Spot::MyTrades => "/api/v3/myTrades",
                Spot::RateLimitOrder => "/api/v3/rateLimitOrder",
                Spot::UserDataStream => "/api/v3/userDataStream",
            },
        });
        format!("{}{}", self.host, api_url)
    }
}

impl RequestSigned for Client {
    fn signed(&self) -> Result<RequestData> {
        todo!()
    }
}
