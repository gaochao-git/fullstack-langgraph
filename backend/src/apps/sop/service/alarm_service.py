"""
报警服务
直接调用配置的报警接口获取数据
"""
import httpx
from typing import List, Dict, Any, Optional
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException, ResponseCode
from src.shared.core.config import settings

logger = get_logger(__name__)


class AlarmService:
    """报警服务 - 调用外部报警系统接口"""
    
    def __init__(self):
        # 从配置获取报警接口地址
        self.alarm_url = getattr(settings, 'ALARM_API_URL', None)
        if not self.alarm_url:
            raise BusinessException(
                "未配置报警接口地址，请在.env中设置ALARM_API_URL",
                ResponseCode.INTERNAL_ERROR
            )
        self.timeout = 30.0
    
    async def get_alarms(
        self,
        alarm_level: Optional[List[str]] = None,
        alarm_time: Optional[str] = None,
        team_tag: Optional[List[str]] = None,
        idc_tag: Optional[List[str]] = None,
        alarm_ip: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """
        获取报警数据
        
        要求外部接口返回的数据格式：
        [
            {
                "alarm_id": "事件ID",
                "alarm_source": "数据源",
                "alarm_key": "监控指标key",
                "alarm_name": "报警名称",
                "alarm_desc": "报警描述",
                "alarm_level": "严重级别",
                "alarm_time": "时间",
                "alarm_ip": "主机IP",
                "team_tag": "团队tag",
                "idc_tag": "机房tag"
            }
        ]
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                # 构建请求参数
                params = {
                    'page': page,
                    'page_size': page_size,
                    **kwargs
                }
                
                # 添加过滤参数
                if alarm_level:
                    params['alarm_level'] = alarm_level
                if alarm_time:
                    params['alarm_time'] = alarm_time
                if team_tag:
                    params['team_tag'] = team_tag
                if idc_tag:
                    params['idc_tag'] = idc_tag
                if alarm_ip:
                    params['alarm_ip'] = alarm_ip
                
                # 调用外部报警接口
                response = await client.get(self.alarm_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # 如果返回的是包装格式，提取数据
                if isinstance(data, dict) and 'data' in data:
                    alerts = data['data']
                else:
                    alerts = data
                
                # 返回完整的分页数据
                if isinstance(data, dict) and 'data' in data:
                    # 已经是期望的分页格式
                    logger.info(f"Retrieved {data.get('total', 0)} total alarms, page {data.get('page', 1)}")
                    return data
                elif isinstance(data, list):
                    # 兼容旧格式：如果返回的是数组，适配后包装成分页格式
                    alerts = data
                    logger.info(f"Retrieved {len(alerts)} alarms (legacy format)")
                    
                    # 适配旧格式到新格式
                    normalized_alerts = []
                    for alert in alerts:
                        if 'alarm_id' in alert:
                            normalized_alerts.append(alert)
                        elif 'event_id' in alert:
                            # Zabbix格式转换
                            normalized = {
                                'alarm_id': alert.get('event_id'),
                                'alarm_source': 'Zabbix',
                                'alarm_key': alert.get('metric_key', alert.get('item_key', '')),
                                'alarm_name': alert.get('name', ''),
                                'alarm_desc': alert.get('description', alert.get('trigger_description', '')),
                                'alarm_level': alert.get('severity_name', str(alert.get('severity', ''))),
                                'alarm_time': alert.get('timestamp', ''),
                                'alarm_ip': alert.get('host_ip', ''),
                                'team_tag': None,
                                'idc_tag': None
                            }
                            
                            if 'tags' in alert and isinstance(alert['tags'], list):
                                for tag in alert['tags']:
                                    if tag.get('tag') == 'team_tag':
                                        normalized['team_tag'] = tag.get('value')
                                    elif tag.get('tag') == 'idc_tag':
                                        normalized['idc_tag'] = tag.get('value')
                            
                            normalized_alerts.append(normalized)
                        else:
                            normalized_alerts.append(alert)
                    
                    # 包装成分页格式
                    return {
                        'total': len(normalized_alerts),
                        'page': 1,
                        'page_size': len(normalized_alerts),
                        'data': normalized_alerts
                    }
                else:
                    # 其他情况
                    logger.warning(f"Unexpected response format from alarm API: {type(data)}")
                    return data
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error calling alarm API: {e}")
                raise BusinessException(
                    f"调用报警接口失败: {str(e)}",
                    ResponseCode.BAD_GATEWAY
                )
            except Exception as e:
                logger.error(f"Unexpected error calling alarm API: {e}")
                raise BusinessException(
                    f"报警服务异常: {str(e)}",
                    ResponseCode.INTERNAL_ERROR
                )


# 创建全局实例
alarm_service = AlarmService()