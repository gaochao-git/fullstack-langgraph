#!/usr/bin/env python3
"""
MCP服务器统一配置文件 - 支持新旧两种格式
"""

import os
import sys
import yaml
from typing import Dict, List, Any, Optional

# 缓存配置
_CONFIG: Optional[Dict[str, Any]] = None
_CONFIG_FORMAT: Optional[str] = None  # 'old' or 'new'

def load_config(verbose=True) -> Dict[str, Any]:
    """
    从配置文件加载配置，自动识别新旧格式
    
    Args:
        verbose: 是否打印详细信息
    
    Returns:
        Dict: 配置字典（始终返回旧格式以保持兼容）
    """
    global _CONFIG, _CONFIG_FORMAT
    
    if _CONFIG is not None:
        return _CONFIG
    
    config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    if not os.path.exists(config_file):
        print(f"❌ 错误：配置文件不存在: {config_file}")
        sys.exit(1)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
            
            if verbose:
                print(f"✅ 成功加载配置文件: {config_file}")
            
            # 检测配置格式
            if 'servers' in raw_config and isinstance(raw_config['servers'], dict):
                # 新格式：servers 下是服务器配置
                _CONFIG_FORMAT = 'new'
                _CONFIG = convert_new_to_old_format(raw_config)
                if verbose:
                    print("📋 检测到新配置格式")
            else:
                # 旧格式：services 下是 enabled/disabled
                _CONFIG_FORMAT = 'old'
                _CONFIG = raw_config
                if verbose:
                    print("📋 检测到旧配置格式")
            
            # 显示启用的服务
            if verbose:
                enabled_services = [name for name, enabled in _CONFIG.get('services', {}).items() if enabled]
                print(f"📋 启用的服务: {', '.join(enabled_services)}")
            
            return _CONFIG
            
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        sys.exit(1)

def convert_new_to_old_format(new_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    将新格式配置转换为旧格式
    
    新格式:
    servers:
      db_query:
        enabled: true
        port: 3001
        config:
          host: xxx
          
    旧格式:
    services:
      mysql: true
    mysql:
      host: xxx
    """
    old_config = {
        'services': {}
    }
    
    # 服务名映射
    service_name_map = {
        'db_query': 'mysql',
        'ssh_exec': 'ssh',
        'es_search': 'elasticsearch',
        'zabbix_monitor': 'zabbix',
        'sop_server': 'sop'
    }
    
    servers = new_config.get('servers', {})
    
    for server_id, server_config in servers.items():
        # 获取对应的服务名
        service_name = service_name_map.get(server_id, server_id)
        
        # 设置服务启用状态
        old_config['services'][service_name] = server_config.get('enabled', True)
        
        # 复制服务配置
        if 'config' in server_config:
            old_config[service_name] = server_config['config']
    
    return old_config

def get_config() -> Dict[str, Any]:
    """获取完整配置（兼容旧代码）"""
    global _CONFIG
    if _CONFIG is None:
        load_config(verbose=False)
    return _CONFIG

def is_service_enabled(service_name: str) -> bool:
    """检查服务是否启用"""
    if _CONFIG is None:
        load_config(verbose=False)
    return _CONFIG.get('services', {}).get(service_name, True)

def get_enabled_services() -> List[str]:
    """获取所有启用的服务列表"""
    return [name for name, enabled in _CONFIG.get('services', {}).items() if enabled]

def get_mysql_config() -> Dict[str, Any]:
    """获取MySQL配置"""
    if not is_service_enabled('mysql'):
        raise RuntimeError("MySQL服务未启用")
    return get_config()['mysql']

def get_ssh_config() -> Dict[str, Any]:
    """获取SSH配置"""
    if not is_service_enabled('ssh'):
        raise RuntimeError("SSH服务未启用")
    return get_config()['ssh']

def get_es_config() -> Dict[str, Any]:
    """获取Elasticsearch配置"""
    if not is_service_enabled('elasticsearch'):
        raise RuntimeError("Elasticsearch服务未启用")
    return get_config()['elasticsearch']

def get_zabbix_config() -> Dict[str, Any]:
    """获取Zabbix配置"""
    if not is_service_enabled('zabbix'):
        raise RuntimeError("Zabbix服务未启用")
    return get_config()['zabbix']

def get_sop_config() -> Dict[str, Any]:
    """获取SOP配置"""
    if not is_service_enabled('sop'):
        raise RuntimeError("SOP服务未启用")
    return get_config()['sop']

# 从环境变量获取服务器信息（用于新的manage.py）
def get_current_server_config() -> Optional[Dict[str, Any]]:
    """
    获取当前服务器的配置（通过环境变量）
    由 manage.py 设置的环境变量：
    - MCP_SERVER_NAME: 服务器名称
    - MCP_SERVER_PORT: 服务器端口
    """
    server_name = os.environ.get('MCP_SERVER_NAME')
    if not server_name:
        return None
    
    # 如果是新格式，直接返回对应的配置
    if _CONFIG_FORMAT == 'new':
        raw_config = load_raw_config()
        servers = raw_config.get('servers', {})
        if server_name in servers:
            return servers[server_name].get('config', {})
    
    return None

def load_raw_config() -> Dict[str, Any]:
    """加载原始配置（不转换格式）"""
    config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# 初始化配置
MCP_ENV = os.environ.get('MCP_ENV', 'production')

# 打印当前配置信息（调试用）
if __name__ == "__main__":
    import json
    print(f"当前环境: {MCP_ENV}")
    config = load_config(verbose=True)
    print(f"配置内容（转换后）: {json.dumps(config, indent=2, ensure_ascii=False)}")
    
    # 如果设置了服务器名称，显示当前服务器配置
    if os.environ.get('MCP_SERVER_NAME'):
        print(f"\n当前服务器: {os.environ.get('MCP_SERVER_NAME')}")
        server_config = get_current_server_config()
        if server_config:
            print(f"服务器配置: {json.dumps(server_config, indent=2, ensure_ascii=False)}")