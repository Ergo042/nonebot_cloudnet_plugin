import datetime

from .utils.resolve import tasks_data
from .config import Config
from .utils import api, parse_service_data
from .utils.tools import update_config_param
from nonebot.rule import to_me, is_type, Rule
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment, Message
from nonebot.log import logger
from nonebot.exception import FinishedException
from nonebot.typing import T_State
from nonebot.params import CommandArg,Arg

# ========================帮助指令========================
help_cmd = on_command(
    cmd="cloudnet帮助",
    aliases={"云服务器帮助", "服务器帮助", "cn帮助", "help", "帮助", "菜单"},
    rule=to_me() & is_type("group"),  # 仅响应@机器人或群消息
    priority=11,
    block=True,
)

@help_cmd.handle()
async def handle_help(event: MessageEvent):
    """CloudNet 服务器管理插件帮助"""
    help_msg = """
🎮 CloudNet 服务器管理助手 🎮
————————————————
📌 【基础功能】
1. 更新Token
   指令：更新token / 刷新token / 获取新token
   说明：获取并更新 CloudNet API 认证Token

2. 查询服务器信息
   指令：获取服务器信息 / 查询服务器信息 / 查看服务器状态
   说明：查看所有服务器的运行状态、资源占用等详细信息

📌 【服务器管理】
3. 创建新服务器
   指令：创建服务器 / 新建服务器 / 启动新服务器
   说明：选择Task创建新的服务器实例

4. 启动服务器
   指令：启动服务器 [服务器ID] / 开启服务器 [服务器ID]
   示例：启动服务器 Lobby-2
   说明：将PREPARED状态的服务器启动为RUNNING

5. 重启服务器
   指令：重启服务器 [服务器ID] / 重新启动服务器 [服务器ID]
   示例：重启服务器 Lobby-2
   说明：重启指定运行中的服务器

6. 停止服务器
   指令：停止服务器 [服务器ID] / 关闭服务器 [服务器ID]
   示例：停止服务器 Lobby-2
   说明：将RUNNING状态的服务器停止为STOPPED

📌 【使用提示】
🔸 服务器ID可通过「获取服务器信息」指令查看
🔸 创建服务器时需根据提示输入Task编号
🔸 所有指令无需区分大小写，支持简写
————————————————
💡 更多功能制作中
    """.strip()
    await help_cmd.finish(MessageSegment.text(help_msg))
# ========================默认回复========================
# 定义兜底指令（优先级最低，确保最后触发）
default_reply = on_command(
    cmd="",  # 空命令，匹配所有未被其他指令捕获的消息
    priority=999,  # 优先级设为999（最低），确保其他命令先匹配
    block=True     # 触发后阻断后续逻辑，避免重复回复
)

@default_reply.handle()
async def handle_default_reply(
    event: MessageEvent,
):
    """无匹配指令时的兜底回复逻辑"""
    # 1. 过滤空消息/纯表情/纯空格（避免无效回复）
    msg_text = event.get_message().extract_plain_text()
    if not msg_text.strip():
        return  # 不回复空消息或纯表情等无意义内容
    
    # 2. 友好提示 + 引导使用帮助指令
    default_msg = f"""
🤔 暂未识别到该指令：「{msg_text.strip()}」

💡 你可以尝试以下操作：
✅ 发送「cloudnet帮助」「帮助」或「help」查看所有可用指令
✅ 检查指令是否输入正确（支持别名：如「更新token」=「刷新token」）
✅ 常用指令示例：
   • 更新token —— 更新CloudNet认证Token
   • 获取服务器信息 —— 查看所有服务器状态
   • 启动服务器 Lobby-2 —— 启动指定服务器

    """.strip()
    
    # 3. 发送兜底回复（适配QQ消息格式）
    await default_reply.finish(MessageSegment.text(default_msg))
# ========================功能指令========================


# 更新Token命令
update_token_cmd = on_command(
    cmd="更新token",
    aliases={"刷新token", "获取新token"},
    rule=to_me() & is_type("group"),  # 仅响应@机器人或群消息
    priority=15,
    block=True
)

