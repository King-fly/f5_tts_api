# F5-TTS Zero-Shot Voice Cloning API

F5-TTS API 是一个基于 [F5-TTS](https://github.com/SWivid/F5-TTS) 模型的生产级零样本声音克隆 API 服务，提供高质量的语音合成和声音克隆功能。

## ✨ 核心功能

- **零样本声音克隆**：无需训练，仅需5-10秒参考音频即可克隆声音
- **多种参考音频来源**：支持文件上传和URL两种方式提供参考音频
- **自动语音识别**：自动转录参考音频内容（支持PyTorch 2.2+）
- **异步任务处理**：支持批量克隆任务，提高系统吞吐量
- **用户认证与授权**：支持JWT令牌和API密钥两种认证方式
- **多格式音频输出**：支持WAV等多种音频格式
- **RESTful API接口**：标准化的API设计，易于集成
- **CORS支持**：允许跨域请求，方便前端集成

## 🛠️ 技术栈

- **后端框架**：FastAPI
- **数据库**：SQLite
- **ORM**：SQLAlchemy
- **认证**：JWT + API密钥
- **音频处理**：PyTorch + torchaudio + FFmpeg
- **语音模型**：F5-TTS
- **转录模型**：Whisper（可选）

## 📦 安装与配置

### 1. 克隆仓库

```bash
git clone https://github.com/King-fly/f5_tts_api.git
cd f5_tts_api
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 文件为 `.env` 并根据需要修改：

```bash
cp .env.example .env
```

主要配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| API_HOST | API服务监听地址 | 0.0.0.0 |
| API_PORT | API服务监听端口 | 8000 |
| DEBUG | 调试模式 | True |
| DATABASE_URL | 数据库连接URL | sqlite:///./data/f5_tts.db |
| SECRET_KEY | JWT签名密钥 | 随机生成 |
| ALGORITHM | JWT算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 访问令牌过期时间 | 30 |
| MAX_AUDIO_SIZE | 最大音频文件大小（字节） | 10485760 (10MB) |
| F5_TTS_MODEL | F5-TTS模型名称 | F5TTS_v1_Base |
| TTS_DEVICE | TTS模型运行设备 | cpu |

### 4. 启动服务

```bash
# 开发模式
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 生产模式
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8000
```

服务启动后，可访问以下地址：
- API文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 📋 API 接口说明

### 认证接口

#### 注册用户
```
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "password1234"
}
```

#### 用户登录
```
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "password1234"
}
```

#### 生成API密钥
```
POST /api/v1/auth/api-key
Authorization: Bearer <token>
```

### 音频接口

#### 获取可用模型
```
GET /api/v1/models
```

#### 零样本声音克隆
```
POST /api/v1/clone
Authorization: Bearer <token> 或 X-API-Key: <api_key>
Content-Type: multipart/form-data

# 方式1：文件上传
ref_audio: <音频文件> (required)
ref_text: <参考文本> (optional)
gen_text: <要生成的文本> (required)

# 方式2：URL
ref_audio_url: <音频URL> (required)
ref_text: <参考文本> (optional)
gen_text: <要生成的文本> (required)
```

#### 上传音频样本
```
POST /api/v1/samples
Authorization: Bearer <token> 或 X-API-Key: <api_key>
Content-Type: multipart/form-data

file: <音频文件> (required)
text: <参考文本> (optional)
```

#### 获取音频样本列表
```
GET /api/v1/samples
Authorization: Bearer <token> 或 X-API-Key: <api_key>
```

### 任务接口

#### 创建克隆任务
```
POST /api/v1/tasks
Authorization: Bearer <token> 或 X-API-Key: <api_key>
Content-Type: application/json

{
  "audio_sample_id": 1,
  "text": "要生成的文本",
  "parameters": {}
}
```

#### 获取任务列表
```
GET /api/v1/tasks?skip=0&limit=10
Authorization: Bearer <token> 或 X-API-Key: <api_key>
```

#### 获取任务详情
```
GET /api/v1/tasks/{task_id}
Authorization: Bearer <token> 或 X-API-Key: <api_key>
```

## 🔒 认证方式

F5-TTS API 支持两种认证方式：

### 1. JWT令牌认证

- 适合用户登录场景
- 过期时间可配置（默认30分钟）
- 需在请求头中添加：`Authorization: Bearer <token>`

### 2. API密钥认证

- 适合服务集成场景
- 永久有效，无过期时间
- 需在请求头中添加：`X-API-Key: <api_key>`

## 🧪 测试

### 运行测试用例

```bash
cd tests
python -m pytest -v
```

### 手动测试工具

提供了多个测试脚本，可手动验证API功能：

- `test_auth_clone.py`：测试认证与克隆功能
- `test_ref_audio.py`：测试参考音频上传功能
- `test_tasks.py`：测试异步任务功能
- `test_transcribe.py`：测试转录功能
- `test_voice_clone.py`：测试声音克隆功能

## 🚀 部署

### 1. Docker部署（推荐）

```bash
docker build -t f5_tts_api .
docker run -d -p 8000:8000 -v ./data:/app/data f5_tts_api
```

### 2. 直接部署

```bash
# 安装系统依赖
sudo apt-get install ffmpeg

# 安装Python依赖
pip install -r requirements.txt

# 设置环境变量
export API_HOST=0.0.0.0
export API_PORT=8000
export DEBUG=False

# 启动服务
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8000
```

## 📝 注意事项

1. **PyTorch版本要求**：
   - 语音识别功能需要PyTorch 2.2或更高版本
   - 如果PyTorch版本低于2.2，语音识别功能将不可用，但可以手动提供参考文本

2. **音频文件要求**：
   - 支持WAV、MP3、OGG等常见音频格式
   - 推荐采样率：24kHz
   - 推荐时长：5-10秒
   - 最大文件大小：可通过`MAX_AUDIO_SIZE`配置

3. **性能优化**：
   - 对于大规模部署，建议使用GPU加速（设置`TTS_DEVICE=cuda`）
   - 异步任务处理可通过配置任务队列大小优化

4. **安全配置**：
   - 生产环境请设置`DEBUG=False`
   - 建议使用HTTPS协议
   - 定期更换`SECRET_KEY`

## 📄 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📞 联系方式

如有问题或建议，可通过以下方式联系：
- 邮箱：wangwenfei@example.com
- GitHub：[King-fly](https://github.com/King-fly)

## 📊 版本历史

### v1.0.0 (2026-02-05)
- 首次发布
- 支持零样本声音克隆
- 支持文件上传和URL两种参考音频来源
- 支持JWT和API密钥认证
- 支持异步任务处理

---

**F5-TTS API** - 让声音克隆变得简单高效！ 🎉