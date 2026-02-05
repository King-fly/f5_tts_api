from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from ..database import get_db
from ..schemas import UserCreate, UserResponse, UserLogin, Token, ApiKeyCreate, ApiKeyResponse
from ..repositories import UserRepository, ApiKeyRepository
from ..services import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# 创建HTTPBearer认证方案
bearer_scheme = HTTPBearer()

# 获取当前用户
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = AuthService.verify_token(token, credentials_exception)
    user = UserRepository.get_user_by_id(db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查邮箱是否已存在
    db_user = UserRepository.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 检查用户名是否已存在
    db_user = UserRepository.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # 创建新用户
    hashed_password = AuthService.get_password_hash(user.password)
    db_user = UserRepository.create_user(db, user, hashed_password)
    
    return db_user

@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    user = AuthService.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=30)
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user

@router.post("/keys", response_model=ApiKeyResponse)
def create_api_key(api_key_data: ApiKeyCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """创建新的API密钥"""
    return ApiKeyRepository.create_api_key(db, current_user.id, api_key_data)

@router.get("/keys", response_model=List[ApiKeyResponse])
def get_api_keys(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """获取用户的所有API密钥"""
    return ApiKeyRepository.get_api_keys_by_user_id(db, current_user.id)

@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_key(key_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """删除API密钥"""
    success = ApiKeyRepository.delete_api_key(db, key_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    return None