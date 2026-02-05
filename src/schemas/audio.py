from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# 音频样本基础模式
class AudioSampleBase(BaseModel):
    filename: str

# 音频样本响应模式
class AudioSampleResponse(AudioSampleBase):
    id: int
    user_id: int
    filepath: str
    duration: float
    created_at: datetime

    class Config:
        from_attributes = True

# 克隆任务基础模式
class CloningTaskBase(BaseModel):
    audio_sample_id: int
    text: str = Field(..., min_length=1, max_length=5000)
    parameters: Optional[Dict[str, Any]] = None

# 克隆任务创建模式
class CloningTaskCreate(CloningTaskBase):
    pass

# 克隆任务响应模式
class CloningTaskResponse(CloningTaskBase):
    id: int
    user_id: int
    status: str
    result_filepath: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 克隆任务状态更新模式
class CloningTaskStatusUpdate(BaseModel):
    status: str
    result_filepath: Optional[str] = None