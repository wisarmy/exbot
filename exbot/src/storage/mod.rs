use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use tracing::error;

use crate::{error::Result, exbot_error};

use self::cresedb::CeresDb;

pub mod cresedb;
#[async_trait]
pub trait Storage {
    type QueryItem;
    async fn init(&self) -> Result<()>;
    async fn query(&self, metrics: Vec<String>, sql: String) -> Result<Self::QueryItem>;
}

#[derive(clap::ValueEnum, Serialize, Deserialize, Debug, Clone, Default)]
#[serde(rename_all = "lowercase")]
pub enum DbType {
    #[default]
    CeresDb,
    Redis,
}
#[derive(Serialize, Deserialize, Debug, Clone, Default)]
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
        _ => Err(exbot_error!("not support db type")),
    }
    .inspect_err(|e| error!("init err: {:?}", e))
}

#[cfg(test)]
mod tests {
    use super::*;

    const TABLE: &str = "exbot_test";
    #[tokio::test]
    #[ignore = "need cresedb server"]
    async fn test_store_ceresdb_query() {
        let store = CeresDb::new("127.0.0.1:8831");
        let query_result = store
            .query(
                vec![TABLE.to_string()],
                format!(
                    "create table {} (t timestamp NOT NULL, TIMESTAMP KEY(t))",
                    TABLE
                ),
            )
            .await
            .unwrap();
        assert_eq!(query_result.affected_rows, 0);
        let query_result = store
            .query(vec![TABLE.to_string()], format!("select * from {}", TABLE))
            .await
            .unwrap();
        assert_eq!(query_result.rows.len(), 0);
        let query_result = store
            .query(vec![TABLE.to_string()], format!("drop table {}", TABLE))
            .await
            .unwrap();
        assert_eq!(query_result.affected_rows, 0);
    }
}
