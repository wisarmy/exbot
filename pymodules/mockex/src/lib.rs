pub mod mockex;

use pyo3::prelude::*;
use pyo3::pymodule;

#[pymodule]
fn exbot_mockex(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(mockex::ping, m)?)?;
    Ok(())
}
