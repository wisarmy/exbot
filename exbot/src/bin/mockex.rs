use std::{env, net::SocketAddr};

use axum::{response::Html, routing::get, Router};
use clap::{Parser, Subcommand};
use exbot::{
    config::{self, Config},
    error::Result,
    storage::{self, DbType},
};
use sqlx::SqlitePool;
use tracing::{debug, info};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

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
            config::with_config("mockex.toml", |c| async move {
                debug!("With config: {:?}", c);
                let _pool = SqlitePool::connect(c.storage.unwrap().db_endpoint.as_str())
                    .await
                    .unwrap();
                let app = Router::new().route("/", get(handler));

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
