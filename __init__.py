"""
CloudNet 机器人插件
功能：
1. /查询服务：获取 CloudNet 所有服务状态
2. /更新token：刷新 CloudNet Auth Token
"""

from nonebot.plugin import PluginMetadata
from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter

# 插件元数据（正确写法）
__plugin_meta__ = PluginMetadata(
    name="CloudNet 机器人",
    description="查询 CloudNet 服务状态、更新 Auth Token",
    usage="""
    指令列表：
    /查询服务 - 获取所有 CloudNet 服务的状态信息
    /更新token - 刷新 CloudNet Auth Token 并更新配置
    /刷新token - 同 /更新token（别名）
    """,
    type="application",
    homepage="https://github.com/你的用户名/cloudnet-bot",
    # 核心修复：直接使用适配器的 get_name() 方法，或写字符串 "onebot.v11"
    supported_adapters=(OnebotV11Adapter.get_name(),),
    extra={"author": "你的名字", "version": "1.0.0"},
)

# 加载子模块
from . import main
from .utils import api, resolve, tools

__all__ = ["__plugin_meta__"]