from .config import Config
from .utils import api, parse_service_data
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, MessageSegment
from nonebot.log import logger
from nonebot.exception import FinishedException

# 更新Token命令
update_token_cmd = on_command(
    cmd="更新token",
    aliases={"刷新token", "获取新token"},
    priority=1,
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

        # 5. 脱敏处理（极简逻辑）
        def desensitize(t: str) -> str:
            return t if len(t) <= 12 else f"{t[:8]}...{t[-4:]}"

        access_show = desensitize(access_token)
        refresh_show = desensitize(refresh_token)

        # 6. 消息格式化（简洁且QQ显示正常）
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