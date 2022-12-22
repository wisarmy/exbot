use clap::{Parser, Subcommand};

/// Exbot program
#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    commnad: Command,
}

#[derive(Subcommand, Debug)]
enum Command {
    Daemon {
        #[arg(short, long)]
        config: String,
    },
}

fn main() {
    let commands = Cli::parse();

    match commands.commnad {
        Command::Daemon { config } => {
            println!(">> daemon {}", config);
        }
    }
}
