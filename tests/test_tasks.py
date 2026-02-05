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

print("开始测试F5-TTS API任务管理功能...")
print(f"API地址：{API_URL}")

# 测试辅助函数：获取认证令牌
def get_auth_token():
    print("\n=== 获取认证令牌 ===")
    
    # 先注册一个临时用户
    register_endpoint = f"{API_URL}/api/v1/auth/register"
    test_email = f"test_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    test_username = f"testuser_tasks_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
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

# 测试用例1：上传音频样本
def test_upload_audio(token):
    print("\n=== 测试1：上传音频样本 ===")
    
    if not token:
        print("❌ 跳过测试，因为没有认证令牌")
        return None
    
    endpoint = f"{API_URL}/api/v1/samples"
    
    try:
        with open(REF_AUDIO_PATH, "rb") as f:
            files = {
                "file": (os.path.basename(REF_AUDIO_PATH), f, "audio/wav")
            }
            data = {
                "text": "Hello, this is a test message."
            }
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            # 发送请求
            print(f"正在上传音频文件：{os.path.basename(REF_AUDIO_PATH)}")
            
            response = requests.post(endpoint, files=files, data=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 音频上传成功！")
                print(f"音频ID：{result['id']}")
                print(f"文件名：{result['filename']}")
                print(f"时长：{result['duration']}秒")
                return result['id']  # 返回音频ID用于后续测试
            else:
                print(f"❌ 音频上传失败！状态码：{response.status_code}")
                print(f"错误信息：{response.text}")
                return None
    except Exception as e:
        print(f"❌ 音频上传失败！发生异常：{str(e)}")
        return None

# 测试用例2：创建克隆任务
def test_create_cloning_task(token, audio_id):
    print("\n=== 测试2：创建克隆任务 ===")
    
    if not token or not audio_id:
        print("❌ 跳过测试，因为没有认证令牌或音频ID")
        return None
    
    endpoint = f"{API_URL}/api/v1/tasks"
    
    # 准备测试数据
    test_text = "This is a test of the cloning task functionality."
    
    task_data = {
        "audio_sample_id": audio_id,
        "text": test_text
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        # 发送请求
        print(f"正在创建克隆任务...")
        print(f"音频ID：{audio_id}")
        print(f"生成文本：{test_text}")
        
        response = requests.post(endpoint, json=task_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 任务创建成功！")
            print(f"任务ID：{result['id']}")
            print(f"状态：{result['status']}")
            print(f"创建时间：{result['created_at']}")
            return result['id']  # 返回任务ID用于后续测试
        else:
            print(f"❌ 任务创建失败！状态码：{response.status_code}")
            print(f"错误信息：{response.text}")
            return None
    except Exception as e:
        print(f"❌ 任务创建失败！发生异常：{str(e)}")
        return None

# 测试用例3：获取任务列表
def test_get_tasks_list(token):
    print("\n=== 测试3：获取任务列表 ===")
    
    if not token:
        print("❌ 跳过测试，因为没有认证令牌")
        return False
    
    endpoint = f"{API_URL}/api/v1/tasks"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # 发送请求
        print(f"正在获取任务列表...")
        
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 获取任务列表成功！")
            print(f"任务数量：{len(result)}")
            for task in result:
                print(f"  - 任务ID：{task['id']}，状态：{task['status']}")
            return True
        else:
            print(f"❌ 获取任务列表失败！状态码：{response.status_code}")
            print(f"错误信息：{response.text}")
            return False
    except Exception as e:
        print(f"❌ 获取任务列表失败！发生异常：{str(e)}")
        return False

# 测试用例4：获取单个任务
def test_get_single_task(token, task_id):
    print("\n=== 测试4：获取单个任务 ===")
    
    if not token or not task_id:
        print("❌ 跳过测试，因为没有认证令牌或任务ID")
        return False
    
    endpoint = f"{API_URL}/api/v1/tasks/{task_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        # 发送请求
        print(f"正在获取任务ID：{task_id}...")
        
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 获取任务详情成功！")
            print(f"任务ID：{result['id']}")
            print(f"音频ID：{result['audio_sample_id']}")
            print(f"生成文本：{result['text']}")
            print(f"状态：{result['status']}")
            print(f"创建时间：{result['created_at']}")
            print(f"更新时间：{result['updated_at']}")
            return True
        else:
            print(f"❌ 获取任务详情失败！状态码：{response.status_code}")
            print(f"错误信息：{response.text}")
            return False
    except Exception as e:
        print(f"❌ 获取任务详情失败！发生异常：{str(e)}")
        return False

# 运行所有测试
def run_all_tests():
    print("\n=== 开始执行任务管理API测试 ===")
    
    # 获取认证令牌
    token = get_auth_token()
    if not token:
        print("\n❌ 无法获取认证令牌，测试终止")
        return False
    
    # 测试1：上传音频样本
    audio_id = test_upload_audio(token)
    if not audio_id:
        print("\n❌ 无法上传音频样本，后续测试终止")
        return False
    
    # 测试2：创建克隆任务
    task_id = test_create_cloning_task(token, audio_id)
    
    # 测试3：获取任务列表
    tasks_list_success = test_get_tasks_list(token)
    
    # 测试4：获取单个任务
    single_task_success = test_get_single_task(token, task_id) if task_id else False
    
    # 总结测试结果
    print("\n=== 测试总结 ===")
    print(f"测试1 (上传音频样本): {'通过' if audio_id else '失败'}")
    print(f"测试2 (创建克隆任务): {'通过' if task_id else '失败'}")
    print(f"测试3 (获取任务列表): {'通过' if tasks_list_success else '失败'}")
    print(f"测试4 (获取单个任务): {'通过' if single_task_success else '失败'}")
    
    # 计算通过率
    passed = sum([audio_id is not None, task_id is not None, tasks_list_success, single_task_success])
    total = 4
    print(f"\n测试通过率：{passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有任务管理API测试通过！")
        return True
    else:
        print("\n❌ 部分测试失败，请检查API实现。")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)