use std::io;

use axum::{
    http::{header::ToStrError, status::StatusCode},
    response::IntoResponse,
    Json,
};
use serde_json::json;
use thiserror::Error;
use tracing::warn;

pub type Result<T> = std::result::Result<T, ExbotError>;

#[derive(Error, Debug)]
pub enum ExbotError {
    #[error("invalid header (expected {expected:?}, found {found:?})")]
    InvalidHeader { expected: String, found: String },
    #[error("unknown error")]
    Unknown,
    #[error("{0}")]
    Error(String),
    #[error("io error")]
    IO(#[from] io::Error),
    #[error("toml error")]
    Toml(#[from] toml::ser::Error),
    #[error("serde json error")]
    SerdeJson(#[from] serde_json::Error),
    #[error("reqwest error")]
    Reqwest(#[from] reqwest::Error),
    #[error("sql error")]
    Sql(#[from] sqlx::error::Error),
    #[error("to str error")]
    ToStr(#[from] ToStrError),
}

#[macro_export]
macro_rules! exbot_error {
    ($($arg:tt)*) => {{
        $crate::error::ExbotError::Error(format!($($arg)*))
    }}
}

impl From<&str> for ExbotError {
    fn from(value: &str) -> Self {
        ExbotError::Error(value.to_string())
    }
}

impl IntoResponse for ExbotError {
    fn into_response(self) -> axum::response::Response {
        warn!("{:?}", self);
        let body = Json(json!({
            "error": self.to_string()
        }));
        (StatusCode::INTERNAL_SERVER_ERROR, body).into_response()
    }
}
