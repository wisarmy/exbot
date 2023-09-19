use std::{fs, future::Future, path::PathBuf, str::FromStr, sync::RwLock};

use home::home_dir;
use once_cell::sync::{Lazy, OnceCell};
use serde::{Deserialize, Serialize};
use tracing::{error, info};

use crate::{error::Result, exbot_error, storage};

const EXBOT_PATH: Lazy<PathBuf> = Lazy::new(|| {
    let mut exbot_path = home_dir().unwrap().join(".exbot");
    if let Some(env_exbot_path) = std::env::var_os("EXBOT_PATH") {
        exbot_path = PathBuf::from(env_exbot_path);
    };
    exbot_path
});
pub(crate) static CONFIG: OnceCell<RwLock<Option<Config>>> = OnceCell::new();

#[derive(Serialize, Deserialize, Debug, Default, Clone)]
pub struct Config {
    pub storage: storage::Config,
}

impl FromStr for Config {
    type Err = toml::de::Error;
    #[inline]
    fn from_str(s: &str) -> std::result::Result<Self, Self::Err> {
        toml::from_str(s)
    }
}

fn load(filename: &str) -> &'static RwLock<Option<Config>> {
    CONFIG.get_or_init(|| {
        let config_path = Config::default().config_path(filename);
        info!("Loading config {}", config_path.display());
        RwLock::new(
            fs::read_to_string(&config_path)
                .inspect_err(|e| error!("Read file {}: {}", &config_path.display(), e))
                .ok()
                .and_then(|v| {
                    v.parse()
                        .inspect_err(|e| error!("Parse file {}: {}", &config_path.display(), e))
                        .ok()
                }),
        )
    })
}

#[cfg(not(feature = "async_config"))]
pub fn with_config<T, F>(filename: &str, f: impl FnOnce(&Config) -> T) -> T {
    f(load(filename).read().unwrap().as_ref().unwrap())
}
#[cfg(feature = "async_config")]
pub async fn with_config<T, F, Fut>(filename: &str, f: F) -> T
where
    F: FnOnce(Config) -> Fut,
    Fut: Future<Output = T>,
{
    f(load(filename).read().unwrap().as_ref().unwrap().clone()).await
}

impl Config {
    pub fn init(&self, filename: &str) -> Result<()> {
        if self.config_path(filename).exists() {
            return Err(exbot_error!(
                "exbot config file {} already exists!",
                filename
            ))
            .inspect_err(|e| error!("{}", e));
        }
        fs::create_dir_all(EXBOT_PATH.as_path())
            .inspect_err(|e| error!("Create dir {:?}: {}", EXBOT_PATH, e))?;
        self.save_to_file(filename)?;
        info!("initializing exbot at {}", EXBOT_PATH.display());
        Ok(())
    }
    /// config path
    fn config_path(&self, filename: &str) -> PathBuf {
        EXBOT_PATH.join(filename)
    }
    /// save file
    pub fn save_to_file(&self, filename: &str) -> Result<()> {
        let config_string =
            toml::to_string(&self).inspect_err(|e| error!("Toml serialize: {}", e))?;

        fs::write(self.config_path(filename), config_string)
            .inspect_err(|e| error!("Write config file {:?}: {}", self.config_path(filename), e))?;
        Ok(())
    }
}
