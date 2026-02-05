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

print("开始测试F5-TTS API认证功能...")
print(f"API地址：{API_URL}")

# 测试用例1：用户注册
def test_register():
    print("\n=== 测试1：用户注册 ===")
    
    endpoint = f"{API_URL}/api/v1/auth/register"
    
    # 准备测试数据
    test_email = f"test_auth_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    test_username = f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_user = {
        "username": test_username,
        "email": test_email,
        "password": "password1234"
    }
    
    try:
        # 发送请求
        response = requests.post(endpoint, json=test_user)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 注册成功！")
            print(f"用户ID：{result['id']}")
            print(f"用户名：{result['username']}")
            print(f"邮箱：{result['email']}")
            return test_email, "password1234"  # 返回邮箱和密码用于后续测试
        else:
            print(f"❌ 注册失败！状态码：{response.status_code}")
            print(f"错误信息：{response.text}")
            return None, None
    except Exception as e:
        print(f"❌ 注册失败！发生异常：{str(e)}")
        return None, None

# 测试用例2：用户登录
def test_login(email, password):
    print("\n=== 测试2：用户登录 ===")
    
    if not email or not password:
        print("⚠️  跳过登录测试，因为注册失败")
        return None
    
    endpoint = f"{API_URL}/api/v1/auth/login"
    
    # 准备测试数据
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        # 发送请求
        response = requests.post(endpoint, json=login_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 登录成功！")
            print(f"访问令牌：{result['access_token']}")
            return result['access_token']  # 返回访问令牌用于后续测试
        else:
            print(f"❌ 登录失败！状态码：{response.status_code}")
            print(f"错误信息：{response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录失败！发生异常：{str(e)}")
        return None

# 测试用例3：使用认证令牌克隆声音
def test_voice_clone_with_auth(token):
    print("\n=== 测试3：使用认证令牌克隆声音 ===")
    
    if not token:
        print("⚠️  跳过声音克隆测试，因为获取令牌失败")
        return False
    
    endpoint = f"{API_URL}/api/v1/clone"
    
    # 准备测试数据
    ref_text = "Some call me nature, others call me mother nature."
    gen_text = "This is a test of the F5-TTS API service with authentication."
    
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
        print(f"正在执行声音克隆...")
        print(f"参考文本：{ref_text}")
        print(f"生成文本：{gen_text}")
        
        response = requests.post(endpoint, files=files, data=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 声音克隆成功！")
            print(f"状态：{result['success']}")
            print(f"消息：{result['message']}")
            print(f"音频URL：{API_URL}{result['audio_url']}")
            print(f"时长：{result['duration']}秒")
            return True
        else:
            print(f"\n❌ 声音克隆失败！状态码：{response.status_code}")
            print(f"错误信息：{response.text}")
            return False
    except Exception as e:
        print(f"\n❌ 声音克隆失败！发生异常：{str(e)}")
        return False

# 测试用例4：尝试匿名访问需要认证的API
def test_anonymous_clone():
    print("\n=== 测试4：尝试匿名访问需要认证的API ===")
    
    endpoint = f"{API_URL}/api/v1/clone"
    
    # 准备测试数据
    ref_text = "Some call me nature, others call me mother nature."
    gen_text = "This is a test of anonymous access to F5-TTS API."
    
    # 构建请求
    try:
        files = {
            "ref_audio": open(REF_AUDIO_PATH, "rb"),
        }
        data = {
            "ref_text": ref_text,
            "gen_text": gen_text,
        }
        
        # 发送请求（不包含认证令牌）
        response = requests.post(endpoint, files=files, data=data)
        
        if response.status_code == 401:
            print("✅ 验证成功！匿名访问被正确拒绝")
            print(f"状态码：{response.status_code}")
            print(f"错误信息：{response.text}")
            return True
        else:
            print(f"❌ 验证失败！匿名访问没有被正确拒绝")
            print(f"状态码：{response.status_code}")
            print(f"响应：{response.text}")
            return False
    except Exception as e:
        print(f"❌ 验证失败！发生异常：{str(e)}")
        return False

# 运行所有测试
def run_all_tests():
    email, password = test_register()
    token = test_login(email, password)
    clone_success = test_voice_clone_with_auth(token)
    anonymous_blocked = test_anonymous_clone()
    
    # 总结测试结果
    print("\n=== 测试总结 ===")
    print(f"测试1 (用户注册): {'通过' if email else '失败'}")
    print(f"测试2 (用户登录): {'通过' if token else '失败'}")
    print(f"测试3 (认证克隆): {'通过' if clone_success else '失败'}")
    print(f"测试4 (匿名访问控制): {'通过' if anonymous_blocked else '失败'}")
    
    # 计算通过率
    passed = sum([email is not None, token is not None, clone_success, anonymous_blocked])
    total = 4
    print(f"\n测试通过率：{passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有认证测试通过！API认证功能正常工作。")
        return True
    else:
        print("\n❌ 部分测试失败，请检查API认证配置。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)