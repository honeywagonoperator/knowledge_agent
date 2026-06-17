import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = os.getenv("DB_HOST", "localhost"); port: int = int(os.getenv("DB_PORT", "5432"))
    database: str = os.getenv("DB_NAME", "knowledge_engine"); user: str = os.getenv("DB_USER", "knowledge_engine")
    password: str = os.getenv("DB_PASSWORD", "knowledge_engine")
    @property
    def dsn(self) -> str: return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
