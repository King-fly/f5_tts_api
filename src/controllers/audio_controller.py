from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import tempfile
import logging


from ..database import get_db
from ..schemas import (
    AudioSampleResponse, 
    CloningTaskCreate, 
    CloningTaskResponse,
    VoiceCloneRequest, 
    VoiceCloneResponse
)
from ..repositories import AudioSampleRepository, CloningTaskRepository, ApiKeyRepository
from ..services import AudioService, task_service, tts_service
from .auth_controller import get_current_user
from ..models import User
from ..config import settings

# 设置日志记录器
logger = logging.getLogger(__name__)
router = APIRouter(tags=["Audio"])

# API密钥认证依赖
async def get_current_user_from_api_key(
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    if not api_key:
        return None
    
    user = ApiKeyRepository.is_api_key_valid(db, api_key)
    if user is None:
        return None
    return user

# 获取当前用户（从JWT或API密钥）
async def get_current_user_auth(
    jwt_user: Optional[User] = Depends(get_current_user),
    api_user: Optional[User] = Depends(get_current_user_from_api_key)
):
    if jwt_user:
        return jwt_user
    if api_user:
        return api_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

# 无需认证的公共端点
@router.get("/models", tags=["Models"])
def get_available_models():
    """获取可用的TTS模型信息"""
    return tts_service.get_available_models()

# 需要认证的声音克隆端点
@router.post("/clone", response_model=VoiceCloneResponse, openapi_extra={
    "requestBody": {
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "ref_audio": {
                            "type": "string",
                            "format": "binary",
                            "description": "参考音频文件（与ref_audio_url二选一）"
                        },
                        "ref_audio_url": {
                            "type": "string",
                            "description": "参考音频URL（与ref_audio二选一）"
                        },
                        "ref_text": {
                            "type": "string",
                            "description": "参考音频对应的文本（如果不提供，系统会自动转录）"
                        },
                        "gen_text": {
                            "type": "string",
                            "description": "要生成的文本",
                            "required": True
                        }
                    },
                    "required": ["gen_text"]
                }
            }
        }
    }
})
async def clone_voice(
    *,  # 使用*确保所有参数都是关键字参数
    ref_audio: UploadFile = File(..., media_type="audio/wav", description="参考音频文件"),  # 使其成为必需参数
    ref_audio_url: Optional[str] = Form(None, description="参考音频URL"),
    ref_text: Optional[str] = Form(None, description="参考音频对应的文本"),
    gen_text: str = Form(..., description="要生成的文本"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_auth)
):
    """
    零样本声音克隆API
    
    支持两种方式提供参考音频：
    1. 通过文件上传 (ref_audio)
    2. 通过URL (ref_audio_url)
    
    如果提供了参考音频但没有提供ref_text，系统会自动转录音频内容。
    """
    # 验证输入
    # 注意：由于FastAPI的限制，我们将ref_audio设为必需参数以确保正确的表单处理
    # 但实际上用户可以选择提供ref_audio或ref_audio_url
    # 如果提供了ref_audio_url，我们将忽略ref_audio
    if ref_audio_url:
        # 如果提供了URL，使用URL而不是上传的文件
        ref_audio = None
    
    if not gen_text:
        raise HTTPException(status_code=400, detail="gen_text must be provided")
    
    ref_audio_path = None
    user_id = current_user.id if current_user else None
    
    try:
        # 处理参考音频
        if ref_audio:
            # 检查文件大小
            if ref_audio.size > settings.MAX_AUDIO_SIZE:
                raise HTTPException(status_code=400, detail=f"Audio file too large. Maximum size: {settings.MAX_AUDIO_SIZE / 1024 / 1024}MB")
                
            # 保存上传的文件到临时位置
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(await ref_audio.read())
                ref_audio_path = temp_file.name
        else:
            # 从URL获取参考音频
            ref_audio_path = ref_audio_url
        
        # 如果没有提供ref_text，自动转录
        if not ref_text:
            try:
                ref_text = tts_service.transcribe(ref_audio_path)
            except Exception as e:
                raise HTTPException(status_code=400, detail="Failed to transcribe ref_audio. Please provide ref_text explicitly.")
        
        # 执行声音克隆
        if ref_audio:
            # 从上传文件克隆
            audio_url, duration = tts_service.clone_voice(ref_audio_path, ref_text, gen_text)
        else:
            # 从URL克隆
            audio_url, duration = tts_service.clone_voice_from_url(ref_audio_path, ref_text, gen_text)
        
        # 保存历史记录到数据库（如果用户已认证）
        # 注意：当前实现暂时跳过数据库保存，因为需要创建音频样本记录
        # 后续可以完善这部分功能，先确保声音克隆核心功能可用
        
        # 返回结果
        return VoiceCloneResponse(
            success=True,
            message="Voice cloning completed successfully",
            audio_url=audio_url,
            duration=duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 保存失败记录到数据库（如果用户已认证）
        # 注意：当前实现暂时跳过数据库保存，因为需要创建音频样本记录
        # 后续可以完善这部分功能
        
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")
    finally:
        # 清理临时文件
        if ref_audio and ref_audio_path and os.path.exists(ref_audio_path):
            os.unlink(ref_audio_path)

@router.post("/samples", response_model=AudioSampleResponse)
async def upload_audio_sample(
    file: UploadFile = File(...),
    text: Optional[str] = Form(None, alias="text", description="参考音频对应的文本"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_auth)
):
    """上传音频样本"""
    # 验证文件类型
    if not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio file"
        )
    
    # 保存文件
    try:
        file_path, duration = AudioService.save_uploaded_audio(file, current_user.id)
        
        # 验证音频文件
        is_valid, error_msg = AudioService.validate_audio_file(file_path)
        if not is_valid:
            # 删除无效文件
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio file: {error_msg}"
            )
        
        # 创建音频样本记录
        db_audio_sample = AudioSampleRepository.create_audio_sample(
            db, 
            current_user.id, 
            file.filename, 
            file_path, 
            duration,
            text
        )
        
        return db_audio_sample
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload audio file: {str(e)}"
        )

