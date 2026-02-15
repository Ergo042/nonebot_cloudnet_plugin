import aiohttp
import base64
import json
from typing import Optional, Dict, Any, List
from nonebot.log import logger
from ..config import Config,rest_access_key

CONFIG = Config()
BASE_URL = CONFIG.rest_host  # 例如 http://localhost:8080/api/v3

'''
权限管理部分
'''
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

'''
服务处理部分
'''

async def list_cloudnet_services(access_token:str = rest_access_key) -> Optional[List[Dict[str, Any]]]:
    """
    用获取到的 Bearer Token 查询服务
    """
    url = f"{BASE_URL}/service"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    services = await response.json()
                    if isinstance(services["services"], list):
                        logger.info(f"✅ 获取到 {len(services['services'])} 个服务")
                        return services["services"]
                    else:
                        logger.error("❌ 响应不是列表格式")
                else:
                    logger.error(f"❌ 查询服务失败：HTTP {response.status}")
    except Exception as e:
        logger.error(f"❌ 查询服务异常：{e}")
    return None

async def create_service(service_name: str, access_token: str = rest_access_key):
    """
    创建新服务的函数
    """
    url = f"{BASE_URL}/service/create/taskName"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "taskName": service_name,
    }

    # 发送post请求
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=10) as response:
                if response.status == 200 or response.status == 201:
                    logger.info(f"✅ 服务 '{service_name}' 创建成功")
                    return await response.json()
                else:
                    logger.error(f"❌ 创建服务失败：HTTP {response.status} - {await response.text()}")
    except Exception as e:
        logger.error(f"❌ 创建服务异常：{e}")

async def get_template_list(access_token: str = rest_access_key) -> Optional[List[str]]:
    """
    获取可用模板列表
    """
    url = f"{BASE_URL}/templateStorage/local/templates"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    templates = await response.json()
                    if isinstance(templates["templates"], list):
                        logger.info(f"✅ 获取到 {len(templates['templates'])} 个模板")
                        return [t["name"] for t in templates["templates"]]
                    else:
                        logger.error("❌ 响应不是列表格式")
                else:
                    logger.error(f"❌ 查询模板失败：HTTP {response.status}")
    except Exception as e:
        logger.error(f"❌ 查询模板异常：{e}")

async def list_tasks(access_token: str = rest_access_key) -> Optional[List[Dict[str, Any]]]:
    """
    获取任务列表
    """
    url = f"{BASE_URL}/task"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    tasks = await response.json()
                    if isinstance(tasks["tasks"], list):
                        logger.info(f"✅ 获取到 {len(tasks['tasks'])} 个任务")
                        return tasks["tasks"]
                    else:
                        logger.error("❌ 响应不是列表格式")
                else:
                    logger.error(f"❌ 查询任务失败：HTTP {response.status}")
    except Exception as e:
        logger.error(f"❌ 查询任务异常：{e}")
    return None

async def life_cycle_action(service_id: str, action: str, access_token: str = rest_access_key) -> bool:
    """
    对服务执行生命周期操作（start/stop/restart）
    """
    if action not in {"start", "stop", "restart"}:
        logger.error(f"❌ 无效的生命周期操作：{action}")
        return False
    url = f"{BASE_URL}/service/{service_id}/lifecycle"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    target = {"target": action}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(url, headers=headers,params=target, timeout=10) as response:
                if response.status == 204:
                    logger.info(f"✅ 服务 {service_id} 执行 {action} 成功")
                    return True
                elif response.status == 404:
                    logger.error(f"❌ 服务 {service_id} 不存在，无法执行 {action}")
                else:
                    logger.error(f"❌ 服务 {service_id} 执行 {action} 失败：HTTP {response.status} - {await response.text()}")
    except Exception as e:
        logger.error(f"❌ 服务 {service_id} 执行 {action} 异常：{e}")