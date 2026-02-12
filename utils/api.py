import aiohttp
import base64
import json
from typing import Optional, Dict, Any, List
from nonebot.log import logger
from ..config import Config

CONFIG = Config()
BASE_URL = CONFIG.rest_host  # 例如 http://localhost:8080/api/v3


async def get_auth_token() -> Optional[Dict[str, Any]]:
    """极简版：用 Basic Auth 获取 CloudNet Token"""
    # 1. 生成 Basic Auth 头
    auth_str = f"{CONFIG.cloudnet_username}:{CONFIG.cloudnet_password}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode().strip()
    headers = {"Authorization": f"Basic {auth_b64}", "Content-Type": "application/json"}

    # 2. 发送 POST 请求
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{BASE_URL}/auth", headers=headers, json={}, timeout=10) as resp:
            # 3. 处理响应
            if resp.status != 200:
                logger.error(f"获取Token失败：{resp.status} {await resp.text()}")
                return None
            
            token_data = await resp.json()
            access_token = token_data.get("accessToken", {}).get("token")
            refresh_token = token_data.get("refreshToken", {}).get("token")
            
            return {"accessToken": access_token, "refreshToken": refresh_token} if access_token and refresh_token else None


async def list_cloudnet_services(access_token: str) -> Optional[List[Dict[str, Any]]]:
    """
    用获取到的 Bearer Token 查询服务
    """
    url = f"{BASE_URL}/service/all"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    services = await response.json()
                    if isinstance(services, list):
                        logger.info(f"✅ 获取到 {len(services)} 个服务")
                        return services
                    else:
                        logger.error("❌ 响应不是列表格式")
                else:
                    logger.error(f"❌ 查询服务失败：HTTP {response.status}")
    except Exception as e:
        logger.error(f"❌ 查询服务异常：{e}")
    return None