@update_token_cmd.handle()
async def handle_update_token(event: MessageEvent):
    await update_token_cmd.send(MessageSegment.text("✅ 开始获取并更新 CloudNet Auth Token..."))

    try:
        # 1. 调用API获取Token
        token_result = await api.get_auth_token()

        # 2. 基础校验：返回空/非字典直接失败
        if not isinstance(token_result, dict):
            fail_msg = (
                "❌ Token 更新失败！\n"
                "请检查：\n"
                "1. API地址/用户名密码是否正确\n"
                "2. CloudNet 服务是否运行\n"
                "3. 网络是否通畅"
            )
            await update_token_cmd.finish(MessageSegment.text(fail_msg))

        # 3. 安全提取Token（兼容单层字典，避免KeyError）
        access_token = token_result.get("accessToken", "").strip()
        refresh_token = token_result.get("refreshToken", "").strip()
        
        # 4. 校验Token是否有效
        if not access_token or not refresh_token:
            logger.error(f"Token返回异常：{token_result}")
            await update_token_cmd.finish(
                MessageSegment.text("❌ Token 更新失败：返回的Token为空！")
            )

        # 5. 更新配置文件（适配 Python 格式的 config.py)
        update_config_param("rest_access_key", access_token)
        update_config_param("rest_refresh_key", refresh_token)

        # 6. 脱敏处理（极简逻辑）
        def desensitize(t: str) -> str:
            return t if len(t) <= 12 else f"{t[:8]}...{t[-4:]}"

        access_show = desensitize(access_token)
        refresh_show = desensitize(refresh_token)

        # 7. 消息格式化
        final_msg = f"""🎉 Token 更新成功！

📌 Access Token：{access_show}
📌 Refresh Token：{refresh_show}

✅ 已自动更新至配置文件
💡 后续 API 调用将使用新 Token"""

        # 7. 结束会话（只发送一次，杜绝重复）
        await update_token_cmd.finish(MessageSegment.text(final_msg))

    except FinishedException:
        pass  # 正常结束，不处理
    except Exception as e:
        logger.error(f"Token 更新异常：{str(e)}", exc_info=True)
        await update_token_cmd.finish(
            MessageSegment.text(f"❌ 更新出错：{str(e)}\n请查看后台日志")
        )

# 获取服务器信息命令
get_services_cmd = on_command(
    cmd="获取服务器信息",
    aliases={"查询服务器信息", "查看服务器状态"},
    rule=to_me() & is_type("group"),  # 仅响应@机器人或群消息
    priority=60,
    block=True
)

