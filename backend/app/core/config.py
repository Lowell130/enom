from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "EnotecaMolise API"
    API_V1_STR: str = "/api/v1"
    
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "enoteca_molise"
    
    SECRET_KEY: str = "enotecamolise_secret_jwt_key_2026_super_secure_key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 4320
    
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
    
    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
