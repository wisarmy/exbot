use thiserror::Error;

pub type Result<T> = std::result::Result<T, ExbotError>;

#[derive(Error, Debug)]
pub enum ExbotError {
    #[error("invalid header (expected {expected:?}, found {found:?})")]
    InvalidHeader { expected: String, found: String },
    #[error("unknown error")]
    Unknown,
    #[error("serde json error")]
    SerdeJson(#[from] serde_json::Error),
    #[error("reqwest error")]
    Reqwest(#[from] reqwest::Error),
}
