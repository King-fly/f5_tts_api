from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from ..repositories import UserRepository
from ..schemas import UserCreate, TokenData

# 加载环境变量
load_dotenv()

# 获取密钥和算法
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 不再使用passlib的CryptContext，直接使用bcrypt库

class AuthService:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def get_password_hash(password: str) -> str:
        """获取密码哈希值"""
        # bcrypt限制密码长度为72字节，超过部分会被忽略
        password = password[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, credentials_exception) -> TokenData:
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: int = payload.get("sub")
            email: str = payload.get("email")
            if user_id is None or email is None:
                raise credentials_exception
            token_data = TokenData(user_id=int(user_id), email=email)
            return token_data
        except JWTError:
            raise credentials_exception

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        """认证用户"""
        user = UserRepository.get_user_by_email(db, email)
        if not user:
            return False
        if not AuthService.verify_password(password, user.password_hash):
            return False
        return user