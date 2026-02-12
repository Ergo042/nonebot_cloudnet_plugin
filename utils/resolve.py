from typing import Optional, Dict, Any, List
from datetime import datetime


def parse_service_data(services: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    【独立解析函数】格式化 API 返回的服务数据，转为易读格式（纯数据处理）
    :param services: list_cloudnet_services 函数返回的服务列表
    :return: 格式化后的服务信息列表
    """
    parsed_result = []
    for service in services:
        # 提取各层级字段（容错处理，避免字段缺失报错）
        address = service.get("address", {})
        process_snap = service.get("processSnapshot", {})
        config = service.get("configuration", {})
        props = service.get("properties", {})
        # 修复：service_id 是字符串/字典，加容错，避免 get 报错
        service_id = config.get("serviceId", {}) or {}

        # 数据格式化（时间戳转时间、字节转 MB）
        # 修复：处理 0 时间戳，避免 datetime 报错
        creation_time = service.get("creationTime", 0)
        create_time = datetime.fromtimestamp(creation_time / 1000).strftime(
            "%Y-%m-%d %H:%M:%S") if creation_time > 0 else "未知"

        max_heap_mb = round(process_snap.get("maxHeapMemory", 0) / 1024 / 1024, 0)
        used_heap_mb = round(process_snap.get("heapUsageMemory", 0) / 1024 / 1024, 2)
        cpu_usage = round(process_snap.get("cpuUsage", 0) * 100, 2)

        # 组装易读格式
        parsed_info = {
            "服务名称": service_id.get("taskName", "未知"),
            "服务类型": service_id.get("environmentName", "未知"),
            "绑定地址": f"{address.get('host', '未知')}:{address.get('port', '未知')}",
            "创建时间": create_time,
            "运行状态": service.get("lifeCycle", "未知"),
            "PID": str(process_snap.get("pid", "未知")),
            "CPU 使用率": f"{cpu_usage}%",
            "内存使用": f"{used_heap_mb}MB / {max_heap_mb}MB",
            "在线人数": f"{props.get('Online-Count', 0)}/{props.get('Max-Players', 0)}",
            "服务版本": props.get("Version", "未知")
        }
        parsed_result.append(parsed_info)
    return parsed_result