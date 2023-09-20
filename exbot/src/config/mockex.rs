use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct MockexConfig {
    pub addr: String,
}

impl Default for MockexConfig {
    fn default() -> Self {
        Self {
            addr: "0.0.0.0:2023".to_owned(),
        }
    }
}
