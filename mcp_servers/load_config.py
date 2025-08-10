#!/usr/bin/env python3
"""
MCP服务器统一配置文件
必须使用 config.yaml 配置文件
"""

import os
import sys
import yaml
from typing import Dict, List, Any

def load_config(verbose=True) -> Dict[str, Any]:
    """
    从配置文件加载配置，配置文件必须存在
    
    Args:
        verbose: 是否打印详细信息
    
    Returns:
        Dict: 配置字典
    
    Raises:
        SystemExit: 如果配置文件不存在或加载失败
    """
    config_file = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    if not os.path.exists(config_file):
        print(f"❌ 错误：配置文件不存在: {config_file}")
        print(f"📝 请执行以下命令创建配置文件：")
        print(f"   cd {os.path.dirname(__file__)}")
        print(f"   cp config.yaml.template config.yaml")
        print(f"   vim config.yaml  # 编辑配置文件")
        sys.exit(1)
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
            if verbose:
                print(f"✅ 成功加载配置文件: {config_file}")
            
            # 检查是否有服务配置
            if 'services' not in config:
                if verbose:
                    print(f"⚠️  警告：配置文件缺少 services 配置，默认启用所有服务")
                config['services'] = {
                    'mysql': True,
                    'ssh': True,
                    'elasticsearch': True,
                    'zabbix': True
                }
            
            # 显示启用的服务
            if verbose:
                enabled_services = [name for name, enabled in config.get('services', {}).items() if enabled]
                print(f"📋 启用的服务: {', '.join(enabled_services)}")
            
            # 只验证启用的服务的配置
            enabled_services = [name for name, enabled in config.get('services', {}).items() if enabled]
            for service in enabled_services:
                if service not in config:
                    print(f"❌ 错误：服务 {service} 已启用但缺少配置")
                    sys.exit(1)
            
            return config
    except yaml.YAMLError as e:
        print(f"❌ 错误：配置文件格式错误: {e}")
        print(f"📝 请检查 YAML 格式是否正确")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误：加载配置文件失败: {e}")
        sys.exit(1)

# 加载配置（只在模块导入时打印一次）
# 检查是否是主进程还是子进程
_is_main_process = os.environ.get('MCP_CONFIG_LOADED') != '1'
if _is_main_process:
    os.environ['MCP_CONFIG_LOADED'] = '1'
    
_CONFIG = load_config(verbose=_is_main_process)

def get_config() -> Dict[str, Any]:
    """
    获取配置
    
    Returns:
        Dict: 配置字典
    """
    return _CONFIG

def is_service_enabled(service_name: str) -> bool:
    """
    检查服务是否启用
    
    Args:
        service_name: 服务名称 (mysql, ssh, elasticsearch, zabbix)
    
    Returns:
        bool: 服务是否启用
    """
    return _CONFIG.get('services', {}).get(service_name, True)

def get_enabled_services() -> List[str]:
    """
    获取所有启用的服务列表
    
    Returns:
        List[str]: 启用的服务名称列表
    """
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

# 打印当前配置信息（调试用）
if __name__ == "__main__":
    import json
    print(f"当前环境: {MCP_ENV}")
    print(f"配置内容: {json.dumps(get_config(), indent=2, ensure_ascii=False)}")