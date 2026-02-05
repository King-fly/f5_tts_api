import os
from typing import List, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings(BaseModel):
    # API服务配置
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    ALLOW_ORIGINS: List[str] = os.getenv("ALLOW_ORIGINS", "*").split(",")
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/f5_tts.db")
    
    # 认证配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # F5-TTS模型配置
    F5_TTS_MODEL: str = os.getenv("F5_TTS_MODEL", "F5TTS_v1_Base")
    ODE_METHOD: str = os.getenv("ODE_METHOD", "euler")
    USE_EMA: bool = os.getenv("USE_EMA", "True").lower() in ("true", "1", "t")
    TTS_DEVICE: str = os.getenv("TTS_DEVICE", "cpu")  # cpu, cuda, mps
    
    # 音频配置
    AUDIO_OUTPUT_DIR: str = os.getenv("AUDIO_OUTPUT_DIR", "data/audio_outputs")
    MAX_AUDIO_SIZE: int = int(os.getenv("MAX_AUDIO_SIZE", "10485760"))  # 10MB
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", "logs/app.log")
    
    # 任务队列配置
    TASK_QUEUE_SIZE: int = int(os.getenv("TASK_QUEUE_SIZE", "100"))
    TASK_WORKERS: int = int(os.getenv("TASK_WORKERS", "1"))

# 创建配置实例
settings = Settings()