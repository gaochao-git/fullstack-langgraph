#!/usr/bin/env python3
"""
MCP服务器配置基类
提供统一的配置加载功能，每个服务器独立使用
"""

import os
import yaml
from typing import Dict, Any, Optional

class MCPServerConfig:
    """MCP服务器配置基类"""
    
    def __init__(self, server_name: str = None):
        """
        初始化配置
        
        Args:
            server_name: 服务器名称，如果不提供则从环境变量获取
        """
        self._server_name = server_name or os.environ.get('MCP_SERVER_NAME', '')
        self._config = None
        self._server_info = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        # 配置文件在 mcp_servers 目录下，需要向上两级
        config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
        
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            all_config = yaml.safe_load(f)
        
        # 获取服务器配置
        servers = all_config.get('servers', {})
        self._server_info = servers.get(self._server_name, {})
        
        # 提取配置部分
        self._config = self._server_info.get('config', {})
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config
    
    @property
    def enabled(self) -> bool:
        """服务是否启用"""
        return self._server_info.get('enabled', True)
    
    
    @property
    def display_name(self) -> str:
        """服务显示名称"""
        return self._server_info.get('display_name', self._server_name)
    
    @property
    def server_name(self) -> str:
        """服务器名称"""
        return self._server_name