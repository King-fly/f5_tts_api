from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# 用户基础模式
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

# 用户创建模式
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# 用户登录模式
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 用户响应模式
class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# API密钥基础模式
class ApiKeyBase(BaseModel):
    expires_at: Optional[datetime] = None

# API密钥创建模式
class ApiKeyCreate(ApiKeyBase):
    pass

# API密钥响应模式
class ApiKeyResponse(ApiKeyBase):
    id: int
    user_id: int
    key: str
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# 令牌响应模式
class Token(BaseModel):
    access_token: str
    token_type: str

# 令牌数据模式
class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None