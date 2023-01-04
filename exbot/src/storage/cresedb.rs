use once_cell::sync::Lazy;
use std::sync::Arc;
use tracing::warn;

use async_trait::async_trait;
use ceresdb_client_rs::{
    db_client::{Builder, DbClient},
    model::{request::QueryRequest, QueryResponse},
    RpcContext,
};

use crate::error::Result;

use super::Storage;

static CREATE_TABLES: Lazy<Vec<(&str, &str)>> = Lazy::new(|| {
    vec![(
        "exbot_klines",
        r#"CREATE TABLE exbot_klines (
        symbol string TAG,
        interval string TAG,
        open_time uint64,
        open_price string,
        high_price string,
        low_price string,
        close_price string,
        volume string,
        close_time uint64,
        quote_volume string,
        trades_number uint64,
        taker_buy_base_volume string,
        taker_buy_quote_volume string,
        t timestamp NOT NULL,
        TIMESTAMP KEY(t)) ENGINE=Analytic with (enable_ttl='false')"#,
    )]
});
pub struct CeresDb {
    client: Arc<dyn DbClient>,
    ctx: RpcContext,
}
impl CeresDb {
    pub fn new(endpoint: impl Into<String>) -> Self {
        let client = Builder::new(
            endpoint.into(),
            ceresdb_client_rs::db_client::Mode::Standalone,
        )
        .build();
        let ctx = RpcContext::new("public".to_string(), "".to_string());
        Self { client, ctx }
    }
}
#[async_trait]
impl Storage for CeresDb {
    type QueryItem = QueryResponse;
    async fn init(&self) -> Result<()> {
        for (_index, (table, create_table_sql)) in CREATE_TABLES.iter().enumerate() {
            // check if the table exists
            let table_exist = self
                .client
                .query(
                    &self.ctx,
                    &QueryRequest {
                        metrics: vec![table.to_string()],
                        ql: format!("show tables like {}", table).to_string(),
                    },
                )
                .await?;
            if table_exist.rows.len() > 0 {
                warn!("table {} already exists, ignored", table);
                continue;
            }

            let req = QueryRequest {
                metrics: vec![table.to_string()],
                ql: create_table_sql.to_string(),
            };

            self.client.query(&self.ctx, &req).await?;
        }
        Ok(())
    }
    async fn query(&self, metrics: Vec<String>, sql: String) -> Result<Self::QueryItem> {
        let req = QueryRequest {
            metrics,
            ql: sql.to_string(),
        };

        let item = self.client.query(&self.ctx, &req).await?;
        Ok(item)
    }
}

#[cfg(test)]
mod tests {
    use chrono::Local;
    use std::sync::Arc;

    use ceresdb_client_rs::{
        db_client::{Builder, DbClient},
        model::{request::QueryRequest, value::Value, write::WriteRequestBuilder},
        RpcContext,
    };

    pub const TABLE: &str = "cresedb_test";

    #[tokio::test]
    #[ignore = "need cresedb server"]
    async fn read_write_should_work() {
        let client = Builder::new(
            "127.0.0.1:8831".to_string(),
            ceresdb_client_rs::db_client::Mode::Standalone,
        )
        .build();
        let rpc_ctx = RpcContext::new("public".to_string(), "".to_string());

        // create table
        create_table(&client, &rpc_ctx).await;
        // write
        write(&client, &rpc_ctx).await;
        // read
        read(&client, &rpc_ctx).await;
        // write raw
        write_raw(&client, &rpc_ctx).await;
        // drop table
        drop_table(&client, &rpc_ctx).await;
    }

    async fn create_table(client: &Arc<dyn DbClient>, rpc_ctx: &RpcContext) {
        let create_table_sql = format!(
            r#"CREATE TABLE {} (
        str_tag string TAG,
        int_tag int32 TAG,
        var_tag varbinary TAG,
        str_field string,
        int_field int32,
        bin_field varbinary,
        t timestamp NOT NULL,
        TIMESTAMP KEY(t)) ENGINE=Analytic with (enable_ttl='false')"#,
            TABLE
        );
        let req = QueryRequest {
            metrics: vec![TABLE.to_string()],
            ql: create_table_sql.to_string(),
        };
        let resp = client.query(rpc_ctx, &req).await.unwrap();
        assert_eq!(resp.affected_rows, 0);
    }

    async fn drop_table(client: &Arc<dyn DbClient>, rpc_ctx: &RpcContext) {
        let drop_table_sql = format!("DROP TABLE {}", TABLE);
        let req = QueryRequest {
            metrics: vec![TABLE.to_string()],
            ql: drop_table_sql.to_string(),
        };
        let resp = client.query(rpc_ctx, &req).await.unwrap();
        assert_eq!(resp.affected_rows, 0);
    }

    async fn write(client: &Arc<dyn DbClient>, rpc_ctx: &RpcContext) {
        let ts1 = Local::now().timestamp_millis();
        let mut write_req_builder = WriteRequestBuilder::default();
        // first row
        write_req_builder
            .row_builder()
            .metric(TABLE.to_string())
            .timestamp(ts1)
            .tag("str_tag".to_string(), Value::String("tag_val1".to_string()))
            .tag("int_tag".to_string(), Value::Int32(42))
            .tag(
                "var_tag".to_string(),
                Value::Varbinary(b"tag_bin_val1".to_vec()),
            )
            .field(
                "str_field".to_string(),
                Value::String("field_val1".to_string()),
            )
            .field("int_field".to_string(), Value::Int32(42))
            .field(
                "bin_field".to_string(),
                Value::Varbinary(b"field_bin_val1".to_vec()),
            )
            .finish()
            .unwrap();

        // second row
        write_req_builder
            .row_builder()
            .metric(TABLE.to_string())
            .timestamp(ts1 + 40)
            .tag("str_tag".to_string(), Value::String("tag_val2".to_string()))
            .tag("int_tag".to_string(), Value::Int32(43))
            .tag(
                "var_tag".to_string(),
                Value::Varbinary(b"tag_bin_val2".to_vec()),
            )
            .field(
                "str_field".to_string(),
                Value::String("field_val2".to_string()),
            )
            .field(
                "bin_field".to_string(),
                Value::Varbinary(b"field_bin_val2".to_vec()),
            )
            .finish()
            .unwrap();

        let write_req = write_req_builder.build();
        let res = client.write(rpc_ctx, &write_req).await.unwrap();
        assert_eq!(res.success, 2);
    }

    async fn write_raw(client: &Arc<dyn DbClient>, rpc_ctx: &RpcContext) {
        let req = QueryRequest {
            metrics: vec![TABLE.to_string()],
            ql: format!(
                r#"insert into {} (t, str_tag, int_tag, str_field) values ({}, '{}', {}, '{}')"#,
                TABLE,
                Local::now().timestamp_millis(),
                "str_tag3",
                44,
                "str_field3"
            ),
        };
        let resp = client.query(rpc_ctx, &req).await.unwrap();
        assert_eq!(resp.affected_rows, 1);
    }

    async fn read(client: &Arc<dyn DbClient>, rpc_ctx: &RpcContext) {
        let req = QueryRequest {
            metrics: vec![TABLE.to_string()],
            ql: format!("select * from {}", TABLE),
        };
        let resp = client.query(rpc_ctx, &req).await.unwrap();
        assert_eq!(resp.rows.len(), 2);
    }
}
