use std::io;

use thiserror::Error;

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
    #[error("ceresdb client error")]
    CeresDb(#[from] ceresdb_client_rs::Error),
}

#[macro_export]
macro_rules! exbot_error {
    ($($arg:tt)*) => {{
        $crate::error::ExbotError::Error(format!($($arg)*))
    }}
}
