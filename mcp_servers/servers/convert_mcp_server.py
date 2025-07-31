#!/usr/bin/env python3
"""
多路由OpenAPI MCP服务器
在单个端口上通过不同路径暴露多个OpenAPI配置
支持动态路由: http://host:port/{prefix}/sse
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urljoin
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend/src'))

try:
    from fastmcp import FastMCP
    from pydantic import BaseModel
except ImportError as e:
    print(f"请安装必要依赖: pip install fastmcp pydantic httpx fastapi uvicorn")
    sys.exit(1)

# 数据库和配置导入
try:
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker
    from src.apps.mcp.models import OpenAPIMCPConfig
    from src.shared.db.config import DATABASE_URL
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"数据库模块导入失败: {e}")
    print("将使用模拟数据运行")
    DATABASE_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAPITool(BaseModel):
    """OpenAPI工具定义"""
    name: str
    description: str
    method: str
    path: str
    base_url: str
    parameters: List[Dict[str, Any]] = []
    request_body: Optional[Dict[str, Any]] = None
    auth_config: Optional[Dict[str, Any]] = None
    timeout_config: Optional[Dict[str, Any]] = None


class MultiRouteMCPServer:
    """多路由MCP服务器"""
    
    def __init__(self):
        self.mcps: Dict[str, FastMCP] = {}  # prefix -> FastMCP实例
        self.tools_cache: Dict[str, List[OpenAPITool]] = {}  # prefix -> 工具列表
        self.config_cache: Dict[str, Dict] = {}  # prefix -> 配置信息
        self.app = FastAPI(title="OpenAPI MCP Server", description="动态OpenAPI MCP服务器")
        self.setup_database()
        self.setup_routes()
    
    def setup_database(self):
        """设置数据库连接"""
        if not DATABASE_AVAILABLE:
            self.engine = None
            self.Session = None
            return
            
        try:
            # 转换为同步数据库URL
            sync_db_url = DATABASE_URL.replace('aiomysql+asyncmy://', 'mysql+pymysql://')
            self.engine = create_engine(sync_db_url)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("数据库连接设置完成")
        except Exception as e:
            logger.error(f"数据库连接设置失败: {e}")
            self.engine = None
            self.Session = None
    
    def get_mock_data(self) -> List[Dict[str, Any]]:
        """获取模拟数据"""
        return [
            {
                'id': 1,
                'mcp_server_prefix': 'jsonplaceholder_api',
                'mcp_tool_name': 'get_users',
                'mcp_tool_enabled': 1,
                'openapi_schema': '{
                    "openapi": "3.0.0",
                    "info": {"title": "JSONPlaceholder API", "version": "1.0.0"},
                    "servers": [{"url": "https://jsonplaceholder.typicode.com"}],
                    "paths": {
                        "/users": {
                            "get": {
                                "summary": "获取用户列表",
                                "operationId": "getUsers",
                                "parameters": [
                                    {
                                        "name": "_limit",
                                        "in": "query",
                                        "required": false,
                                        "description": "限制返回数量",
                                        "schema": {"type": "integer", "example": 5}
                                    }
                                ],
                                "responses": {
                                    "200": {
                                        "description": "成功",
                                        "content": {
                                            "application/json": {
                                                "schema": {
                                                    "type": "array",
                                                    "items": {"type": "object"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }',
                'auth_config': '{}',
                'extra_config': '{"read_timeout": 30, "connect_timeout": 10}',
                'is_deleted': 0
            },
            {
                'id': 2,
                'mcp_server_prefix': 'httpbin_api',
                'mcp_tool_name': 'test_get',
                'mcp_tool_enabled': 1,
                'openapi_schema': '{
                    "openapi": "3.0.0",
                    "info": {"title": "HTTPBin API", "version": "1.0.0"},
                    "servers": [{"url": "https://httpbin.org"}],
                    "paths": {
                        "/get": {
                            "get": {
                                "summary": "测试GET请求",
                                "operationId": "testGet",
                                "parameters": [
                                    {
                                        "name": "param1",
                                        "in": "query",
                                        "required": false,
                                        "description": "测试参数1",
                                        "schema": {"type": "string", "example": "test_value"}
                                    }
                                ],
                                "responses": {
                                    "200": {
                                        "description": "成功"
                                    }
                                }
                            }
                        }
                    }
                }',
                'auth_config': '{}',
                'extra_config': '{"read_timeout": 30, "connect_timeout": 10}',
                'is_deleted': 0
            }
        ]
    
    def load_openapi_configs(self) -> List[Dict[str, Any]]:
        """从数据库加载OpenAPI配置"""
        if not self.Session:
            # 返回模拟数据
            return self.get_mock_data()
        
        try:
            with self.Session() as session:
                stmt = select(OpenAPIMCPConfig).where(
                    (OpenAPIMCPConfig.is_deleted == 0) & 
                    (OpenAPIMCPConfig.mcp_tool_enabled == 1)
                )
                configs = session.execute(stmt).scalars().all()
                
                result = []
                for config in configs:
                    config_dict = config.to_dict()
                    result.append(config_dict)
                
                logger.info(f"从数据库加载了 {len(result)} 个启用的OpenAPI配置")
                return result
                
        except Exception as e:
            logger.error(f"加载OpenAPI配置失败: {e}")
            # 降级到模拟数据
            return self.get_mock_data()
    
    def generate_prefix_from_config(self, config: Dict[str, Any]) -> str:
        """从配置获取MCP服务前缀"""
        return config.get('mcp_server_prefix', f"config_{config.get('id', 'unknown')}")
    
    def parse_openapi_config(self, config: Dict[str, Any]) -> List[OpenAPITool]:
        """解析OpenAPI配置生成工具列表"""
        tools = []
        
        try:
            # 解析OpenAPI schema
            openapi_schema = config.get('openapi_schema', '{}')
            if isinstance(openapi_schema, str):
                openapi_schema = json.loads(openapi_schema)
            
            # 获取认证和超时配置
            auth_config = config.get('auth_config', '{}')
            if isinstance(auth_config, str) and auth_config:
                auth_config = json.loads(auth_config)
            else:
                auth_config = {}
            
            extra_config = config.get('extra_config', '{}')
            if isinstance(extra_config, str) and extra_config:
                extra_config = json.loads(extra_config)
            else:
                extra_config = {'read_timeout': 30, 'connect_timeout': 10}
            
            # 从 OpenAPI schema 中提取服务器URL
            servers = openapi_schema.get('servers', [])
            base_url = servers[0].get('url', '') if servers else ''
            
            # 解析paths生成工具
            paths = openapi_schema.get('paths', {})
            for path, path_item in paths.items():
                for method, operation in path_item.items():
                    if method.lower() in ['get', 'post', 'put', 'delete', 'patch']:
                        tool_name = operation.get('operationId', config.get('mcp_tool_name', 'api_tool'))
                        tool = OpenAPITool(
                            name=tool_name,
                            description=operation.get('summary', operation.get('description', f'{method.upper()} {path}')),
                            method=method.upper(),
                            path=path,
                            base_url=base_url,
                            parameters=operation.get('parameters', []),
                            request_body=operation.get('requestBody'),
                            auth_config=auth_config,
                            timeout_config=extra_config
                        )
                        tools.append(tool)
                        break  # 每个配置只生成一个工具（根据数据结构）
                        
        except Exception as e:
            logger.error(f"解析OpenAPI配置失败: {e}")
        
        return tools
    
    def create_mcp_for_config(self, prefix: str, config: Dict[str, Any]) -> FastMCP:
        """为指定配置创建MCP实例"""
        mcp_name = f"openapi_mcp_{prefix}"
        mcp = FastMCP(mcp_name)
        tools = self.parse_openapi_config(config)
        
        # 缓存工具和配置
        self.tools_cache[prefix] = tools
        self.config_cache[prefix] = config
        
        # 为每个工具注册MCP工具函数
        for tool in tools:
            self.register_tool_to_mcp(mcp, tool)
        
        logger.info(f"为prefix '{prefix}' 创建MCP '{mcp_name}'，包含 {len(tools)} 个工具")
        return mcp
    
    def register_tool_to_mcp(self, mcp: FastMCP, tool: OpenAPITool):
        """将OpenAPI工具注册到MCP"""
        
        async def create_tool_function(current_tool):
            """为每个工具创建独立的函数"""
            async def tool_function(**kwargs) -> str:
                return await self.execute_http_request(current_tool, kwargs)
            return tool_function
        
        # 生成工具参数Schema
        parameters = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param in tool.parameters:
            param_name = param.get('name', '')
            param_schema = param.get('schema', {'type': 'string'})
            param_required = param.get('required', False)
            
            parameters["properties"][param_name] = {
                "type": param_schema.get('type', 'string'),
                "description": param.get('description', f'{param_name}参数')
            }
            
            if 'example' in param_schema:
                parameters["properties"][param_name]["example"] = param_schema['example']
            
            if param_required:
                parameters["required"].append(param_name)
        
        # 处理请求体参数
        if tool.request_body:
            parameters["properties"]["body"] = {
                "type": "object",
                "description": "请求体数据"
            }
        
        # 创建工具函数
        tool_func = asyncio.create_task(create_tool_function(tool)).result()
        
        # 注册工具到MCP
        mcp.tool(
            name=tool.name,
            description=tool.description,
            parameters=parameters
        )(tool_func)
    
    async def execute_http_request(self, tool: OpenAPITool, params: Dict[str, Any]) -> str:
        """执行HTTP请求"""
        try:
            # 构建URL
            path = tool.path
            query_params = {}
            path_params = {}
            
            # 分离路径参数和查询参数
            for param in tool.parameters:
                param_name = param.get('name', '')
                param_in = param.get('in', 'query')
                
                if param_name in params:
                    if param_in == 'path':
                        path_params[param_name] = params[param_name]
                    elif param_in == 'query':
                        query_params[param_name] = params[param_name]
            
            # 替换路径参数
            for param_name, param_value in path_params.items():
                path = path.replace(f'{{{param_name}}}', str(param_value))
            
            # 构建完整URL
            url = urljoin(tool.base_url, path.lstrip('/'))
            
            # 设置超时
            timeout_config = tool.timeout_config or {}
            timeout = httpx.Timeout(
                connect=timeout_config.get('connect_timeout', 10),
                read=timeout_config.get('read_timeout', 30),
                write=timeout_config.get('write_timeout', 10),
                pool=timeout_config.get('total_timeout', 60)
            )
            
            # 设置认证头
            headers = {'Content-Type': 'application/json'}
            auth_config = tool.auth_config or {}
            
            if auth_config:
                auth_type = auth_config.get('type', 'none')
                if auth_type == 'bearer':
                    token = auth_config.get('token', '')
                    prefix = auth_config.get('token_prefix', 'Bearer')
                    headers['Authorization'] = f'{prefix} {token}'
                elif auth_type == 'api_key':
                    header_name = auth_config.get('header_name', 'X-API-Key')
                    api_key = auth_config.get('api_key', '')
                    headers[header_name] = api_key
            
            # 执行HTTP请求
            async with httpx.AsyncClient(timeout=timeout) as client:
                if tool.method.upper() == 'GET':
                    response = await client.get(url, params=query_params, headers=headers)
                elif tool.method.upper() == 'POST':
                    json_data = params.get('body') if 'body' in params else None
                    response = await client.post(url, params=query_params, json=json_data, headers=headers)
                elif tool.method.upper() == 'PUT':
                    json_data = params.get('body') if 'body' in params else None
                    response = await client.put(url, params=query_params, json=json_data, headers=headers)
                elif tool.method.upper() == 'DELETE':
                    response = await client.delete(url, params=query_params, headers=headers)
                else:
                    return f"不支持的HTTP方法: {tool.method}"
                
                # 处理响应
                if response.status_code >= 400:
                    return f"HTTP错误 {response.status_code}: {response.text}"
                
                try:
                    result = response.json()
                    return json.dumps(result, ensure_ascii=False, indent=2)
                except:
                    return response.text
                    
        except Exception as e:
            logger.error(f"执行HTTP请求失败 [{tool.name}]: {e}")
            return f"请求执行失败: {str(e)}"
    
    def setup_routes(self):
        """设置路由"""
        
        @self.app.get("/")
        async def root():
            """根路径，显示可用的MCP端点"""
            configs = self.load_openapi_configs()
            endpoints = []
            
            # 按prefix分组
            prefix_groups = {}
            for config in configs:
                prefix = self.generate_prefix_from_config(config)
                if prefix not in prefix_groups:
                    prefix_groups[prefix] = []
                prefix_groups[prefix].append(config)
            
            for prefix, prefix_configs in prefix_groups.items():
                endpoints.append({
                    'prefix': prefix,
                    'tools_count': len(prefix_configs),
                    'tool_names': [cfg.get('mcp_tool_name', 'unknown') for cfg in prefix_configs],
                    'sse_endpoint': f'/{prefix}/sse',
                    'stdio_endpoint': f'/{prefix}/stdio'
                })
            
            return {
                'message': 'OpenAPI MCP Server',
                'available_endpoints': endpoints,
                'total_prefixes': len(endpoints),
                'total_tools': len(configs)
            }
        
        @self.app.get("/{prefix}/sse")
        @self.app.post("/{prefix}/sse")
        async def handle_sse(prefix: str):
            """处理SSE请求"""
            return await self.handle_mcp_request(prefix, 'sse')
        
        @self.app.get("/{prefix}/stdio")
        @self.app.post("/{prefix}/stdio")
        async def handle_stdio(prefix: str):
            """处理STDIO请求"""
            return await self.handle_mcp_request(prefix, 'stdio')
    
    
    def create_mcp_for_prefix(self, prefix: str, configs: List[Dict[str, Any]]) -> FastMCP:
        """为指定前缀下的所有配置创建MCP实例"""
        mcp_name = f"openapi_mcp_{prefix}"
        mcp = FastMCP(mcp_name)
        all_tools = []
        
        # 为每个配置解析工具
        for config in configs:
            tools = self.parse_openapi_config(config)
            all_tools.extend(tools)
        
        # 缓存工具和配置
        self.tools_cache[prefix] = all_tools
        self.config_cache[prefix] = configs[0] if configs else {}  # 使用第一个配置作为代表
        
        # 为每个工具注册MCP工具函数
        for tool in all_tools:
            self.register_tool_to_mcp(mcp, tool)
        
        logger.info(f"为prefix '{prefix}' 创建MCP '{mcp_name}'，包含 {len(all_tools)} 个工具")
        return mcp
        
    async def handle_mcp_request(self, prefix: str, transport: str):
        """处理MCP请求"""
        if prefix not in self.mcps:
            # 动态创建MCP实例
            configs = self.load_openapi_configs()
            prefix_configs = [cfg for cfg in configs if self.generate_prefix_from_config(cfg) == prefix]
            
            if not prefix_configs:
                raise HTTPException(status_code=404, detail=f"MCP服务前缀 '{prefix}' 不存在")
            
            # 为该prefix下的所有配置创建MCP实例
            self.mcps[prefix] = self.create_mcp_for_prefix(prefix, prefix_configs)
        
        mcp = self.mcps[prefix]
        
        # 这里需要根据FastMCP的实际API来处理请求
        # 由于FastMCP的具体实现可能有所不同，这里提供一个框架
        try:
            # 假设FastMCP有处理请求的方法
            if hasattr(mcp, 'handle_request'):
                return await mcp.handle_request(transport=transport)
            else:
                return {"error": "MCP请求处理未实现"}
        except Exception as e:
            logger.error(f"处理MCP请求失败 [{prefix}]: {e}")
            raise HTTPException(status_code=500, detail=f"MCP服务错误: {str(e)}")
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8100):
        """启动服务器"""
        logger.info(f"启动OpenAPI MCP服务器在 http://{host}:{port}")
        
        # 预加载所有配置
        configs = self.load_openapi_configs()
        logger.info(f"预加载了 {len(configs)} 个启用的OpenAPI配置")
        
        # 按prefix分组显示
        prefix_groups = {}
        for config in configs:
            prefix = self.generate_prefix_from_config(config)
            if prefix not in prefix_groups:
                prefix_groups[prefix] = []
            prefix_groups[prefix].append(config.get('mcp_tool_name', 'unknown'))
        
        for prefix, tool_names in prefix_groups.items():
            logger.info(f"  - {prefix} -> /{prefix}/sse (包含工具: {', '.join(tool_names)})")
        
        # 启动服务器
        config = uvicorn.Config(self.app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """主函数"""
    server = MultiRouteMCPServer()
    
    try:
        await server.start_server(host="0.0.0.0", port=8100)
    except KeyboardInterrupt:
        logger.info("服务器停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")


if __name__ == "__main__":
    print("🚀 启动多路由OpenAPI MCP服务器...")
    print("📡 服务将在 http://localhost:8100 启动")
    print("🔗 访问根路径查看所有可用的MCP端点")
    asyncio.run(main())