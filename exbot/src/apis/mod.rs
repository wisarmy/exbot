use self::spot::Spot;

pub mod spot;

pub enum API {
    Spot(Spot),
}

pub trait ToUrl {
    /// to api url
    fn to_url(&self, api: API) -> String;
}
