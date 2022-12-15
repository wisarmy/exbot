use exbot::{
    apis::{
        spot::{kline::Kline, Spot},
        API,
    },
    client::{binance, Client, RequestData},
};
use serde_json::{json, Value};

fn main() {
    let reqwest_data = RequestData::default()
        .add_query(("symbol", "NEARUSDT"))
        .add_query(("interval", "1m"))
        .add_query(("limit", "5"));
    let response = Client::<binance::Client>::default()
        .get::<Vec<Vec<Value>>>(API::Spot(Spot::Klines), reqwest_data);
    assert!(response.is_ok());
    let data = response
        .unwrap()
        .into_iter()
        .map(|v| v.try_into().unwrap())
        .collect::<Vec<Kline<binance::Client>>>();
    assert_eq!(data.len(), 5);
    println!("{}", json!(data));
}
