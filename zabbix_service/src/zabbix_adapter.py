"""
Zabbix 适配器
将 Zabbix 数据转换为统一的告警格式
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ZabbixAlarmAdapter:
    """Zabbix数据适配器，转换为统一的告警格式"""
    
    def to_alarm_format(self, problem: Dict[str, Any]) -> Dict[str, Any]:
        """
        将Zabbix问题数据转换为统一的告警格式
        
        Args:
            problem: Zabbix问题数据
            
        Returns:
            统一格式的告警数据
        """
        # 提取标签信息
        tags = problem.get("tags", [])
        team_tag = None
        idc_tag = None
        level_tag = None
        
        for tag in tags:
            if tag.get("tag") == "team_tag":
                team_tag = tag.get("value")
            elif tag.get("tag") == "idc_tag":
                idc_tag = tag.get("value")
            elif tag.get("tag") == "level_tag":
                level_tag = tag.get("value")
        
        # 构建统一格式
        alarm = {
            "alarm_id": problem.get("eventid", ""),
            "alarm_source": "Zabbix",
            "alarm_key": problem.get("item_key", ""),
            "alarm_name": problem.get("name", ""),
            "alarm_desc": problem.get("description", problem.get("trigger_description", "")),
            "alarm_level": level_tag or problem.get("severity_name", str(problem.get("severity", ""))),
            "alarm_time": problem.get("timestamp", ""),
            "alarm_ip": problem.get("host_ip", ""),
            "team_tag": team_tag,
            "idc_tag": idc_tag,
            # 保留原始数据以便调试
            "_raw": problem
        }
        
        return alarm