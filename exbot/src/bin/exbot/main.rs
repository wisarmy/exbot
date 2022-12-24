use clap::{Parser, Subcommand};
use exbot::storage;
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
        /// ceresdb endpoint
        // TODO more db support in the future
        #[arg(short, long, default_value_t = String::from("127.0.0.1:8831"))]
        endpoint: String,
    },
    Daemon {
        #[arg(short, long)]
        config: String,
    },
}
#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let cli = Cli::parse();
    match cli.commnad {
        Command::Init { endpoint } => {
            storage::init(endpoint).await;
        }
        Command::Daemon { config } => {
            println!(">> daemon {}", config);
        }
    }
}
