import requests
import os
import sys
from datetime import datetime

# API地址
API_URL = "http://localhost:8000"

# 参考音频文件路径
REF_AUDIO_PATH = "/Users/wangwenfei/Dev/github/F5-TTS/src/f5_tts/infer/examples/basic/basic_ref_en.wav"

# 验证参考音频文件是否存在
if not os.path.exists(REF_AUDIO_PATH):
    print(f"错误：参考音频文件不存在 {REF_AUDIO_PATH}")
    sys.exit(1)

print("开始测试F5-TTS API transcribe功能...")
print(f"API地址：{API_URL}")

# 获取认证令牌
def get_auth_token():
    # 先注册一个临时用户
    register_endpoint = f"{API_URL}/api/v1/auth/register"
    test_email = f"test_transcribe_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    test_username = f"testuser_trans_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    register_data = {
        "username": test_username,
        "email": test_email,
        "password": "password1234"
    }
    
    try:
        # 注册用户
        register_response = requests.post(register_endpoint, json=register_data)
        if register_response.status_code != 200:
            print(f"❌ 用户注册失败：{register_response.text}")
            return None
        
        # 登录获取令牌
        login_endpoint = f"{API_URL}/api/v1/auth/login"
        login_data = {
            "email": test_email,
            "password": "password1234"
        }
        
        login_response = requests.post(login_endpoint, json=login_data)
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            print(f"✅ 获取认证令牌成功！")
            return token
        else:
            print(f"❌ 用户登录失败：{login_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 获取令牌失败：{str(e)}")
        return None

# 测试transcribe功能
def test_transcribe():
    print("\n=== 测试：transcribe功能 ===")
    
    # 获取认证令牌
    token = get_auth_token()
    if not token:
        return False
    
    endpoint = f"{API_URL}/api/v1/clone"
    
    # 准备测试数据
    gen_text = "This is a test of transcribe functionality."
    
    try:
        with open(REF_AUDIO_PATH, "rb") as f:
            files = {
                "ref_audio": (os.path.basename(REF_AUDIO_PATH), f, "audio/wav")
            }
            data = {
                "gen_text": gen_text
            }  # 不提供ref_text
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            # 发送请求
            print(f"正在上传文件：{os.path.basename(REF_AUDIO_PATH)}")
            print(f"生成文本：{gen_text}")
            
            response = requests.post(endpoint, files=files, data=data, headers=headers)
            
            print(f"\n响应状态码：{response.status_code}")
            print(f"响应内容：{response.text}")
            
            return response.status_code == 200
    except Exception as e:
        print(f"\n❌ 测试失败！发生异常：{str(e)}")
        return False

# 运行测试
if __name__ == "__main__":
    test_transcribe()