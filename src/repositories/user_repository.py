from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
from ..models import User, ApiKey
from ..schemas import UserCreate, ApiKeyCreate

class UserRepository:
    @staticmethod
    def create_user(db: Session, user: UserCreate, hashed_password: str) -> User:
        """创建新用户"""
        db_user = User(
            username=user.username,
            email=user.email,
            password_hash=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """通过ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()

class ApiKeyRepository:
    @staticmethod
    def create_api_key(db: Session, user_id: int, api_key_data: ApiKeyCreate) -> ApiKey:
        """创建新的API密钥"""
        # 生成随机API密钥
        key = secrets.token_urlsafe(32)
        
        db_api_key = ApiKey(
            user_id=user_id,
            key=key,
            expires_at=api_key_data.expires_at
        )
        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)
        return db_api_key

    @staticmethod
    def get_api_keys_by_user_id(db: Session, user_id: int) -> List[ApiKey]:
        """获取用户的所有API密钥"""
        return db.query(ApiKey).filter(ApiKey.user_id == user_id).all()

    @staticmethod
    def get_api_key_by_key(db: Session, key: str) -> Optional[ApiKey]:
        """通过密钥字符串获取API密钥"""
        return db.query(ApiKey).filter(ApiKey.key == key).first()

    @staticmethod
    def get_api_key_by_id(db: Session, key_id: int) -> Optional[ApiKey]:
        """通过ID获取API密钥"""
        return db.query(ApiKey).filter(ApiKey.id == key_id).first()

    @staticmethod
    def delete_api_key(db: Session, key_id: int, user_id: int) -> bool:
        """删除API密钥"""
        db_api_key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.user_id == user_id).first()
        if db_api_key:
            db.delete(db_api_key)
            db.commit()
            return True
        return False

    @staticmethod
    def is_api_key_valid(db: Session, key: str) -> Optional[User]:
        """验证API密钥是否有效"""
        db_api_key = db.query(ApiKey).filter(ApiKey.key == key).first()
        if not db_api_key or not db_api_key.is_active:
            return None
        
        # 检查是否过期
        if db_api_key.expires_at and datetime.utcnow() > db_api_key.expires_at:
            return None
        
        # 获取关联的用户
        return db.query(User).filter(User.id == db_api_key.user_id).first()