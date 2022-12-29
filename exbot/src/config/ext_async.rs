use std::future::Future;

use super::{load, Config};
pub async fn with_config<T, F, Fut>(f: F) -> T
where
    F: FnOnce(Config) -> Fut,
    Fut: Future<Output = T>,
{
    f(load().read().unwrap().as_ref().unwrap().clone()).await
}
