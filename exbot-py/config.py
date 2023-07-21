import tomllib
from pydantic import BaseModel

class Exchange(BaseModel):
    name: str
    key: str
    secret: str
    passphrase: str


class Config:
    def __init__(self, data) -> None:
        self.exchange = Exchange(**data['exchange'])

def load_config(config_path) -> Config:
    with open(config_path, 'rb') as f:
        config = tomllib.load(f)
        return Config(config)
