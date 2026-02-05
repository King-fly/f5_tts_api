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

print("开始测试F5-TTS API ref_audio参数处理...")
print(f"API地址：{API_URL}")

# 测试辅助函数：获取认证令牌
def get_auth_token():
    print("\n=== 获取认证令牌 ===")
    
    # 先注册一个临时用户
    register_endpoint = f"{API_URL}/api/v1/auth/register"
    test_email = f"test_ref_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    test_username = f"testuser_ref_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
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

# 测试用例1：正常的文件上传
def test_normal_file_upload(token):
    print("\n=== 测试1：正常的文件上传 ===")
    
    if not token:
        print("❌ 跳过测试，因为没有认证令牌")
        return False
    
    endpoint = f"{API_URL}/api/v1/clone"
    
    # 准备测试数据
    ref_text = "Some call me nature, others call me mother nature."
    gen_text = "This is a test of normal file upload functionality."
    
    try:
        with open(REF_AUDIO_PATH, "rb") as f:
            files = {
                "ref_audio": (os.path.basename(REF_AUDIO_PATH), f, "audio/wav")
            }
            data = {
                "ref_text": ref_text,
                "gen_text": gen_text
            }
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            # 发送请求
            print(f"正在上传文件：{os.path.basename(REF_AUDIO_PATH)}")
            print(f"参考文本：{ref_text}")
            print(f"生成文本：{gen_text}")
            
            response = requests.post(endpoint, files=files, data=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ 文件上传成功！")
                print(f"状态：{result['success']}")
                print(f"消息：{result['message']}")
                print(f"音频URL：{API_URL}{result['audio_url']}")
                print(f"时长：{result['duration']}秒")
                return True
            else:
                print(f"\n❌ 文件上传失败！状态码：{response.status_code}")
                print(f"错误信息：{response.text}")
                return False
    except Exception as e:
        print(f"\n❌ 文件上传失败！发生异常：{str(e)}")
        return False

# 测试用例2：没有提供ref_text（自动转录）
def test_auto_transcribe(token):
    print("\n=== 测试2：没有提供ref_text（自动转录） ===")
    
    if not token:
        print("❌ 跳过测试，因为没有认证令牌")
        return False
    
    endpoint = f"{API_URL}/api/v1/clone"
    
    # 准备测试数据（不提供ref_text）
    gen_text = "This is a test of automatic transcription functionality."
    
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
            print(f"（不提供ref_text，测试自动转录功能）")
            print(f"生成文本：{gen_text}")
            
            response = requests.post(endpoint, files=files, data=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ 自动转录成功！")
                print(f"状态：{result['success']}")
                print(f"消息：{result['message']}")
                print(f"音频URL：{API_URL}{result['audio_url']}")
                print(f"时长：{result['duration']}秒")
                return True
            else:
                print(f"\n❌ 自动转录失败！状态码：{response.status_code}")
                print(f"错误信息：{response.text}")
                return False
    except Exception as e:
        print(f"\n❌ 自动转录失败！发生异常：{str(e)}")
        return False

# 测试用例3：不提供ref_audio或ref_audio_url
def test_missing_audio(token):
    print("\n=== 测试3：不提供ref_audio或ref_audio_url ===")
    
    if not token:
        print("❌ 跳过测试，因为没有认证令牌")
        return False
    
    endpoint = f"{API_URL}/api/v1/clone"
    
    # 准备测试数据（不提供任何音频）
    data = {
        "ref_text": "Some call me nature, others call me mother nature.",
        "gen_text": "This is a test of missing audio validation."
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # 发送请求
        print("正在测试：不提供任何音频")
        
        response = requests.post(endpoint, data=data, headers=headers)
        
        if response.status_code == 400:
            print("\n✅ 验证成功！系统正确拒绝了缺少音频的请求")
            print(f"状态码：{response.status_code}")
            print(f"错误信息：{response.text}")
            return True
        else:
            print(f"\n❌ 验证失败！系统没有正确拒绝缺少音频的请求")
            print(f"状态码：{response.status_code}")
            print(f"响应：{response.text}")
            return False
    except Exception as e:
        print(f"\n❌ 测试失败！发生异常：{str(e)}")
        return False

# 测试用例4：测试clone_voice_from_url功能
def test_clone_from_url(token):
    print("\n=== 测试4：使用URL方式克隆声音 ===")
    
    if not token:
        print("❌ 跳过测试，因为没有认证令牌")
        return False
    
    endpoint = f"{API_URL}/api/v1/clone"
    
    # 使用公开可用的参考音频URL
    # 注意：这个URL可能会过期，需要替换为有效的音频URL
    ref_audio_url = "https://www2.cs.uic.edu/~i101/SoundFiles/CantinaBand3.wav"
    ref_text = "This is a test of clone from URL functionality."
    gen_text = "This audio was generated using a reference audio from URL."
    
    try:
        data = {
            "ref_audio_url": ref_audio_url,
            "ref_text": ref_text,
            "gen_text": gen_text
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # 发送请求
        print(f"正在使用URL：{ref_audio_url}")
        print(f"参考文本：{ref_text}")
        print(f"生成文本：{gen_text}")
        
        response = requests.post(endpoint, data=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 从URL克隆成功！")
            print(f"状态：{result['success']}")
            print(f"消息：{result['message']}")
            print(f"音频URL：{API_URL}{result['audio_url']}")
            print(f"时长：{result['duration']}秒")
            return True
        else:
            print(f"\n❌ 从URL克隆失败！状态码：{response.status_code}")
            print(f"错误信息：{response.text}")
            return False
    except Exception as e:
        print(f"\n❌ 从URL克隆失败！发生异常：{str(e)}")
        return False

# 运行所有测试
def run_all_tests():
    # 获取认证令牌
    token = get_auth_token()
    
    if not token:
        print("\n❌ 无法获取认证令牌，无法进行测试")
        sys.exit(1)
    
    # 运行测试
    test1_passed = test_normal_file_upload(token)
    test2_passed = test_auto_transcribe(token)
    test3_passed = test_missing_audio(token)
    test4_passed = test_clone_from_url(token)
    
    # 总结测试结果
    print("\n=== 测试总结 ===")
    print(f"测试1 (正常文件上传): {'通过' if test1_passed else '失败'}")
    print(f"测试2 (自动转录): {'通过' if test2_passed else '失败'}")
    print(f"测试3 (缺少音频验证): {'通过' if test3_passed else '失败'}")
    print(f"测试4 (URL克隆): {'通过' if test4_passed else '失败'}")
    
    # 计算通过率
    passed = sum([test1_passed, test2_passed, test3_passed, test4_passed])
    total = 4
    print(f"\n测试通过率：{passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有ref_audio参数测试通过！")
        return True
    else:
        print("\n❌ 部分测试失败，请检查API实现。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)