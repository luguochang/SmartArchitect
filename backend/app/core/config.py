from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Logging Configuration
    LOG_LEVEL: str = "INFO"              # 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LOG_DIR: str = "logs"                # 日志目录（相对于 backend/）
    ENVIRONMENT: str = "development"     # 环境模式 (development, production)

    # AI Model API Keys (Optional)
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    SILICONFLOW_API_KEY: str = "sk-labtoeibcevkdzanpprwezzivdokslxnspigjnapxyogvpgp"
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
