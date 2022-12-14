use crate::apis::{ToUrl, API};
use anyhow::Result;
use reqwest::header::{HeaderMap, HeaderName, HeaderValue};
use serde::de::DeserializeOwned;

pub mod binance;

pub trait ClientApi {
    fn get<T: DeserializeOwned>(&self, api: API, reqwest_data: RequestData) -> Result<T>;
    fn post<T: DeserializeOwned>(&self, api: API, reqwest_data: RequestData) -> Result<T>;
    fn put<T: DeserializeOwned>(&self, api: API, reqwest_data: RequestData) -> Result<T>;
    fn delete<T: DeserializeOwned>(&self, api: API, reqwest_data: RequestData) -> Result<T>;
}
pub struct RequestData {
    headers: HeaderMap,
    query: Vec<(&'static str, &'static str)>,
}

impl Default for RequestData {
    fn default() -> Self {
        Self {
            headers: HeaderMap::new(),
            query: vec![],
        }
    }
}

impl RequestData {
    pub fn add_header(mut self, key: &'static str, val: &'static str) -> Self {
        self.headers
            .insert(HeaderName::from_static(key), HeaderValue::from_static(val));
        self
    }
    pub fn add_query(mut self, value: (&'static str, &'static str)) -> Self {
        self.query.push(value);
        self
    }
}

#[derive(Clone, Default)]
pub struct Client<C = binance::Client>
where
    C: ToUrl + ClientApi,
{
    ex_client: C,
}

impl<C> Client<C>
where
    C: ToUrl + ClientApi,
{
    pub fn new(ex_client: C) -> Self {
        Self { ex_client }
    }
}

impl ClientApi for Client {
    fn get<T: DeserializeOwned>(&self, api: API, reqwest_data: RequestData) -> Result<T> {
        self.ex_client.get(api, reqwest_data)
    }
    fn post<T: DeserializeOwned>(&self, api: API, reqwest_data: RequestData) -> Result<T> {
        self.ex_client.post(api, reqwest_data)
    }
    fn put<T: DeserializeOwned>(&self, api: API, reqwest_data: RequestData) -> Result<T> {
        self.ex_client.put(api, reqwest_data)
    }
    fn delete<T: DeserializeOwned>(&self, api: API, reqwest_data: RequestData) -> Result<T> {
        self.ex_client.delete(api, reqwest_data)
    }
}

#[cfg(test)]
mod tests {
    use serde_json::Value;

    use crate::{
        apis::spot::{kline::Kline, Spot},
        client::binance::Client,
    };

    use super::*;
    #[test]
    fn kline_should_work() {
        let reqwest_data = RequestData::default()
            .add_query(("symbol", "NEARUSDT"))
            .add_query(("interval", "1m"))
            .add_query(("limit", "5"));
        let response =
            Client::default().get::<Vec<Vec<Value>>>(API::Spot(Spot::Klines), reqwest_data);
        assert!(response.is_ok());
        let data = response
            .unwrap()
            .into_iter()
            .map(|v| v.try_into().unwrap())
            .collect::<Vec<Kline<Client>>>();
        assert_eq!(data.len(), 5);
    }
}
