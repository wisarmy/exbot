use async_trait::async_trait;
use tracing::error;

use crate::error::Result;

use self::cresedb::CeresDb;

pub mod cresedb;
#[async_trait]
pub trait Storage {
    async fn init(&self) -> Result<()>;
}

pub async fn init(endpoint: String) {
    let store = CeresDb::new(endpoint);
    match store.init().await {
        Err(e) => {
            error!("init err: {:?}", e);
        }
        _ => {}
    }
}
