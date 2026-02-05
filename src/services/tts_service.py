import os
import sys
import torch
import tempfile
import random
import string
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import requests

# 添加F5-TTS到Python路径
if "/Users/wangwenfei/Dev/github/F5-TTS" not in sys.path:
    sys.path.append("/Users/wangwenfei/Dev/github/F5-TTS")

# 尝试导入F5-TTS模块
try:
    from f5_tts.api import F5TTS
    F5_TTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Failed to import F5-TTS: {e}")
    F5_TTS_AVAILABLE = False

from ..config import settings

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.model = None
        self.loaded = False
        self.audio_output_dir = settings.AUDIO_OUTPUT_DIR
        self._ensure_output_dir()
        
    def _ensure_output_dir(self):
        """确保音频输出目录存在"""
        os.makedirs(self.audio_output_dir, exist_ok=True)
        
    async def load_model(self):
        """加载F5-TTS模型"""
        if not F5_TTS_AVAILABLE:
            raise Exception("F5-TTS module not available")
            
        try:
            logger.info("Loading F5-TTS model...")
            self.model = F5TTS(
                model=settings.F5_TTS_MODEL,
                ode_method=settings.ODE_METHOD,
                use_ema=settings.USE_EMA,
                device=settings.TTS_DEVICE
            )
            self.loaded = True
            logger.info("F5-TTS model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load F5-TTS model: {str(e)}")
            raise
            
    def _generate_unique_filename(self, prefix: str = "generated", extension: str = "wav") -> str:
        """生成唯一的文件名"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"{prefix}_{timestamp}_{random_str}.{extension}"
    
    def transcribe(self, ref_audio_path: str, language: Optional[str] = None) -> str:
        """
        转录参考音频
        
        注意：此功能依赖于whisper模型，需要PyTorch 2.2或更高版本
        """
        if not self.loaded:
            raise Exception("TTS model not loaded")
            
        try:
            return self.model.transcribe(ref_audio_path, language)
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            # 提供更友好的错误信息
            if "PyTorch" in str(e) or "pytorch" in str(e):
                raise Exception("Transcription requires PyTorch 2.2 or higher. Please provide ref_text explicitly.")
            raise
    
    def clone_voice(self, ref_audio_path: str, ref_text: str, gen_text: str) -> Tuple[str, float]:
        """
        执行声音克隆
        
        Args:
            ref_audio_path: 参考音频路径
            ref_text: 参考音频对应的文本
            gen_text: 要生成的文本
            
        Returns:
            Tuple[str, float]: 生成的音频文件URL和时长
        """
        if not self.loaded:
            raise Exception("TTS model not loaded")
            
        try:
            logger.info("Starting voice cloning...")
            
            # 生成唯一的输出文件名
            output_filename = self._generate_unique_filename()
            output_path = os.path.join(self.audio_output_dir, output_filename)
            
            # 执行推理
            wav, sr, _ = self.model.infer(
                ref_file=ref_audio_path,
                ref_text=ref_text,
                gen_text=gen_text,
                file_wave=output_path,
                remove_silence=True
            )
            
            # 计算音频时长（秒）
            duration = len(wav) / sr
            
            # 生成可访问的URL
            audio_url = f"/audio/{output_filename}"
            
            logger.info(f"Voice cloning completed. Output: {audio_url}, Duration: {duration}s")
            return audio_url, duration
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {str(e)}")
            raise
    
    def clone_voice_from_url(self, ref_audio_url: str, ref_text: str, gen_text: str) -> Tuple[str, float]:
        """
        从URL加载参考音频并执行声音克隆
        
        Args:
            ref_audio_url: 参考音频URL
            ref_text: 参考音频对应的文本
            gen_text: 要生成的文本
            
        Returns:
            Tuple[str, float]: 生成的音频文件URL和时长
        """
        try:
            # 下载参考音频到临时文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                response = requests.get(ref_audio_url)
                response.raise_for_status()
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            # 执行声音克隆
            audio_url, duration = self.clone_voice(temp_file_path, ref_text, gen_text)
            
            # 删除临时文件
            os.unlink(temp_file_path)
            
            return audio_url, duration
            
        except Exception as e:
            logger.error(f"Voice cloning from URL failed: {str(e)}")
            raise
    
    def get_available_models(self) -> Dict[str, Any]:
        """获取可用的TTS模型信息"""
        return {
            "available_models": [
                {
                    "name": "F5TTS_v1_Base",
                    "description": "F5-TTS v1 Base model",
                    "default": True
                },
                {
                    "name": "F5TTS_Base",
                    "description": "F5-TTS Base model"
                },
                {
                    "name": "E2TTS_Base",
                    "description": "E2-TTS Base model"
                }
            ],
            "current_model": settings.F5_TTS_MODEL,
            "device": settings.TTS_DEVICE
        }

# 创建TTSService的单例实例
tts_service = TTSService()