@get_services_cmd.handle()
async def handle_get_services(event: MessageEvent):
    await get_services_cmd.send(MessageSegment.text("🔍 正在获取服务器信息..."))

    try:
        # 1. 调用API获取服务器数据
        services_result = await api.list_cloudnet_services()

        # 2. 基础校验：返回空/非列表直接失败
        if not isinstance(services_result, list):
            fail_msg = (
                "❌ 获取服务器信息失败！\n"
                "请检查：\n"
                "1. API地址/用户名密码是否正确\n"
                "2. CloudNet 服务是否运行\n"
                "3. 网络是否通畅"
            )
            await get_services_cmd.finish(MessageSegment.text(fail_msg))

        # 3. 解析并格式化服务器信息
        services_info = parse_service_data(services_result)

        # 4. 消息格式化（简洁且QQ显示正常）
        service_cards = []
        for idx, info in enumerate(services_info, 1):
            card = f"""
    ┌────────── 服务器 {idx} ──────────
    │ 📛 服务名称：{info['服务名称']}
    │ 🆔 唯一ID：{info['uniqueId']}
    │ 📌 服务类型：{info['服务类型']}
    │ 🔧 服务模版：{info['服务模版']}
    │ 📍 绑定地址：{info['绑定地址']}
    │ 🕒 创建时间：{info['创建时间']}
    │ 🟢 运行状态：{info['运行状态']}
    │ 🆔 进程PID：{info['PID']}
    │ 📊 CPU使用率：{info['CPU 使用率']}
    │ 📈 内存使用：{info['内存使用']}
    │ 👥 在线人数：{info['在线人数']}
    │ 🎯 服务版本：{info['服务版本']}
    └───────────────────────────────"""
            service_cards.append(card)
        
        # 最终消息拼接
        final_msg = f"""🎉 服务器信息获取成功！
    📋 共检测到 {len(services_info)} 个服务器节点：
    {''.join(service_cards)}

    ✅ 数据来源：CloudNet API
    🕙 更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        # 5. 结束会话
        await get_services_cmd.finish(MessageSegment.text(final_msg))

    except FinishedException:
        pass  # 正常结束，不处理
    except Exception as e:
        logger.error(f"获取服务器信息异常：{str(e)}", exc_info=True)
        await get_services_cmd.finish(
            MessageSegment.text(f"❌ 获取出错：{str(e)}\n请查看后台日志")
        )

# 创建服务器命令
create_service_cmd = on_command(
    cmd="创建服务器",
    aliases={"新建服务器", "启动新服务器"},
    rule=to_me() & is_type("group"),  # 仅响应@机器人或群消息
    priority=15,
    block=True
)

@create_service_cmd.handle()
async def handle_create_service(event: MessageEvent,state: T_State):
    try: 
        # 1.尝试获取服务器task列表
        tasks = await api.list_tasks()
        if not isinstance(tasks, list) or not tasks:
            await create_service_cmd.finish(
                MessageSegment.text("❌ 获取服务器任务失败，无法创建服务器！")
            )
        # 2. 提取任务名称列表
        state["task_names"] = tasks_data(tasks)  # 存储任务列表到状态，供后续步骤使用
        # 3. 给任务编号并发送任务列表给用户，提示输入任务编号
        task_msg = "请选择服务器任务（输入编号）：\n" + "\n".join(
            [f"{idx + 1}. {name}" for idx, name in enumerate(state["task_names"])]
        )
        await create_service_cmd.send(MessageSegment.text(task_msg))
        # 4. 等待用户输入任务编号
    except FinishedException:
        pass  # 正常结束，不处理
    except Exception as e:
        logger.error(f"创建服务器异常：{str(e)}", exc_info=True)
        await create_service_cmd.finish(
            MessageSegment.text(f"❌ 创建服务器出错：{str(e)}\n请查看后台日志")
        )
@create_service_cmd.got("task_index", prompt="请输入任务编号：") 
async def handle_task_index(state: T_State, task_index: Message = Arg()):
    try:
        index = int(task_index.extract_plain_text().strip()) - 1
        if index < 0 or index >= len(state["task_names"]):
            await create_service_cmd.finish(
                MessageSegment.text("❌ 编号无效，请重新执行命令并输入正确编号！")
            )
        selected_task = state["task_names"][index]
        # 5. 调用API创建服务器
        create_result = await api.create_service(selected_task)
        if create_result:
            await create_service_cmd.finish(
                MessageSegment.text(f"🎉 服务器创建成功！使用任务：{selected_task}")
            )
        else:
            await create_service_cmd.finish(
                MessageSegment.text("❌ 服务创建失败，请查看后台日志！")
            )
    except ValueError:
        await create_service_cmd.finish(
            MessageSegment.text("❌ 输入无效，请输入数字编号！")
        )

#服务器的生命周期操作
start_service_cmd = on_command(
    cmd="启动服务器",
    aliases={"开启服务器", "运行服务器"},
    rule=to_me() & is_type("group"),  # 仅响应@机器人或群消息
    priority=15,
    block=True
)
@start_service_cmd.handle()
async def handle_start_service(CommandArg: Message = CommandArg()):
    try:
        # 1. 获取用户输入的服务器唯一ID
        service_id = CommandArg
        if not service_id:
            await start_service_cmd.finish(
                MessageSegment.text("❌ 请提供要启动的服务器！")
            )
        # 2. 调用API执行启动操作
        result = await api.life_cycle_action(service_id, "start")
        if result:
            await start_service_cmd.finish(
                MessageSegment.text(f"🎉 服务器 {service_id} 启动成功！")
            )
        else:
            await start_service_cmd.finish(
                MessageSegment.text(f"❌ 服务器 {service_id} 启动失败，请检查服务器是否已存在！")
            )
    except FinishedException:
        pass  # 正常结束，不处理

restart_service_cmd = on_command(
    cmd="重启服务器",
    aliases={"重启服务器", "重新启动服务器"},
    rule=to_me() & is_type("group"),  # 仅响应@机器人或群消息
    priority=15,
    block=True
)
@restart_service_cmd.handle()
async def handle_restart_service(arg: Message = CommandArg()):
    try:
        # 1. 获取用户输入的服务器唯一ID
        service_id = arg.extract_plain_text().strip()
        if not service_id:
            await restart_service_cmd.finish(
                MessageSegment.text("❌ 请提供要重启的服务器！")
            )
        # 2. 调用API执行重启操作
        result = await api.life_cycle_action(service_id, "restart")
        if result:
            await restart_service_cmd.finish(
                MessageSegment.text(f"🎉 服务器 {service_id} 重启成功！")
            )
        else:
            await restart_service_cmd.finish(
                MessageSegment.text(f"❌ 服务器 {service_id} 重启失败，请检查服务器是否已存在！")
            )
    except FinishedException:
        pass  # 正常结束，不处理

stop_service_cmd = on_command(
    cmd="停止服务器",
    aliases={"关闭服务器", "停止运行服务器"},
    rule=to_me() & is_type("group"),  # 仅响应@机器人或群消息
    priority=15,
    block=True
)
@stop_service_cmd.handle()
async def handle_stop_service(CommandArg: Message = CommandArg()):
    try:
        # 1. 获取用户输入的服务器唯一ID
        service_id = CommandArg
        if not service_id:
            await stop_service_cmd.finish(
                MessageSegment.text("❌ 请提供要停止的服务器！")
            )
        # 2. 调用API执行停止操作
        result = await api.life_cycle_action(service_id, "stop")
        if result:
            await stop_service_cmd.finish(
                MessageSegment.text(f"🎉 服务器 {service_id} 停止成功！")
            )
        else:
            await stop_service_cmd.finish(
                MessageSegment.text(f"❌ 服务器 {service_id} 停止失败，请检查服务器是否已存在！")
            )
    except FinishedException:
        pass  # 正常结束，不处理