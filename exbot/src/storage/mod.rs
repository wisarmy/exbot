use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use tracing::error;

use crate::{error::Result, exbot_error};

#[async_trait]
pub trait Storage {
    type QueryItem;
    async fn init(&self) -> Result<()>;
    async fn query(&self, sql: String) -> Result<Self::QueryItem>;
}

#[derive(clap::ValueEnum, Serialize, Deserialize, Debug, Clone, Default)]
#[serde(rename_all = "lowercase")]
pub enum DbType {
    #[default]
    Sqlite,
    Mysql,
}
#[derive(Serialize, Deserialize, Debug, Clone, Default)]
pub struct Config {
    pub db_type: DbType,
    pub db_endpoint: String,
}

pub async fn init(c: Config) -> Result<()> {
    match c.db_type {
        DbType::Sqlite => Ok(()),
        _ => Err(exbot_error!("not support db type")),
    }
    .inspect_err(|e| error!("init err: {:?}", e))
}
