from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "The Gaffer Default"
    ENV: str = "DEV"
    PACER_THRESHOLD: float = 30.0
    TWITCH_TOKEN: str = "unset"

    class Config:
        env_file = ".env"

settings = Settings()