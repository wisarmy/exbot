use axum::{extract::State, http::HeaderMap, Json};
use serde::{Deserialize, Serialize};
use sqlx::SqlitePool;
use utoipa::ToSchema;

use crate::error::Result;

#[derive(Deserialize, Serialize, Debug, ToSchema, Clone)]
pub struct CreateOrderParam {
    #[schema(example = "NEAR/USDT:USDT")]
    symbol: String,
    side: String,
    qty: f64,
    price: f64,
    reduce_only: bool,
}
#[utoipa::path(
    post,
    path = "/mix/place_order",
    request_body = CreateOrderParam,
    responses(
        (status = 200, description = "created successfully"),
        (status = 500, description = "internal error")
    )
)]
pub async fn create_order(
    headers: HeaderMap,
    State(pool): State<SqlitePool>,
    Json(payload): Json<CreateOrderParam>,
) -> Result<()> {
    let request_id = headers
        .get("request_id")
        .ok_or("the header request_id is required")?
        .to_str()?;
    let _resp = sqlx::query!(
        "INSERT INTO mockex_orders (id, symbol, side, qty, price, reduce_only)
    VALUES (?, ?, ?, ?, ?, ?)",
        request_id,
        payload.symbol,
        payload.side,
        payload.qty,
        payload.price,
        payload.reduce_only
    )
    .execute(&pool)
    .await?;
    Ok(())
}
