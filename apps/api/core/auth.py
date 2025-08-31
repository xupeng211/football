"""
JWT认证模块

提供API token认证功能
"""

import os
from datetime import datetime, timedelta
from typing import Any, Optional

import jwt
import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 安全方案
security = HTTPBearer()


class TokenData(BaseModel):
    """Token数据模型"""

    username: Optional[str] = None
    scopes: list[str] = []


class User(BaseModel):
    """用户模型"""

    username: str
    email: Optional[str] = None
    is_active: bool = True
    scopes: list[str] = []


def create_access_token(
    data: dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 过期时间差

    Returns:
        JWT访问令牌
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    logger.info("Created access token", username=data.get("sub"), expires=expire)
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    验证JWT令牌

    Args:
        token: JWT令牌

    Returns:
        TokenData: 解码后的令牌数据

    Raises:
        HTTPException: 令牌无效或过期
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")

        if username is None:
            logger.warning("Token missing username")
            raise credentials_exception

        scopes = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=scopes)

        logger.debug("Token verified successfully", username=username)
        return token_data

    except jwt.PyJWTError as e:
        logger.warning("Token verification failed", error=str(e))
        raise credentials_exception


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    获取当前用户

    Args:
        credentials: HTTP认证凭据

    Returns:
        User: 当前用户信息

    Raises:
        HTTPException: 认证失败
    """
    token_data = verify_token(credentials.credentials)

    # 这里可以从数据库或其他数据源获取用户信息
    # 目前使用简单的硬编码用户
    user = get_user_by_username(token_data.username)

    if user is None:
        logger.warning("User not found", username=token_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_user_by_username(username: str) -> Optional[User]:
    """
    根据用户名获取用户信息

    Args:
        username: 用户名

    Returns:
        User: 用户信息，如果不存在则返回None
    """
    # 简单的用户数据库（实际应用中应该从数据库获取）
    fake_users_db = {
        "admin": User(
            username="admin",
            email="admin@example.com",
            is_active=True,
            scopes=["read", "write", "admin"],
        ),
        "user": User(
            username="user", email="user@example.com", is_active=True, scopes=["read"]
        ),
        "api_key": User(
            username="api_key",
            email="api@example.com",
            is_active=True,
            scopes=["read", "predict"],
        ),
    }

    return fake_users_db.get(username)


def require_scopes(required_scopes: list[str]):
    """
    创建需要特定权限的依赖项

    Args:
        required_scopes: 需要的权限列表

    Returns:
        Dependency function
    """

    def check_scopes(current_user: User = Depends(get_current_user)) -> User:
        for scope in required_scopes:
            if scope not in current_user.scopes:
                logger.warning(
                    "Insufficient permissions",
                    username=current_user.username,
                    required=required_scopes,
                    has=current_user.scopes,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation requires '{scope}' permission",
                )
        return current_user

    return check_scopes


# 常用的权限依赖项
require_read = require_scopes(["read"])
require_write = require_scopes(["write"])
require_admin = require_scopes(["admin"])
require_predict = require_scopes(["predict"])
