use clap::{Parser, Subcommand};
use exbot::{
    config::{self, Config},
    error::Result,
    storage::{self, DbType},
};
use tracing::{debug, info};
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

/// Exbot program
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
        #[arg(long, default_value_t = String::from(config::root_path().join("exbot.db").to_str().unwrap()))]
        db_endpoint: String,
    },
    Daemon,
}
#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
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
                mockex: None,
            }
            .init("exbot.toml")?;
        }
        Command::Daemon => {
            info!("Initializing daemon");
            config::with_config("exbot.toml", |c| async move {
                debug!("With config: {:?}", c);
            })
            .await;
        }
    }
    Ok(())
}
