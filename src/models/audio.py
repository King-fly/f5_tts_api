from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class AudioSample(Base):
    __tablename__ = "audio_samples"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    duration = Column(Float, nullable=False)
    text = Column(Text, nullable=True)  # 参考音频对应的文本
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    user = relationship("User", back_populates="audio_samples")
    cloning_tasks = relationship("CloningTask", back_populates="audio_sample", cascade="all, delete-orphan")

class CloningTask(Base):
    __tablename__ = "cloning_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    audio_sample_id = Column(Integer, ForeignKey("audio_samples.id", ondelete="CASCADE"), nullable=False)
    text = Column(Text, nullable=False)
    parameters = Column(Text, nullable=True)  # JSON 格式存储参数
    status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    result_filepath = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="cloning_tasks")
    audio_sample = relationship("AudioSample", back_populates="cloning_tasks")