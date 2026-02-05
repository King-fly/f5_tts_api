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

print("开始测试F5-TTS声音克隆API核心功能...")
print(f"API地址：{API_URL}")
print(f"参考音频：{REF_AUDIO_PATH}")

# 获取认证令牌
def get_auth_token():
    print("\n正在获取认证令牌...")
    
    # 先注册一个临时用户
    register_endpoint = f"{API_URL}/api/v1/auth/register"
    test_email = f"test_voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    test_username = f"testuser_voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
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

# 准备测试数据
ref_text = "Some call me nature, others call me mother nature."
gen_text = "This is a test of the F5-TTS API service."

# 获取认证令牌
token = get_auth_token()
if not token:
    print("\n❌ 无法获取认证令牌，测试失败")
    sys.exit(1)

# 构建请求
try:
    files = {
        "ref_audio": open(REF_AUDIO_PATH, "rb"),
    }
    data = {
        "ref_text": ref_text,
        "gen_text": gen_text,
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 发送请求
    print("\n正在执行声音克隆...")
    print(f"参考文本：{ref_text}")
    print(f"生成文本：{gen_text}")
    
    response = requests.post(f"{API_URL}/api/v1/clone", files=files, data=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ 声音克隆成功！")
        print(f"状态：{result['success']}")
        print(f"消息：{result['message']}")
        print(f"音频URL：{API_URL}{result['audio_url']}")
        print(f"时长：{result['duration']}秒")
        sys.exit(0)
    else:
        print(f"\n❌ 声音克隆失败！状态码：{response.status_code}")
        print(f"错误信息：{response.text}")
        sys.exit(1)
except Exception as e:
    print(f"\n❌ 发生异常：{str(e)}")
    sys.exit(1)