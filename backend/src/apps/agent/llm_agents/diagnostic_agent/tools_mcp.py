"""
MCP工具整合模块
负责合并系统工具和MCP工具，避免重复
"""

import asyncio
import logging
from typing import List
from langchain_mcp_adapters.client import MultiServerMCPClient
from .....shared.tools import sop_tool, general_tool

logger = logging.getLogger(__name__)

class MCPToolsIntegrator:
    """MCP工具整合器"""
    
    def __init__(self):
        self.server_config = {
            "database": {"url": "http://localhost:3001/sse", "transport": "sse"},
            "ssh": {"url": "http://localhost:3002/sse", "transport": "sse"},
            "elasticsearch": {"url": "http://localhost:3003/sse", "transport": "sse"},
            "zabbix": {"url": "http://localhost:3004/sse", "transport": "sse"}
        }
    
    async def get_mcp_tools(self):
        """获取MCP工具 - 按照官方推荐的简单方式"""
        try:
            # 官方推荐的简单用法
            client = MultiServerMCPClient(self.server_config)
            all_mcp_tools = await client.get_tools()
            
            # 过滤工具 - 可以根据需要排除某些工具
            filtered_tools = self._filter_tools(all_mcp_tools)
            
            logger.info(f"✅ 成功获取 {len(all_mcp_tools)} 个MCP工具，过滤后 {len(filtered_tools)} 个")
            return filtered_tools
            
        except Exception as e:
            logger.warning(f"⚠️  获取MCP工具失败: {e}，将只使用系统工具")
            return []
    
    def _filter_tools(self, tools):
        """过滤MCP工具"""
        excluded_tools = ['execute_system_command']
        return [tool for tool in tools if tool.name not in excluded_tools]
    
    def get_system_tools(self, enable_approval: bool = False):
        """获取指定的系统工具：SOP相关 + 时间工具"""
        system_tools = [
            # SOP相关工具
            sop_tool.get_sop_content,
            sop_tool.get_sop_detail,
            sop_tool.list_sops,
            sop_tool.search_sops,
            # 时间工具
            general_tool.get_current_time
        ]
        
        # 如果启用审批，应用到系统工具（MCP工具暂不支持审批）
        if enable_approval:
            # TODO: 如果需要对系统工具应用审批，在这里实现
            pass
        
        return system_tools
    
    async def get_combined_tools(self, enable_approval: bool = False):
        """获取合并后的工具列表（系统工具：SOP+时间，MCP工具：SSH+MySQL+ES+Zabbix）"""
        # 获取MCP工具
        mcp_tools = await self.get_mcp_tools()
        
        # 获取系统工具
        system_tools = self.get_system_tools(enable_approval)
        
        # 合并工具
        combined_tools = list(system_tools) + list(mcp_tools)
        return combined_tools

# 全局实例
mcp_integrator = MCPToolsIntegrator()

async def get_diagnostic_tools(enable_approval: bool = False):
    """获取诊断工具列表"""
    return await mcp_integrator.get_combined_tools(enable_approval)