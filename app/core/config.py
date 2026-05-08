from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeoMarket B2C"
    VERSION: str = "0.1"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/neomarket_b2c"
    JWT_SECRET: str = "secret"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
