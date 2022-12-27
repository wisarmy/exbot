use std::{fs, path::PathBuf, sync::RwLock};

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

#[derive(Serialize, Deserialize, Debug)]
pub struct Config {
    pub storage: storage::Config,
}

pub fn config() -> &'static RwLock<Option<Config>> {
    CONFIG.get_or_init(load_config)
}

pub fn load_config() -> RwLock<Option<Config>> {
    todo!()
}

impl Config {
    pub fn init(&self) -> Result<()> {
        if self.config_path().exists() {
            return Err(exbot_error!("exbot config file exbot.toml already exists!"))
                .inspect_err(|e| error!("{}", e));
        }
        fs::create_dir_all(EXBOT_PATH.as_path())
            .inspect_err(|e| error!("Create dir {:?}: {}", EXBOT_PATH, e))?;
        self.save_to_file()?;
        info!("initializing exbot at {}", EXBOT_PATH.display());
        Ok(())
    }
    /// config path
    fn config_path(&self) -> PathBuf {
        EXBOT_PATH.join("exbot.toml")
    }
    /// save file
    pub fn save_to_file(&self) -> Result<()> {
        let config_string = toml::to_string(&self).inspect_err(|e| error!("{}", e))?;

        fs::write(self.config_path(), config_string)
            .inspect_err(|e| error!("Write config file {:?}: {}", self.config_path(), e))?;
        Ok(())
    }
}
