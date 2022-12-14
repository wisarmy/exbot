use thiserror::Error;

#[derive(Error, Debug)]
pub enum ExbotError {
    #[error("invalid header (expected {expected:?}, found {found:?})")]
    InvalidHeader { expected: String, found: String },
    #[error("unknown error")]
    Unknown,
    #[error("json error")]
    Json(#[from] serde_json::Error),
}
