from pydantic import EmailStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
        DATABASE_URL: str
        MONGO_INITDB_DATABASE: str
        CLIENT_ORIGIN: str
        GITHUB_AUTHORIZE: str
        GITHUB_ACCESS_TOKEN_URL: str
        GITHUB_API_URL: str
        GITHUB_CLIENT_ID: str
        GITHUB_CLIENT_SECRET: str
        GITHUB_CALLBACK_URL: str
        OPENAI_API_KEY: str
        OPENAI_MODEL: str = "gpt-4o"  # Default model, can be overridden
        JWT_SECRET_KEY: str
        JWT_ALGORITHM: str = "HS256"
        JWT_EXPIRY_DAYS: int = 30
        class Config:
                env_file = './.env'

 
settings = Settings()