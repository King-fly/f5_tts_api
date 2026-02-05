import asyncio
import json
from typing import Optional
from sqlalchemy.orm import Session
from ..repositories import CloningTaskRepository, AudioSampleRepository
from ..schemas import CloningTaskCreate, CloningTaskStatusUpdate
from ..services.tts_service import tts_service
import os

class TaskService:
    def __init__(self):
        self.task_queue = None
        self.is_processing = False
        self.processing_task = None
    
    async def start_processing(self, db: Session):
        """开始处理任务队列"""
        if not self.is_processing:
            # 确保队列在当前事件循环中创建
            if self.task_queue is None:
                self.task_queue = asyncio.Queue()
            self.is_processing = True
            self.processing_task = asyncio.create_task(self._process_queue(db))
    
    async def stop_processing(self):
        """停止处理任务队列"""
        if self.is_processing:
            self.is_processing = False
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass
                self.processing_task = None
    
    async def add_task(self, db: Session, user_id: int, task_data: CloningTaskCreate) -> int:
        """
        添加克隆任务到队列
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            task_data: 任务数据
            
        Returns:
            任务ID
        """
        # 创建任务记录
        db_task = CloningTaskRepository.create_cloning_task(db, user_id, task_data)
        
        # 确保队列已创建
        if self.task_queue is None:
            self.task_queue = asyncio.Queue()
            
        # 将任务添加到队列
        await self.task_queue.put(db_task.id)
        
        # 确保处理任务的协程正在运行
        if not self.is_processing:
            await self.start_processing(db)
        
        return db_task.id
    
    async def _process_queue(self, db: Session):
        """处理任务队列"""
        while self.is_processing:
            try:
                # 从队列中获取任务ID
                task_id = await self.task_queue.get()
                
                try:
                    # 处理任务
                    await self._process_task(db, task_id)
                except Exception as e:
                    print(f"Error processing task {task_id}: {e}")
                    # 更新任务状态为失败
                    CloningTaskRepository.update_cloning_task_status(
                        db, 
                        task_id, 
                        CloningTaskStatusUpdate(status="failed", result_filepath=None)
                    )
                finally:
                    # 标记任务为完成
                    self.task_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in task processing loop: {e}")
    
    async def _process_task(self, db: Session, task_id: int):
        """
        处理单个克隆任务
        
        Args:
            db: 数据库会话
            task_id: 任务ID
        """
        # 获取任务信息
        db_task = CloningTaskRepository.get_cloning_task_by_id(db, task_id)
        if not db_task:
            print(f"Task {task_id} not found")
            return
        
        # 更新任务状态为处理中
        CloningTaskRepository.update_cloning_task_status(
            db, 
            task_id, 
            CloningTaskStatusUpdate(status="processing", result_filepath=None)
        )
        
        # 获取音频样本信息
        audio_sample = AudioSampleRepository.get_audio_sample_by_id(db, db_task.audio_sample_id)
        if not audio_sample:
            print(f"Audio sample {db_task.audio_sample_id} not found for task {task_id}")
            CloningTaskRepository.update_cloning_task_status(
                db, 
                task_id, 
                CloningTaskStatusUpdate(status="failed", result_filepath=None)
            )
            return
        
        # 解析参数
        parameters = json.loads(db_task.parameters) if db_task.parameters else None
        
        # 执行声音克隆
        try:
            # 获取参考文本
            ref_text = audio_sample.text
            
            # 如果没有参考文本，尝试转录
            if not ref_text:
                try:
                    ref_text = tts_service.transcribe(audio_sample.filepath)
                except Exception as e:
                    # 转录失败，使用默认文本
                    ref_text = "Hello, this is a test message."
                    print(f"Warning: Transcription failed, using default text. Error: {e}")
            
            # 调用TTS模型生成音频
            audio_url, duration = tts_service.clone_voice(
                ref_audio_path=audio_sample.filepath,
                ref_text=ref_text,
                gen_text=db_task.text
            )
            
            # 更新任务状态为完成
            CloningTaskRepository.update_cloning_task_status(
                db, 
                task_id, 
                CloningTaskStatusUpdate(status="completed", result_filepath=audio_url)
            )
        except Exception as e:
            print(f"Error generating audio for task {task_id}: {e}")
            CloningTaskRepository.update_cloning_task_status(
                db, 
                task_id, 
                CloningTaskStatusUpdate(status="failed", result_filepath=None)
            )

# 创建全局任务服务实例
task_service = TaskService()