use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use tracing::error;

use crate::error::{ExbotError, Result};

use self::cresedb::CeresDb;

pub mod cresedb;
#[async_trait]
pub trait Storage {
    async fn init(&self) -> Result<()>;
}

#[derive(clap::ValueEnum, Serialize, Deserialize, Debug, Clone)]
#[serde(rename_all = "lowercase")]
pub enum DbType {
    CeresDb,
    Redis,
}
#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Config {
    pub db_type: DbType,
    pub db_endpoint: String,
}

pub async fn init(c: Config) -> Result<()> {
    match c.db_type {
        DbType::CeresDb => {
            let store = CeresDb::new(c.db_endpoint);
            store.init().await
        }
        _ => Err(ExbotError::Error("not support db type")),
    }
    .inspect_err(|e| error!("init err: {:?}", e))
}
