#!/usr/bin/env python3
"""
详细的MCP客户端测试脚本
使用FastMCP客户端全面测试所有MCP服务器
"""

import asyncio
import json
import time
from fastmcp import Client
from typing import Dict, List, Any


class MCPTester:
    def __init__(self):
        self.servers = [
            {
                "name": "数据库工具服务器", 
                "url": "http://localhost:3001/sse/",
                "port": 3001,
                "expected_tools": ["execute_mysql_query"]
            },
            {
                "name": "SSH工具服务器", 
                "url": "http://localhost:3002/sse/",
                "port": 3002,
                "expected_tools": ["get_system_info", "analyze_processes", "check_service_status", "analyze_system_logs", "execute_system_command"]
            },
            {
                "name": "Elasticsearch工具服务器", 
                "url": "http://localhost:3003/sse/",
                "port": 3003,
                "expected_tools": ["get_es_data", "get_es_trends_data", "get_es_indices"]
            },
            {
                "name": "Zabbix工具服务器", 
                "url": "http://localhost:3004/sse/",
                "port": 3004,
                "expected_tools": ["get_zabbix_metric_data", "get_zabbix_metrics"]
            }
        ]
        
    async def test_server_connection(self, server_info: Dict) -> Dict[str, Any]:
        """测试服务器连接和工具发现"""
        print(f"\n{'='*60}")
        print(f"🔍 测试 {server_info['name']}")
        print(f"📡 URL: {server_info['url']}")
        print(f"🚪 端口: {server_info['port']}")
        print(f"{'='*60}")
        
        result = {
            "server_name": server_info["name"],
            "connected": False,
            "tools_count": 0,
            "tools_found": [],
            "missing_tools": [],
            "errors": []
        }
        
        try:
            async with Client(server_info["url"]) as client:
                # 测试连接
                print("✅ MCP客户端连接成功")
                result["connected"] = True
                
                # 获取工具列表
                tools = await client.list_tools()
                result["tools_count"] = len(tools)
                
                print(f"🔧 发现工具数量: {len(tools)}")
                print(f"📋 期望工具数量: {len(server_info['expected_tools'])}")
                
                # 详细列出所有工具
                for i, tool in enumerate(tools, 1):
                    tool_name = tool.name
                    result["tools_found"].append(tool_name)
                    
                    print(f"\n  🛠️  工具 {i}: {tool_name}")
                    print(f"      📝 描述: {tool.description}")
                    
                    # 显示工具参数
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        properties = tool.inputSchema.get('properties', {})
                        if properties:
                            print(f"      📥 参数:")
                            for param_name, param_info in properties.items():
                                param_type = param_info.get('type', 'unknown')
                                param_desc = param_info.get('description', '无描述')
                                print(f"         • {param_name} ({param_type}): {param_desc}")
                
                # 检查缺失的工具
                expected_tools = set(server_info["expected_tools"])
                found_tools = set(result["tools_found"])
                result["missing_tools"] = list(expected_tools - found_tools)
                
                if result["missing_tools"]:
                    print(f"\n⚠️  缺失的工具: {result['missing_tools']}")
                else:
                    print(f"\n✅ 所有期望的工具都已找到")
                
                return result
                
        except Exception as e:
            error_msg = f"连接错误: {str(e)}"
            print(f"❌ {error_msg}")
            result["errors"].append(error_msg)
            return result
    
    async def test_tool_execution(self, server_url: str, tool_name: str, test_args: Dict) -> Dict[str, Any]:
        """测试特定工具的执行"""
        print(f"\n🧪 测试工具执行: {tool_name}")
        print(f"📥 测试参数: {json.dumps(test_args, ensure_ascii=False, indent=2)}")
        
        result = {
            "tool_name": tool_name,
            "success": False,
            "response": None,
            "error": None,
            "execution_time": 0
        }
        
        try:
            start_time = time.time()
            async with Client(server_url) as client:
                response = await client.call_tool(tool_name, test_args)
                end_time = time.time()
                
                result["execution_time"] = round(end_time - start_time, 3)
                result["success"] = True
                
                # 提取响应内容
                response_text = None
                if hasattr(response, 'content') and response.content:
                    for content in response.content:
                        if hasattr(content, 'text'):
                            response_text = content.text
                            break
                elif hasattr(response, 'result'):
                    response_text = response.result
                elif hasattr(response, 'data'):
                    response_text = response.data
                else:
                    response_text = str(response)
                
                result["response"] = response_text
                
                print(f"✅ 工具执行成功")
                print(f"⏱️  执行时间: {result['execution_time']}秒")
                print(f"📤 响应内容:")
                
                # 尝试格式化JSON响应
                try:
                    parsed_response = json.loads(response_text) if isinstance(response_text, str) else response_text
                    print(json.dumps(parsed_response, ensure_ascii=False, indent=2))
                except:
                    print(response_text)
                
                return result
                
        except Exception as e:
            error_msg = str(e)
            result["error"] = error_msg
            print(f"❌ 工具执行失败: {error_msg}")
            return result
    
    async def run_comprehensive_test(self):
        """运行综合测试"""
        print("🚀 开始MCP服务器综合测试")
        print(f"📅 测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. 连接测试
        print(f"\n{'🔗 第一阶段: 连接和工具发现测试':=^80}")
        connection_results = []
        
        for server_info in self.servers:
            result = await self.test_server_connection(server_info)
            connection_results.append(result)
            await asyncio.sleep(1)  # 避免过快请求
        
        # 2. 工具执行测试
        print(f"\n{'🧪 第二阶段: 工具执行测试':=^80}")
        execution_results = []
        
        # 定义测试用例
        test_cases = [
            {
                "server_url": "http://localhost:3001/sse/",
                "tool_name": "execute_mysql_query",
                "args": {"query": "SELECT VERSION() as mysql_version", "limit": 1}
            },
            {
                "server_url": "http://localhost:3002/sse/",
                "tool_name": "get_system_info",
                "args": {}
            },
            {
                "server_url": "http://localhost:3003/sse/",
                "tool_name": "get_es_indices",
                "args": {}
            },
            {
                "server_url": "http://localhost:3004/sse/",
                "tool_name": "get_zabbix_metrics",
                "args": {"hostname": "localhost"}
            }
        ]
        
        for test_case in test_cases:
            result = await self.test_tool_execution(
                test_case["server_url"],
                test_case["tool_name"],
                test_case["args"]
            )
            execution_results.append(result)
            await asyncio.sleep(1)
        
        # 3. 测试结果汇总
        self.print_test_summary(connection_results, execution_results)
    
    def print_test_summary(self, connection_results: List[Dict], execution_results: List[Dict]):
        """打印测试结果汇总"""
        print(f"\n{'📊 测试结果汇总':=^80}")
        
        # 连接测试汇总
        print(f"\n🔗 连接测试结果:")
        total_servers = len(connection_results)
        connected_servers = sum(1 for r in connection_results if r["connected"])
        
        print(f"   总服务器数: {total_servers}")
        print(f"   成功连接: {connected_servers}")
        print(f"   连接成功率: {connected_servers/total_servers*100:.1f}%")
        
        total_expected_tools = sum(len(server["expected_tools"]) for server in self.servers)
        total_found_tools = sum(r["tools_count"] for r in connection_results)
        
        print(f"   期望工具总数: {total_expected_tools}")
        print(f"   发现工具总数: {total_found_tools}")
        print(f"   工具发现率: {total_found_tools/total_expected_tools*100:.1f}%")
        
        # 执行测试汇总
        print(f"\n🧪 工具执行测试结果:")
        total_executions = len(execution_results)
        successful_executions = sum(1 for r in execution_results if r["success"])
        
        print(f"   总执行测试: {total_executions}")
        print(f"   成功执行: {successful_executions}")
        print(f"   执行成功率: {successful_executions/total_executions*100:.1f}%")
        
        if execution_results:
            avg_time = sum(r["execution_time"] for r in execution_results) / len(execution_results)
            print(f"   平均执行时间: {avg_time:.3f}秒")
        
        # 详细错误信息
        print(f"\n🐛 错误详情:")
        has_errors = False
        for result in connection_results:
            if result["errors"]:
                has_errors = True
                print(f"   {result['server_name']}: {'; '.join(result['errors'])}")
        
        for result in execution_results:
            if result["error"]:
                has_errors = True
                print(f"   {result['tool_name']}: {result['error']}")
        
        if not has_errors:
            print("   ✅ 没有发现错误")
        
        print(f"\n{'测试完成':=^80}")


async def main():
    """主函数"""
    tester = MCPTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())