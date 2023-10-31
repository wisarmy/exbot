use std::{env, net::SocketAddr};

use axum::{
    body::Body,
    http::{HeaderValue, Method, Request},
    middleware::{from_fn, Next},
    response::{Html, IntoResponse, Response},
    routing::{get, post},
    Router,
};
use clap::{Parser, Subcommand};
use exbot::{
    config::{self, Config},
    error::Result,
    services::mockex_service,
    storage::{self, DbType},
};
use sqlx::SqlitePool;
use tokio::signal;
use tower_http::cors::{Any, CorsLayer};
use tracing::{debug, info};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
use utoipa::{
    openapi::security::{ApiKey, ApiKeyValue, SecurityScheme},
    Modify, OpenApi,
};
use utoipa_redoc::{Redoc, Servable};
use uuid::Uuid;

/// Exbot mock exchange program
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    commnad: Command,
}

#[derive(Subcommand, Debug)]
enum Command {
    Init {
        #[arg(long, value_enum, default_value_t = DbType::Sqlite)]
        db_type: DbType,
        #[arg(long, default_value_t = String::from(config::root_path().join("mockex.db").to_str().unwrap()))]
        db_endpoint: String,
    },
    Daemon,
}
#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let cli = Cli::parse();
    match cli.commnad {
        Command::Init {
            db_type,
            db_endpoint,
        } => {
            // init storage
            let storage_config = storage::Config {
                db_type,
                db_endpoint,
            };
            storage::init(storage_config.clone()).await?;
            // init config
            Config {
                storage: Some(storage_config),
                mockex: Some(config::mockex::MockexConfig::default()),
            }
            .init("mockex.toml")?;
        }
        Command::Daemon => {
            info!("Initializing daemon");
            #[derive(OpenApi)]
            #[openapi(
				paths(
                    mockex_service::create_order
				),
				components(
                    schemas(mockex_service::CreateOrderParam)
				),
				modifiers(&SecurityAddon),
				tags(
					(name = "exbot mockex api", description = "Exbot mockex API")
				)
			)]
            struct ApiDoc;

            struct SecurityAddon;

            impl Modify for SecurityAddon {
                fn modify(&self, openapi: &mut utoipa::openapi::OpenApi) {
                    if let Some(components) = openapi.components.as_mut() {
                        components.add_security_scheme(
                            "api_key",
                            SecurityScheme::ApiKey(ApiKey::Header(ApiKeyValue::new("todo_apikey"))),
                        )
                    }
                }
            }

            config::with_config("mockex.toml", |c| async move {
                debug!("With config: {:?}", c);
                let pool = SqlitePool::connect(c.storage.unwrap().db_endpoint.as_str())
                    .await
                    .unwrap();
                let app = Router::new()
                    .merge(Redoc::with_url("/redoc", ApiDoc::openapi()))
                    .route("/", get(handler))
                    .route("/mix/place_order", post(mockex_service::create_order))
                    .with_state(pool)
                    .layer(from_fn(add_request_id))
                    .layer(
                        CorsLayer::new()
                            .allow_origin(Any)
                            .allow_methods(vec![
                                Method::GET,
                                Method::POST,
                                Method::OPTIONS,
                                Method::PUT,
                                Method::DELETE,
                            ])
                            .allow_headers(Any),
                    );

                let addr = c
                    .mockex
                    .clone()
                    .unwrap()
                    .addr
                    .parse::<SocketAddr>()
                    .unwrap();
                tracing::info!("listening on {}", addr);
                axum::Server::bind(&addr)
                    .serve(app.into_make_service())
                    .with_graceful_shutdown(shutdown_signal())
                    .await
                    .unwrap()
            })
            .await;
        }
    }
    Ok(())
}

async fn handler() -> Html<&'static str> {
    Html("<h1>Exbot Mockex!</h1>")
}
async fn shutdown_signal() {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {},
        _ = terminate => {},
    }

    println!("signal received, starting graceful shutdown");
}

pub async fn add_request_id(
    mut request: Request<Body>,
    next: Next<Body>,
) -> std::result::Result<impl IntoResponse, Response> {
    let uuid = Uuid::new_v4();

    request.headers_mut().insert(
        "request_id",
        HeaderValue::from_str(&uuid.to_string()).unwrap(),
    );

    Ok(next.run(request).await)
}
