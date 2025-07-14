"""
Zabbix工具 - 使用LangChain工具框架
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from langchain.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

def _create_zabbix_session():
    """创建新的Zabbix会话，每次调用都重新认证"""
    # 默认配置，按优先级排序
    default_configs = [
        {"url": "http://82.156.146.51/zabbix", "username": "Admin", "password": "zabbix"},
        {"url": "http://82.156.146.51/zabbix", "username": "admin", "password": "zabbix"},
        {"url": "http://82.156.146.51:8080/zabbix", "username": "Admin", "password": "zabbix"}
    ]
    
    for config in default_configs:
        try:
            session = requests.Session()
            url = config["url"].rstrip('/')
            
            # 认证获取token
            payload = {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": config["username"],
                    "password": config["password"]
                },
                "id": 1
            }
            
            response = session.post(
                f"{url}/api_jsonrpc.php",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    auth_token = result["result"]
                    logger.info(f"Zabbix连接成功，URL: {url}")
                    return {"session": session, "url": url, "auth_token": auth_token}
                
        except Exception as e:
            logger.debug(f"尝试配置 {config['url']} 失败: {e}")
            continue
    
    raise Exception("无法建立Zabbix连接，请检查Zabbix服务状态和配置")

def _zabbix_api_call(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """执行Zabbix API调用，每次都创建新连接"""
    try:
        zabbix_config = _create_zabbix_session()
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "auth": zabbix_config["auth_token"],
            "id": 1
        }
        
        response = zabbix_config["session"].post(
            f"{zabbix_config['url']}/api_jsonrpc.php",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP error: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Error in Zabbix API call: {e}")
        return {"error": f"API call failed: {str(e)}"}

class ActiveAlertsInput(BaseModel):
    """活跃告警查询输入参数"""
    severity_min: int = Field(default=2, description="最小严重程度(0-5)")
    time_range_hours: int = Field(default=24, description="时间范围(小时)")

@tool("get_active_alerts", args_schema=ActiveAlertsInput)
def get_active_alerts(
    severity_min: int = 2,
    time_range_hours: int = 24
) -> str:
    """获取Zabbix活跃告警。用于查看当前系统中的活跃告警信息。
    
    Args:
        severity_min: 最小严重程度，0-5，默认2(Warning)
        time_range_hours: 时间范围(小时)，默认24小时
    
    Returns:
        包含活跃告警的JSON字符串
    """
    # 连接检查已移至_zabbix_api_call中自动处理
    
    try:
        # 获取触发器
        time_from = int((datetime.now() - timedelta(hours=time_range_hours)).timestamp())
        
        params = {
            "output": ["triggerid", "description", "status", "priority", "lastchange"],
            "filter": {
                "status": 0  # 启用的触发器
            },
            "min_severity": severity_min,
            "sortfield": "priority",
            "sortorder": "DESC",
            "expandDescription": True,
            "expandData": True,
            "expandComment": True
        }
        
        result = _zabbix_api_call("trigger.get", params)
        
        if "error" in result:
            return json.dumps(result)
        
        triggers = result.get("result", [])
        
        # 获取每个触发器的主机信息
        alert_data = []
        for trigger in triggers:
            # 获取主机信息
            host_params = {
                "output": ["hostid", "host", "name"],
                "triggerids": trigger["triggerid"]
            }
            
            host_result = _zabbix_api_call("host.get", host_params)
            hosts = host_result.get("result", [])
            
            # 获取最新事件
            event_params = {
                "output": ["eventid", "clock", "value", "acknowledged"],
                "triggerids": trigger["triggerid"],
                "sortfield": "clock",
                "sortorder": "DESC",
                "limit": 1
            }
            
            event_result = _zabbix_api_call("event.get", event_params)
            events = event_result.get("result", [])
            
            severity_map = {
                "0": "Not classified",
                "1": "Information", 
                "2": "Warning",
                "3": "Average",
                "4": "High",
                "5": "Disaster"
            }
            
            for host in hosts:
                alert_data.append({
                    "trigger_id": trigger["triggerid"],
                    "description": trigger["description"],
                    "severity": severity_map.get(trigger["priority"], "Unknown"),
                    "severity_level": int(trigger["priority"]),
                    "host": host["host"],
                    "host_name": host["name"],
                    "status": "PROBLEM" if trigger["status"] == "0" else "OK",
                    "last_change": datetime.fromtimestamp(int(trigger["lastchange"])).isoformat(),
                    "acknowledged": events[0]["acknowledged"] == "1" if events else False,
                    "event_id": events[0]["eventid"] if events else None
                })
        
        # 按严重程度排序
        alert_data.sort(key=lambda x: x["severity_level"], reverse=True)
        
        return json.dumps({
            "total_alerts": len(alert_data),
            "alerts": alert_data,
            "time_range": f"Last {time_range_hours} hours"
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting active alerts: {e}")
        return json.dumps({"error": f"Failed to get active alerts: {str(e)}"})

class HostMetricsInput(BaseModel):
    """主机监控指标输入参数"""
    hostname: str = Field(description="主机名")
    metrics: Optional[List[str]] = Field(default=None, description="指标列表")
    time_range_hours: int = Field(default=1, description="时间范围(小时)")

@tool("get_host_metrics", args_schema=HostMetricsInput)
def get_host_metrics(
    hostname: str,
    metrics: Optional[List[str]] = None,
    time_range_hours: int = 1
) -> str:
    """获取主机监控指标。用于查看特定主机的性能指标数据。
    
    Args:
        hostname: 主机名
        metrics: 指标列表，默认为CPU、内存、磁盘使用率
        time_range_hours: 时间范围(小时)
    
    Returns:
        包含主机监控指标的JSON字符串
    """
    # 连接检查已移至_zabbix_api_call中自动处理
    
    if not metrics:
        metrics = [
            "system.cpu.util",
            "vm.memory.util",
            "vfs.fs.size[/,pused]",
            "system.cpu.load[percpu,avg1]"
        ]
    
    try:
        # 获取主机ID
        host_params = {
            "output": ["hostid", "host", "name"],
            "filter": {
                "host": hostname
            }
        }
        
        host_result = _zabbix_api_call("host.get", host_params)
        
        if "error" in host_result:
            return json.dumps(host_result)
        
        hosts = host_result.get("result", [])
        if not hosts:
            return json.dumps({"error": f"Host {hostname} not found"})
        
        host_id = hosts[0]["hostid"]
        
        # 获取监控项
        item_params = {
            "output": ["itemid", "name", "key_", "lastvalue", "units"],
            "hostids": host_id,
            "search": {
                "key_": metrics
            },
            "searchByAny": True
        }
        
        item_result = _zabbix_api_call("item.get", item_params)
        
        if "error" in item_result:
            return json.dumps(item_result)
        
        items = item_result.get("result", [])
        
        # 获取历史数据
        time_from = int((datetime.now() - timedelta(hours=time_range_hours)).timestamp())
        time_till = int(datetime.now().timestamp())
        
        metrics_data = {}
        
        for item in items:
            # 获取历史数据
            history_params = {
                "output": "extend",
                "itemids": item["itemid"],
                "time_from": time_from,
                "time_till": time_till,
                "sortfield": "clock",
                "sortorder": "DESC",
                "limit": 100
            }
            
            # 根据数据类型选择history表
            if item["key_"].startswith("system.cpu") or "util" in item["key_"]:
                history_result = _zabbix_api_call("history.get", {**history_params, "history": 0})
            else:
                history_result = _zabbix_api_call("history.get", {**history_params, "history": 3})
            
            if "result" in history_result:
                history_data = history_result["result"]
                
                # 转换时间戳并计算统计
                values = []
                timestamps = []
                
                for point in history_data:
                    try:
                        value = float(point["value"])
                        values.append(value)
                        timestamps.append(datetime.fromtimestamp(int(point["clock"])).isoformat())
                    except (ValueError, TypeError):
                        continue
                
                if values:
                    avg_value = sum(values) / len(values)
                    max_value = max(values)
                    min_value = min(values)
                else:
                    avg_value = max_value = min_value = 0
                
                metrics_data[item["key_"]] = {
                    "name": item["name"],
                    "current_value": item["lastvalue"],
                    "units": item["units"],
                    "avg_value": round(avg_value, 2),
                    "max_value": round(max_value, 2),
                    "min_value": round(min_value, 2),
                    "data_points": len(values),
                    "history": list(zip(timestamps, values))[-20:]  # 最近20个点
                }
        
        return json.dumps({
            "hostname": hostname,
            "host_id": host_id,
            "time_range": f"Last {time_range_hours} hour(s)",
            "metrics": metrics_data
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting host metrics: {e}")
        return json.dumps({"error": f"Failed to get host metrics: {str(e)}"})

class ProblemEventsInput(BaseModel):
    """问题事件查询输入参数"""
    time_range_hours: int = Field(default=24, description="时间范围(小时)")
    severity_min: int = Field(default=2, description="最小严重程度(0-5)")

@tool("get_problem_events", args_schema=ProblemEventsInput)
def get_problem_events(
    time_range_hours: int = 24,
    severity_min: int = 2
) -> str:
    """获取问题事件。用于查看系统中发生的问题事件历史。
    
    Args:
        time_range_hours: 时间范围(小时)
        severity_min: 最小严重程度(0-5)
    
    Returns:
        包含问题事件的JSON字符串
    """
    # 连接检查已移至_zabbix_api_call中自动处理
    
    try:
        time_from = int((datetime.now() - timedelta(hours=time_range_hours)).timestamp())
        
        params = {
            "output": ["eventid", "source", "object", "objectid", "clock", "value", "acknowledged", "severity"],
            "source": 0,  # 触发器事件
            "object": 0,  # 触发器对象
            "value": 1,   # 问题事件
            "time_from": time_from,
            "sortfield": "clock",
            "sortorder": "DESC",
            "selectTags": "extend"
        }
        
        result = _zabbix_api_call("event.get", params)
        
        if "error" in result:
            return json.dumps(result)
        
        events = result.get("result", [])
        
        # 获取触发器和主机详细信息
        event_data = []
        
        for event in events:
            trigger_params = {
                "output": ["triggerid", "description", "priority"],
                "triggerids": event["objectid"]
            }
            
            trigger_result = _zabbix_api_call("trigger.get", trigger_params)
            
            if "result" in trigger_result and trigger_result["result"]:
                trigger = trigger_result["result"][0]
                
                # 获取主机信息
                host_params = {
                    "output": ["hostid", "host", "name"],
                    "triggerids": trigger["triggerid"]
                }
                
                host_result = _zabbix_api_call("host.get", host_params)
                
                if "result" in host_result and host_result["result"]:
                    host = host_result["result"][0]
                    
                    severity_map = {
                        "0": "Not classified",
                        "1": "Information",
                        "2": "Warning", 
                        "3": "Average",
                        "4": "High",
                        "5": "Disaster"
                    }
                    
                    event_data.append({
                        "event_id": event["eventid"],
                        "timestamp": datetime.fromtimestamp(int(event["clock"])).isoformat(),
                        "description": trigger["description"],
                        "severity": severity_map.get(trigger["priority"], "Unknown"),
                        "severity_level": int(trigger["priority"]),
                        "host": host["host"],
                        "host_name": host["name"],
                        "acknowledged": event["acknowledged"] == "1",
                        "tags": event.get("tags", [])
                    })
        
        # 过滤严重程度并排序
        filtered_events = [e for e in event_data if e["severity_level"] >= severity_min]
        filtered_events.sort(key=lambda x: (x["severity_level"], x["timestamp"]), reverse=True)
        
        return json.dumps({
            "total_events": len(filtered_events),
            "events": filtered_events,
            "time_range": f"Last {time_range_hours} hours",
            "severity_filter": f"Minimum severity: {severity_min}"
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting problem events: {e}")
        return json.dumps({"error": f"Failed to get problem events: {str(e)}"})

class HostAvailabilityInput(BaseModel):
    """主机可用性查询输入参数"""
    hostnames: Optional[List[str]] = Field(default=None, description="主机名列表")

@tool("get_host_availability", args_schema=HostAvailabilityInput)
def get_host_availability(hostnames: Optional[List[str]] = None) -> str:
    """获取主机可用性状态。用于检查主机的连接状态和可用性。
    
    Args:
        hostnames: 主机名列表，None表示检查所有主机
    
    Returns:
        包含主机可用性状态的JSON字符串
    """
    # 连接检查已移至_zabbix_api_call中自动处理
    
    try:
        params = {
            "output": ["hostid", "host", "name", "available", "error", "errors_from"],
            "selectInterfaces": ["ip", "port", "type", "available"]
        }
        
        if hostnames:
            params["filter"] = {"host": hostnames}
        
        result = _zabbix_api_call("host.get", params)
        
        if "error" in result:
            return json.dumps(result)
        
        hosts = result.get("result", [])
        
        availability_data = []
        
        for host in hosts:
            status_map = {
                "0": "Unknown",
                "1": "Available", 
                "2": "Unavailable"
            }
            
            interface_status = []
            for interface in host.get("interfaces", []):
                interface_type_map = {
                    "1": "Zabbix Agent",
                    "2": "SNMP",
                    "3": "IPMI",
                    "4": "JMX"
                }
                
                interface_status.append({
                    "type": interface_type_map.get(interface["type"], "Unknown"),
                    "ip": interface["ip"],
                    "port": interface["port"], 
                    "status": status_map.get(interface["available"], "Unknown")
                })
            
            availability_data.append({
                "host": host["host"],
                "host_name": host["name"],
                "status": status_map.get(host["available"], "Unknown"),
                "error": host.get("error", ""),
                "errors_from": datetime.fromtimestamp(int(host["errors_from"])).isoformat() if host.get("errors_from") else None,
                "interfaces": interface_status
            })
        
        return json.dumps({
            "total_hosts": len(availability_data),
            "hosts": availability_data
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting host availability: {e}")
        return json.dumps({"error": f"Failed to get host availability: {str(e)}"})

# 重命名工具以匹配SOP配置
get_zabbix_metric_data = get_host_metrics

class HostMetricsListInput(BaseModel):
    """获取主机可用指标输入参数"""
    hostname: str = Field(description="主机名")

@tool("get_zabbix_metrics", args_schema=HostMetricsListInput)
def get_zabbix_metrics(hostname: str) -> str:
    """获取指定主机的所有可用监控指标。用于查看主机支持哪些监控指标。
    
    Args:
        hostname: 主机名
    
    Returns:
        包含可用指标列表的JSON字符串
    """
    try:
        # 获取主机ID
        host_params = {
            "output": ["hostid", "host", "name"],
            "filter": {
                "host": hostname
            }
        }
        
        host_result = _zabbix_api_call("host.get", host_params)
        
        if "error" in host_result:
            return json.dumps(host_result)
        
        hosts = host_result.get("result", [])
        if not hosts:
            return json.dumps({"error": f"Host {hostname} not found"})
        
        host_id = hosts[0]["hostid"]
        
        # 获取所有监控项
        item_params = {
            "output": ["itemid", "name", "key_", "units", "description", "status"],
            "hostids": host_id,
            "filter": {
                "status": 0  # 启用的监控项
            }
        }
        
        item_result = _zabbix_api_call("item.get", item_params)
        
        if "error" in item_result:
            return json.dumps(item_result)
        
        items = item_result.get("result", [])
        
        # 按类别分组指标
        metrics_by_category = {}
        
        for item in items:
            key = item["key_"]
            
            # 根据key确定类别
            if key.startswith("system.cpu"):
                category = "CPU"
            elif key.startswith("vm.memory") or key.startswith("memory"):
                category = "Memory"
            elif key.startswith("vfs.fs") or key.startswith("disk"):
                category = "Disk"
            elif key.startswith("net.if") or key.startswith("network"):
                category = "Network"
            elif key.startswith("system."):
                category = "System"
            else:
                category = "Other"
            
            if category not in metrics_by_category:
                metrics_by_category[category] = []
            
            metrics_by_category[category].append({
                "key": key,
                "name": item["name"],
                "units": item["units"],
                "description": item.get("description", "")
            })
        
        # 计算总数
        total_metrics = sum(len(metrics) for metrics in metrics_by_category.values())
        
        return json.dumps({
            "hostname": hostname,
            "host_id": host_id,
            "total_metrics": total_metrics,
            "metrics_by_category": metrics_by_category
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting zabbix metrics: {e}")
        return json.dumps({"error": f"Failed to get zabbix metrics: {str(e)}"})

# 导出所有工具
zabbix_tools = [
    get_zabbix_metric_data,
    get_zabbix_metrics
] 