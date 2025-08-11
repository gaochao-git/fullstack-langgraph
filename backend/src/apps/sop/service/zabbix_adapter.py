"""
Zabbix 适配器
将 Zabbix 数据转换为通用监控格式，然后传给监控服务
"""
from typing import List, Dict, Any, Optional
from src.apps.sop.service.zabbix_service import get_zabbix_service
from src.shared.core.logging import get_logger
from src.shared.core.config import settings
import httpx

logger = get_logger(__name__)


async def setup_zabbix_monitoring_adapter():
    """
    设置 Zabbix 作为监控数据源
    这个函数应该在一个独立的服务中运行，定期将 Zabbix 数据推送到监控服务
    """
    # 这里是一个示例，实际使用时应该作为独立服务运行
    pass


async def convert_zabbix_to_monitoring_format(zabbix_problems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    将 Zabbix 问题数据转换为通用监控格式
    """
    monitoring_alerts = []
    
    for problem in zabbix_problems:
        alert = {
            "event_id": problem.get('eventid', ''),
            "name": problem.get('name', ''),
            "description": problem.get('trigger_description', ''),
            "severity": problem.get('severity', '0'),
            "severity_name": problem.get('severity_name', ''),
            "timestamp": problem.get('clock', ''),
            "hostname": problem.get('hostname', ''),
            "host_ip": problem.get('host_ip', ''),
            "metric_key": problem.get('item_key', ''),
            "metric_value": problem.get('last_value', ''),
            "metric_unit": problem.get('units', ''),
            "tags": problem.get('tags', [])
        }
        monitoring_alerts.append(alert)
    
    return monitoring_alerts


# 如果需要，可以创建一个定时任务将 Zabbix 数据推送到监控服务
async def push_zabbix_to_monitoring_service():
    """
    将 Zabbix 数据推送到通用监控服务
    """
    try:
        # 获取 Zabbix 数据
        zabbix_service = get_zabbix_service()
        async with zabbix_service:
            problems = await zabbix_service.get_problems(
                severity_min=0,
                recent_only=True,
                limit=1000
            )
        
        # 转换格式
        monitoring_alerts = await convert_zabbix_to_monitoring_format(problems)
        
        # 推送到监控服务（如果监控服务支持推送）
        monitoring_api_url = getattr(settings, 'MONITORING_PUSH_URL', None)
        if monitoring_api_url:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    monitoring_api_url,
                    json=monitoring_alerts
                )
                response.raise_for_status()
                logger.info(f"Successfully pushed {len(monitoring_alerts)} alerts to monitoring service")
                
    except Exception as e:
        logger.error(f"Failed to push Zabbix data to monitoring service: {e}")