import requests
import os
from datetime import datetime

# API地址
API_URL = "http://localhost:8000"

# 参考音频文件路径
REF_AUDIO_PATH = "/Users/wangwenfei/Dev/github/F5-TTS/src/f5_tts/infer/examples/basic/basic_ref_en.wav"

# 验证参考音频文件是否存在
if not os.path.exists(REF_AUDIO_PATH):
    print(f"错误：参考音频文件不存在 {REF_AUDIO_PATH}")
    exit(1)

# 生成唯一的测试email
TEST_EMAIL = f"test_ref_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
TEST_PASSWORD = "password1234"

print(f"正在测试 /api/v1/clone 端点的 ref_audio 参数...")
print(f"API地址：{API_URL}")
print(f"测试邮箱：{TEST_EMAIL}")

# 1. 注册新用户
print("\n1. 注册新用户...")
register_endpoint = f"{API_URL}/api/v1/auth/register"
register_data = {
    "username": f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD
}

register_response = requests.post(register_endpoint, json=register_data)
if register_response.status_code != 200:
    print(f"❌ 用户注册失败：{register_response.text}")
    exit(1)
print("✅ 用户注册成功")

# 2. 登录获取token
print("\n2. 登录获取token...")
login_endpoint = f"{API_URL}/api/v1/auth/login"
login_data = {
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD
}

login_response = requests.post(login_endpoint, json=login_data)
if login_response.status_code != 200:
    print(f"❌ 用户登录失败：{login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
print(f"✅ 获取token成功：{token}")

# 3. 测试上传文件
print("\n3. 测试上传音频文件...")
clone_endpoint = f"{API_URL}/api/v1/clone"

headers = {
    "Authorization": f"Bearer {token}"
}

files = {
    "ref_audio": (os.path.basename(REF_AUDIO_PATH), open(REF_AUDIO_PATH, "rb"), "audio/wav"),
    "ref_text": (None, "Hello, this is a test message."),
    "gen_text": (None, "This is a test of the cloning functionality.")
}

response = requests.post(clone_endpoint, files=files, headers=headers)

if response.status_code == 200:
    print("✅ 文件上传和克隆成功！")
    print(f"响应：{response.json()}")
    print("\n🎉 修复成功！ref_audio参数现在应该在Swagger UI中显示为文件上传控件。")
else:
    print(f"❌ 文件上传和克隆失败！状态码：{response.status_code}")
    print(f"错误信息：{response.text}")
    print("\n❌ 修复可能未生效，请检查API实现。")

# 4. 检查Swagger UI中的API定义
print("\n4. 检查API文档定义...")
docs_endpoint = f"{API_URL}/openapi.json"
docs_response = requests.get(docs_endpoint)

if docs_response.status_code == 200:
    openapi_data = docs_response.json()
    clone_path = openapi_data["paths"]["/api/v1/clone"]
    post_operation = clone_path["post"]
    request_body = post_operation.get("requestBody", {})
    content = request_body.get("content", {})
    
    if "multipart/form-data" in content:
        print("✅ API定义正确使用了multipart/form-data类型")
        
        # 检查ref_audio参数定义
        schema = content["multipart/form-data"]["schema"]
        
        # 处理$ref引用
        if "$ref" in schema:
            ref_path = schema["$ref"].lstrip("#/")
            ref_parts = ref_path.split("/")
            
            # 从openapi_data中获取引用的schema
            ref_schema = openapi_data
            for part in ref_parts:
                ref_schema = ref_schema[part]
            
            schema = ref_schema
        
        properties = schema.get("properties", {})
        
        if "ref_audio" in properties:
            ref_audio_prop = properties["ref_audio"]
            
            # 检查anyOf定义
            if "anyOf" in ref_audio_prop:
                for option in ref_audio_prop["anyOf"]:
                    if option.get("format") == "binary":
                        print("✅ ref_audio参数定义为binary格式，应该在Swagger UI中显示为文件上传控件")
                        break
                else:
                    print("❌ ref_audio参数格式不正确，未找到binary格式定义")
                    print(f"完整定义：{ref_audio_prop}")
            elif ref_audio_prop.get("format") == "binary":
                print("✅ ref_audio参数定义为binary格式，应该在Swagger UI中显示为文件上传控件")
            else:
                print(f"❌ ref_audio参数格式不正确：{ref_audio_prop.get('format')}")
                print(f"完整定义：{ref_audio_prop}")
        else:
            print("❌ 未找到ref_audio参数定义")
            print(f"所有属性：{list(properties.keys())}")
            print(f"完整schema：{schema}")
    else:
        print("❌ API定义未使用multipart/form-data类型")
        print(f"Content类型：{list(content.keys())}")
else:
    print(f"❌ 获取API文档失败：{docs_response.status_code}")