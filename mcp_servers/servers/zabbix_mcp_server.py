#!/usr/bin/env python3
"""
Zabbix Tools MCP Server
基于现有Zabbix工具实现的MCP服务器
"""

import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import os
from fastmcp import FastMCP
from base_config import MCPServerConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("Zabbix Tools Server")

# 加载配置
config = MCPServerConfig('zabbix_monitor')

def _create_zabbix_session():
    """创建新的Zabbix会话，每次调用都重新认证"""
    try:
        session = requests.Session()
        url = config.get("url").rstrip('/')
        
        # 认证获取token
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": config.get("username"),
                "password": config.get("password")
            },
            "id": 1
        }
        
        response = session.post(
            url,
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
        logger.error(f"Zabbix连接失败: {e}")
    
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

@mcp.tool()
async def get_zabbix_metric_data(
    ip: str = None,
    metric_key: str = "system.cpu.util",
    start_time: str = "",
    end_time: str = ""
) -> str:
    """获取指定主机的特定监控指标历史数据。用于查看具体指标的时间序列数据。
    
    Args:
        ip: 主机IP地址
        metric_key: 指标名称，例如：system.cpu.util，如果用户未明确输入key，请先获取指标名在调用
        start_time: 开始时间，格式：YYYY-MM-DD HH:MM:SS
        end_time: 结束时间，格式：YYYY-MM-DD HH:MM:SS
    
    Returns:
        包含指标历史数据的JSON字符串
    """
    try:
        # 解析时间参数
        if not start_time or not end_time:
            # 默认为最近1小时
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(hours=1)
        else:
            try:
                start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return json.dumps({"error": "时间格式错误，请使用 YYYY-MM-DD HH:MM:SS 格式"})
        
        time_from = int(start_dt.timestamp())
        time_till = int(end_dt.timestamp())
        
        # 通过IP地址查找主机
        # 如果配置了 default_host_ip，强制使用它（忽略用户传入的IP）
        config = get_zabbix_config()
        if 'default_host_ip' in config and config['default_host_ip']:
            actual_ip = config['default_host_ip']
        else:
            actual_ip = ip
        host_interface_result = _zabbix_api_call('hostinterface.get', {
            'output': ['hostid'],
            'filter': {'ip': actual_ip}
        })
        
        if "error" in host_interface_result:
            return json.dumps(host_interface_result)
        
        interfaces = host_interface_result.get("result", [])
        if not interfaces:
            return json.dumps({"error": f"No host found with IP {actual_ip}"})
        
        host_id = interfaces[0]["hostid"]
        
        # 获取指定的监控项
        item_params = {
            "output": ["itemid", "name", "key_", "lastvalue", "units"],
            "hostids": host_id,
            "filter": {
                "key_": metric_key
            }
        }
        
        item_result = _zabbix_api_call("item.get", item_params)
        
        if "error" in item_result:
            return json.dumps(item_result)
        
        items = item_result.get("result", [])
        if not items:
            return json.dumps({"error": f"Metric '{metric_key}' not found on host {actual_ip}"})
        
        item = items[0]
        
        # 获取历史数据
        history_params = {
            "output": "extend",
            "itemids": item["itemid"],
            "time_from": time_from,
            "time_till": time_till,
            "sortfield": "clock",
            "sortorder": "ASC"
        }
        
        # 根据数据类型选择history表
        if item["key_"].startswith("system.cpu") or "util" in item["key_"]:
            history_result = _zabbix_api_call("history.get", {**history_params, "history": 0})
        else:
            history_result = _zabbix_api_call("history.get", {**history_params, "history": 3})
        
        if "error" in history_result:
            return json.dumps(history_result)
        
        history_data = history_result.get("result", [])
        
        # 转换数据格式
        formatted_history = []
        values = []
        
        for point in history_data:
            try:
                value = float(point["value"])
                timestamp = datetime.fromtimestamp(int(point["clock"])).strftime("%Y-%m-%d %H:%M:%S")
                formatted_history.append([timestamp, value])
                values.append(value)
            except (ValueError, TypeError):
                continue
        
        # 计算统计数据
        if values:
            avg_value = sum(values) / len(values)
            max_value = max(values)
            min_value = min(values)
        else:
            avg_value = max_value = min_value = 0
        
        metrics_data = {
            item["key_"]: {
                "name": item["name"],
                "current_value": item["lastvalue"],
                "units": item["units"],
                "avg_value": round(avg_value, 2),
                "max_value": round(max_value, 2),
                "min_value": round(min_value, 2),
                "data_points": len(values),
                "history": formatted_history
            }
        }
        
        return json.dumps({
            "hostname": actual_ip,
            "host_id": host_id,
            "metric_key": metric_key,
            "time_range": f"{start_time} to {end_time}",
            "metrics": metrics_data
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting zabbix metric data: {e}")
        return json.dumps({"error": f"Failed to get zabbix metric data: {str(e)}"})

@mcp.tool()
async def get_zabbix_metrics(hostname: str = None) -> str:
    """获取指定主机的所有可用监控指标。用于查看主机支持哪些监控指标。
    
    Args:
        hostname: 主机名
    
    Returns:
        包含可用指标列表的JSON字符串
    """
    try:
        # 通过IP地址查找主机
        # 如果配置了 default_host_ip，强制使用它（忽略用户传入的hostname）
        config = get_zabbix_config()
        if 'default_host_ip' in config and config['default_host_ip']:
            actual_hostname = config['default_host_ip']
        else:
            actual_hostname = hostname
        host_interface_result = _zabbix_api_call('hostinterface.get', {
            'output': ['hostid'],
            'filter': {'ip': actual_hostname}
        })
        
        if "error" in host_interface_result:
            return json.dumps(host_interface_result)
        
        interfaces = host_interface_result.get("result", [])
        if not interfaces:
            return json.dumps({"error": f"No host found with IP {actual_hostname}"})
        
        host_id = interfaces[0]["hostid"]
        
        # 获取主机详细信息
        host_result = _zabbix_api_call("host.get", {
            "output": ["hostid", "host", "name"],
            "hostids": host_id
        })
        
        if "error" in host_result:
            return json.dumps(host_result)
        
        hosts = host_result.get("result", [])
        if not hosts:
            return json.dumps({"error": f"Host details not found for ID {host_id}"})
        
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
            "input_hostname": hostname,
            "actual_hostname": hosts[0]["host"],
            "host_name": hosts[0]["name"],
            "host_id": host_id,
            "total_metrics": total_metrics,
            "metrics_by_category": metrics_by_category
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting zabbix metrics: {e}")
        return json.dumps({"error": f"Failed to get zabbix metrics: {str(e)}"})

if __name__ == "__main__":
    # 获取端口（从环境变量或配置）
    port = int(os.environ.get('MCP_SERVER_PORT', config.port))
    
    logger.info(f"Starting {config.display_name} on port {port}")
    logger.info(f"Zabbix config: url={config.get('url')}, user={config.get('username')}")
    
    # 测试Zabbix连接
    try:
        session, token, url = _create_zabbix_session()
        session.close()
        logger.info("Zabbix连接测试成功")
    except Exception as e:
        logger.warning(f"Zabbix连接测试失败: {e}")
    
    # 使用SSE传输方式启动服务器
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)