from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# 声音克隆请求模型
class VoiceCloneRequest(BaseModel):
    ref_audio_url: Optional[str] = None  # 参考音频URL
    ref_text: Optional[str] = None  # 参考音频对应的文本
    gen_text: str = Field(..., min_length=1, max_length=5000)  # 要生成的文本
    user_id: Optional[int] = None  # 可选的用户ID

# 声音克隆响应模型
class VoiceCloneResponse(BaseModel):
    success: bool = True
    message: str = "Voice cloning completed successfully"
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

# 克隆历史记录模型
class CloneHistoryBase(BaseModel):
    ref_audio_url: Optional[str] = None
    ref_text: Optional[str] = None
    gen_text: str = Field(..., min_length=1, max_length=5000)
    user_id: Optional[int] = None

class CloneHistoryCreate(CloneHistoryBase):
    pass

class CloneHistoryResponse(CloneHistoryBase):
    id: int
    generated_audio_url: Optional[str]
    duration: Optional[float]
    status: str = "completed"
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True