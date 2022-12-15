use crate::apis::{ToUrl, API};
use anyhow::Result;
use reqwest::blocking::Client as InnerClient;
use reqwest::header::{HeaderMap, HeaderName, HeaderValue};

pub mod binance;

pub trait RequestSigned {
    fn signed(&self) -> Result<RequestData>;
}
#[derive(Debug, Clone)]
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
    /// merge input RequestData item, overwriting if exist
    pub fn merge(mut self, reqwest_data: RequestData) -> Self {
        reqwest_data.headers.into_iter().for_each(|(key, val)| {
            self.headers.insert(key.unwrap(), val);
        });
        reqwest_data.query.into_iter().for_each(|(key, val)| {
            self.query.push((key, val));
        });
        self
    }
}

#[derive(Clone, Default)]
pub struct Client<C = binance::Client>
where
    C: ToUrl + RequestSigned,
{
    inner_client: InnerClient,
    ex_client: C,
}

impl<C> Client<C>
where
    C: ToUrl + RequestSigned,
{
    pub fn new(ex_client: C) -> Self {
        Self {
            ex_client,
            inner_client: InnerClient::builder()
                .pool_idle_timeout(None)
                .build()
                .unwrap(),
        }
    }

    pub fn get<T: serde::de::DeserializeOwned>(
        &self,
        api: API,
        request_data: RequestData,
    ) -> Result<T> {
        Ok(self
            .inner_client
            .get(self.ex_client.to_url(api))
            .query(request_data.query.as_slice())
            .headers(request_data.headers)
            .send()?
            .json::<T>()?)
    }

    pub fn get_signed<T: serde::de::DeserializeOwned>(
        &self,
        api: API,
        request_data: RequestData,
    ) -> Result<T> {
        let request_data = self.ex_client.signed()?.merge(request_data);
        Ok(self
            .inner_client
            .get(self.ex_client.to_url(api))
            .query(request_data.query.as_slice())
            .headers(request_data.headers)
            .send()?
            .json::<T>()?)
    }

    pub fn post<T: serde::de::DeserializeOwned>(
        &self,
        api: API,
        request_data: RequestData,
    ) -> Result<T> {
        Ok(self
            .inner_client
            .post(self.ex_client.to_url(api))
            .headers(request_data.headers)
            .send()?
            .json::<T>()?)
    }
    pub fn put<T: serde::de::DeserializeOwned>(
        &self,
        api: API,
        request_data: RequestData,
    ) -> Result<T> {
        Ok(self
            .inner_client
            .put(self.ex_client.to_url(api))
            .headers(request_data.headers)
            .send()?
            .json::<T>()?)
    }
    pub fn delete<T: serde::de::DeserializeOwned>(
        &self,
        api: API,
        request_data: RequestData,
    ) -> Result<T> {
        Ok(self
            .inner_client
            .delete(self.ex_client.to_url(api))
            .headers(request_data.headers)
            .send()?
            .json::<T>()?)
    }
}

#[cfg(test)]
mod tests {
    use serde_json::Value;

    use crate::apis::spot::{kline::Kline, Spot};

    use super::*;
    #[test]
    fn kline_should_work() {
        let request_data = RequestData::default()
            .add_query(("symbol", "NEARUSDT"))
            .add_query(("interval", "1m"))
            .add_query(("limit", "5"));
        let response = Client::new(binance::Client::default())
            .get::<Vec<Vec<Value>>>(API::Spot(Spot::Klines), request_data);
        assert!(response.is_ok());
        let data = response
            .unwrap()
            .into_iter()
            .map(|v| v.try_into().unwrap())
            .collect::<Vec<Kline<binance::Client>>>();
        assert_eq!(data.len(), 5);
    }
}
