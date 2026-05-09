from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeoMarket B2C"
    VERSION: str = "0.1"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/neomarket_b2c"
    JWT_SECRET_KEY: str = "your_secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_DAYS: int = 5
    JWT_SECURE: bool = False
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
