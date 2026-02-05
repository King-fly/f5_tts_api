from sqlalchemy.orm import Session
from typing import Optional, List
import json
from ..models import AudioSample, CloningTask
from ..schemas import CloningTaskCreate, CloningTaskStatusUpdate

class AudioSampleRepository:
    @staticmethod
    def create_audio_sample(db: Session, user_id: int, filename: str, filepath: str, duration: float, text: Optional[str] = None) -> AudioSample:
        """创建新的音频样本"""
        db_audio_sample = AudioSample(
            user_id=user_id,
            filename=filename,
            filepath=filepath,
            duration=duration,
            text=text
        )
        db.add(db_audio_sample)
        db.commit()
        db.refresh(db_audio_sample)
        return db_audio_sample

    @staticmethod
    def get_audio_samples_by_user_id(db: Session, user_id: int) -> List[AudioSample]:
        """获取用户的所有音频样本"""
        return db.query(AudioSample).filter(AudioSample.user_id == user_id).all()

    @staticmethod
    def get_audio_sample_by_id(db: Session, sample_id: int, user_id: Optional[int] = None) -> Optional[AudioSample]:
        """通过ID获取音频样本"""
        query = db.query(AudioSample).filter(AudioSample.id == sample_id)
        if user_id:
            query = query.filter(AudioSample.user_id == user_id)
        return query.first()

    @staticmethod
    def delete_audio_sample(db: Session, sample_id: int, user_id: int) -> bool:
        """删除音频样本"""
        db_audio_sample = db.query(AudioSample).filter(AudioSample.id == sample_id, AudioSample.user_id == user_id).first()
        if db_audio_sample:
            db.delete(db_audio_sample)
            db.commit()
            return True
        return False

class CloningTaskRepository:
    @staticmethod
    def create_cloning_task(db: Session, user_id: int, task_data: CloningTaskCreate) -> CloningTask:
        """创建新的克隆任务"""
        # 将参数转换为JSON字符串
        parameters_json = json.dumps(task_data.parameters) if task_data.parameters else None
        
        db_task = CloningTask(
            user_id=user_id,
            audio_sample_id=task_data.audio_sample_id,
            text=task_data.text,
            parameters=parameters_json,
            status="pending"
        )
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task

    @staticmethod
    def get_cloning_tasks_by_user_id(db: Session, user_id: int) -> List[CloningTask]:
        """获取用户的所有克隆任务"""
        return db.query(CloningTask).filter(CloningTask.user_id == user_id).order_by(CloningTask.created_at.desc()).all()

    @staticmethod
    def get_cloning_task_by_id(db: Session, task_id: int, user_id: Optional[int] = None) -> Optional[CloningTask]:
        """通过ID获取克隆任务"""
        query = db.query(CloningTask).filter(CloningTask.id == task_id)
        if user_id:
            query = query.filter(CloningTask.user_id == user_id)
        return query.first()

    @staticmethod
    def update_cloning_task_status(db: Session, task_id: int, status_update: CloningTaskStatusUpdate) -> Optional[CloningTask]:
        """更新克隆任务状态"""
        db_task = db.query(CloningTask).filter(CloningTask.id == task_id).first()
        if db_task:
            db_task.status = status_update.status
            if status_update.result_filepath:
                db_task.result_filepath = status_update.result_filepath
            db.commit()
            db.refresh(db_task)
            return db_task
        return None

    @staticmethod
    def get_pending_tasks(db: Session, limit: int = 5) -> List[CloningTask]:
        """获取待处理的任务"""
        return db.query(CloningTask).filter(CloningTask.status == "pending").limit(limit).all()