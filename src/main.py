from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncio
import os

from .database import get_db, engine, Base
from .controllers import auth_router, audio_router
from .services import task_service, tts_service
from .config import settings
from .logging_config import setup_logging

# 设置日志
logger = setup_logging()

# 创建数据库表
Base.metadata.create_all(bind=engine)
logger.info("Database tables created successfully")

# 创建FastAPI应用
app = FastAPI(
    title="F5-TTS Zero-Shot Voice Cloning API",
    description="Production-grade zero-shot voice cloning API based on F5-TTS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.DEBUG
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录，用于提供生成的音频文件
if not os.path.exists(settings.AUDIO_OUTPUT_DIR):
    os.makedirs(settings.AUDIO_OUTPUT_DIR)
app.mount("/audio", StaticFiles(directory=settings.AUDIO_OUTPUT_DIR), name="audio")

# 注册路由
app.include_router(auth_router, prefix="/api/v1", tags=["Authentication"])
app.include_router(audio_router, prefix="/api/v1", tags=["Audio"])

# 启动事件
@app.on_event("startup")
async def startup_event():
    # 加载TTS模型
    try:
        await tts_service.load_model()
        logger.info("TTS model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load TTS model: {str(e)}")
        # 继续启动服务，让API可用但TTS功能不可用
    
    # 启动任务处理队列
    db = next(get_db())
    await task_service.start_processing(db)
    logger.info("Task processing service started")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    # 停止任务处理队列
    await task_service.stop_processing()
    logger.info("Task processing service stopped")

# 健康检查端点
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# 根路径
@app.get("/")
def read_root():
    return {
        "message": "Welcome to F5-TTS Zero-Shot Voice Cloning API",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    logger.info(f"Starting F5-TTS API service on {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    uvicorn.run(
        "src.main:app", 
        host=settings.API_HOST, 
        port=settings.API_PORT, 
        reload=settings.DEBUG
    )