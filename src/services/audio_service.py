import os
import uuid
import subprocess
import tempfile
from typing import Tuple
import torchaudio

class AudioService:
    @staticmethod
    def save_uploaded_audio(uploaded_file, user_id: int) -> Tuple[str, float]:
        """
        保存上传的音频文件并返回文件路径和时长
        
        Args:
            uploaded_file: 上传的文件对象
            user_id: 用户ID
            
        Returns:
            (文件路径, 时长) 元组
        """
        # 确保音频样本目录存在
        user_audio_dir = os.path.join(os.path.dirname(__file__), "..", "..", "audio_samples", str(user_id))
        os.makedirs(user_audio_dir, exist_ok=True)
        
        # 生成唯一文件名
        file_extension = os.path.splitext(uploaded_file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(user_audio_dir, unique_filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            content = uploaded_file.file.read()
            buffer.write(content)
        
        # 计算音频时长
        duration = AudioService.get_audio_duration(file_path)
        
        return file_path, duration
    
    @staticmethod
    def get_audio_duration(file_path: str) -> float:
        """
        获取音频文件的时长（秒）
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            音频时长（秒）
        """
        try:
            # 使用torchaudio获取音频时长
            waveform, sample_rate = torchaudio.load(file_path)
            duration = waveform.shape[1] / sample_rate
            return duration
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            # 如果torchaudio失败，尝试使用ffmpeg
            try:
                cmd = [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    file_path
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                duration = float(result.stdout.strip())
                return duration
            except Exception as e:
                print(f"Error getting audio duration with ffmpeg: {e}")
                # 如果所有方法都失败，返回默认时长
                return 0.0
    
    @staticmethod
    def convert_audio_format(input_path: str, output_format: str = "wav") -> str:
        """
        转换音频文件格式
        
        Args:
            input_path: 输入音频文件路径
            output_format: 输出音频格式
            
        Returns:
            转换后的音频文件路径
        """
        try:
            # 生成输出文件路径
            base_name = os.path.splitext(input_path)[0]
            output_path = f"{base_name}.{output_format}"
            
            # 使用torchaudio进行格式转换
            waveform, sample_rate = torchaudio.load(input_path)
            torchaudio.save(output_path, waveform, sample_rate)
            
            return output_path
        except Exception as e:
            print(f"Error converting audio format: {e}")
            # 如果torchaudio失败，尝试使用ffmpeg
            try:
                # 生成临时输出文件路径
                with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as temp_file:
                    output_path = temp_file.name
                
                cmd = [
                    "ffmpeg",
                    "-i", input_path,
                    "-y",  # 覆盖现有文件
                    output_path
                ]
                subprocess.run(cmd, check=True)
                
                return output_path
            except Exception as e:
                print(f"Error converting audio format with ffmpeg: {e}")
                # 如果所有方法都失败，返回原始文件
                return input_path
    
    @staticmethod
    def validate_audio_file(file_path: str) -> Tuple[bool, str]:
        """
        验证音频文件是否有效
        
        Args:
            file_path: 音频文件路径
            
        Returns:
            (是否有效, 错误信息) 元组
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "File is empty"
            
            # 检查是否为音频文件
            try:
                waveform, sample_rate = torchaudio.load(file_path)
                if waveform.numel() == 0:
                    return False, "Audio file contains no data"
                
                # 检查音频时长
                duration = waveform.shape[1] / sample_rate
                if duration < 0.1:
                    return False, "Audio duration is too short (minimum 0.1 seconds)"
                if duration > 60:
                    return False, "Audio duration is too long (maximum 60 seconds)"
                
                return True, ""
            except Exception as e:
                return False, f"Invalid audio file: {str(e)}"
        except Exception as e:
            return False, f"Error validating audio file: {str(e)}"