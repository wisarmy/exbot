use pyo3::prelude::*;

#[pyfunction]
pub fn ping() -> PyResult<String> {
    Ok("pong".to_string())
}