@router.get("/samples", response_model=List[AudioSampleResponse])
def get_audio_samples(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_auth)
):
    """获取用户的所有音频样本"""
    return AudioSampleRepository.get_audio_samples_by_user_id(db, current_user.id)

@router.post("/tasks", response_model=CloningTaskResponse)
async def create_cloning_task(
    task_data: CloningTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_auth)
):
    """
    创建异步声音克隆任务
    
    Args:
        task_data: 克隆任务的创建数据，包含音频样本ID、文本和可选参数
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        新创建的克隆任务信息
    """
    # 验证音频样本是否存在
    db_audio_sample = AudioSampleRepository.get_audio_sample_by_id(db, task_data.audio_sample_id, current_user.id)
    if not db_audio_sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio sample not found or not accessible"
        )
    
    # 创建任务记录
    db_task = CloningTaskRepository.create_cloning_task(
        db, 
        current_user.id, 
        task_data
    )
    
    # 提交到任务队列
    await task_service.add_task(db, current_user.id, task_data)
    
    return db_task

@router.get("/tasks", response_model=List[CloningTaskResponse])
def get_cloning_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_auth),
    skip: int = 0,
    limit: int = 10
):
    """
    获取用户的所有克隆任务
    
    Args:
        db: 数据库会话
        current_user: 当前认证用户
        skip: 跳过的任务数量
        limit: 返回的任务数量上限
        
    Returns:
        克隆任务列表
    """
    try:
        tasks = CloningTaskRepository.get_cloning_tasks_by_user_id(db, current_user.id)
        # 实现简单的分页
        paginated_tasks = tasks[skip:skip + limit]
        return paginated_tasks
    except Exception as e:
        logger.error(f"Failed to get cloning tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cloning tasks: {str(e)}"
        )

@router.get("/tasks/{task_id}", response_model=CloningTaskResponse)
def get_cloning_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_auth)
):
    """
    获取特定克隆任务的详细信息
    
    Args:
        task_id: 克隆任务ID
        db: 数据库会话
        current_user: 当前认证用户
        
    Returns:
        克隆任务详细信息
    """
    try:
        db_task = CloningTaskRepository.get_cloning_task_by_id(db, task_id, current_user.id)
        if not db_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cloning task not found or not accessible"
            )
        return db_task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cloning task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cloning task: {str(e)}"
        )