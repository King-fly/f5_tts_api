from fastapi.security import OAuth2PasswordBearer

# 定义OAuth2密码Bearer方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")