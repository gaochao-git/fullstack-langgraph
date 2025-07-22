# MCP服务器与客户端快速入门手册

## 📚 **什么是MCP**
MCP (Model Context Protocol) 是一个标准化协议，用于AI应用与外部工具的通信。它让你的工具可以独立运行，AI系统按需调用。

## 🏗️ **基本架构**
```
AI应用 ←→ MCP客户端 ←→ MCP服务器 ←→ 实际工具
```

## 🚀 **创建MCP服务器**

### **1. 安装依赖**
```bash
pip install fastmcp
```

### **2. 最简单的服务器**
```python
# my_server.py
from fastmcp import FastMCP

# 创建服务器
mcp = FastMCP("My First Server")

# 定义工具
@mcp.tool()
async def hello_world(name: str = "World") -> str:
    """向指定的人问好"""
    return f"Hello, {name}!"

@mcp.tool()
async def add_numbers(a: int, b: int) -> str:
    """计算两个数字的和"""
    result = a + b
    return f"{a} + {b} = {result}"

# 启动服务器
if __name__ == "__main__":
    mcp.run(transport="sse", host="localhost", port=3001)
```

### **3. 运行服务器**
```bash
python my_server.py
```

## 🔧 **创建MCP客户端**

### **基础客户端使用**
```python
# my_client.py
import asyncio
from fastmcp import Client

async def main():
    # 连接到MCP服务器
    async with Client("http://localhost:3001/sse/") as client:
        
        # 1. 发现可用工具
        tools = await client.list_tools()
        print("可用工具:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # 2. 调用工具
        result1 = await client.call_tool("hello_world", {"name": "Alice"})
        print(f"结果1: {result1}")
        
        result2 = await client.call_tool("add_numbers", {"a": 5, "b": 3})
        print(f"结果2: {result2}")

# 运行客户端
if __name__ == "__main__":
    asyncio.run(main())
```

## 📝 **实用工具示例**

### **文件操作服务器**
```python
# file_server.py
import os
import json
from fastmcp import FastMCP

mcp = FastMCP("File Tools Server")

@mcp.tool()
async def read_file(file_path: str) -> str:
    """读取文件内容"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.dumps({"success": True, "content": content})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool() 
async def write_file(file_path: str, content: str) -> str:
    """写入文件内容"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"success": True, "message": "文件写入成功"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def list_directory(dir_path: str = ".") -> str:
    """列出目录内容"""
    try:
        files = os.listdir(dir_path)
        return json.dumps({"success": True, "files": files})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

if __name__ == "__main__":
    mcp.run(transport="sse", host="localhost", port=3002)
```

### **HTTP请求服务器**
```python
# http_server.py
import json
import aiohttp
from fastmcp import FastMCP

mcp = FastMCP("HTTP Tools Server")

@mcp.tool()
async def get_request(url: str) -> str:
    """发送GET请求"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                content = await response.text()
                return json.dumps({
                    "success": True,
                    "status": response.status,
                    "content": content[:1000]  # 限制长度
                })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def post_request(url: str, data: str) -> str:
    """发送POST请求"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                content = await response.text()
                return json.dumps({
                    "success": True,
                    "status": response.status,
                    "content": content
                })
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

if __name__ == "__main__":
    mcp.run(transport="sse", host="localhost", port=3003)
```

## 🧪 **通用测试客户端**
```python
# test_client.py
import asyncio
import json
from fastmcp import Client

class MCPTester:
    def __init__(self, server_url: str):
        self.server_url = server_url
    
    async def test_server(self):
        """测试MCP服务器功能"""
        try:
            async with Client(self.server_url) as client:
                print(f"🔗 连接到: {self.server_url}")
                
                # 获取工具列表
                tools = await client.list_tools()
                print(f"✅ 发现 {len(tools)} 个工具:")
                
                for i, tool in enumerate(tools, 1):
                    print(f"  {i}. {tool.name}")
                    print(f"     描述: {tool.description}")
                    
                    # 显示参数
                    if hasattr(tool, 'inputSchema') and tool.inputSchema:
                        params = tool.inputSchema.get('properties', {})
                        if params:
                            print(f"     参数: {list(params.keys())}")
                    print()
                
                return tools
                
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return []
    
    async def call_tool(self, tool_name: str, args: dict = None):
        """调用指定工具"""
        if args is None:
            args = {}
            
        try:
            async with Client(self.server_url) as client:
                result = await client.call_tool(tool_name, args)
                
                # 提取结果文本
                result_text = None
                if hasattr(result, 'content') and result.content:
                    for content in result.content:
                        if hasattr(content, 'text'):
                            result_text = content.text
                            break
                else:
                    result_text = str(result)
                
                print(f"🔧 工具: {tool_name}")
                print(f"📥 参数: {args}")
                print(f"📤 结果: {result_text}")
                return result_text
                
        except Exception as e:
            print(f"❌ 工具调用失败: {e}")
            return None

# 使用示例
async def main():
    # 测试不同的服务器
    servers = [
        ("基础工具", "http://localhost:3001/sse/"),
        ("文件工具", "http://localhost:3002/sse/"),
        ("HTTP工具", "http://localhost:3003/sse/")
    ]
    
    for name, url in servers:
        print(f"\n{'='*50}")
        print(f"测试 {name} 服务器")
        print(f"{'='*50}")
        
        tester = MCPTester(url)
        tools = await tester.test_server()
        
        # 测试一些工具调用
        if tools:
            await asyncio.sleep(1)  # 稍等一下
            
            if name == "基础工具":
                await tester.call_tool("hello_world", {"name": "MCP"})
                await tester.call_tool("add_numbers", {"a": 10, "b": 20})
            
            elif name == "文件工具":
                await tester.call_tool("list_directory", {"dir_path": "."})
            
            elif name == "HTTP工具":
                await tester.call_tool("get_request", {
                    "url": "https://httpbin.org/get"
                })

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔄 **启动和使用流程**

### **1. 启动服务器**
```bash
# 终端1: 启动基础工具服务器
python my_server.py

# 终端2: 启动文件工具服务器  
python file_server.py

# 终端3: 启动HTTP工具服务器
python http_server.py
```

### **2. 测试服务器**
```bash
# 终端4: 运行测试客户端
python test_client.py
```

## 📋 **最佳实践**

### **1. 服务器端**
```python
# 1. 总是提供清楚的工具描述
@mcp.tool()
async def my_tool(param: str) -> str:
    """清楚描述这个工具的作用和用途"""
    pass

# 2. 使用类型提示
@mcp.tool() 
async def typed_tool(name: str, age: int, active: bool = True) -> str:
    """带类型提示的工具更容易使用"""
    pass

# 3. 返回JSON格式便于解析
@mcp.tool()
async def json_tool() -> str:
    return json.dumps({
        "success": True,
        "data": "some data",
        "message": "操作成功"
    })

# 4. 处理异常
@mcp.tool()
async def safe_tool() -> str:
    try:
        # 你的逻辑
        return json.dumps({"success": True})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
```

### **2. 客户端端**
```python
# 1. 总是使用async with
async with Client(server_url) as client:
    # 操作

# 2. 处理连接异常
try:
    async with Client(server_url) as client:
        result = await client.call_tool("tool_name", args)
except Exception as e:
    print(f"操作失败: {e}")

# 3. 验证工具存在
tools = await client.list_tools()
tool_names = [t.name for t in tools]
if "my_tool" in tool_names:
    await client.call_tool("my_tool", {})
```

## 🎯 **快速开始模板**

### **服务器模板**
```python
from fastmcp import FastMCP
import json

mcp = FastMCP("My Server Name")

@mcp.tool()
async def my_tool(param1: str, param2: int = 0) -> str:
    """工具描述"""
    try:
        # 你的逻辑
        result = f"处理 {param1}, 数值: {param2}"
        return json.dumps({"success": True, "result": result})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

if __name__ == "__main__":
    mcp.run(transport="sse", host="localhost", port=3001)
```

### **客户端模板**
```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:3001/sse/") as client:
        # 发现工具
        tools = await client.list_tools()
        print(f"工具: {[t.name for t in tools]}")
        
        # 调用工具
        result = await client.call_tool("my_tool", {
            "param1": "test",
            "param2": 42
        })
        print(f"结果: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📁 **本项目MCP服务器**

本目录包含的故障分析系统MCP服务器:

- `db_mcp_server.py` - MySQL数据库诊断工具 (端口3001)
- `ssh_mcp_server.py` - SSH系统管理工具 (端口3002)  
- `es_mcp_server.py` - Elasticsearch查询工具 (端口3003)
- `zabbix_mcp_server.py` - Zabbix监控工具 (端口3004)

### **启动本项目服务器**
```bash
# 启动所有服务器
./start_servers.sh

# 测试所有服务器
python test_mcp_detailed.py

# 停止所有服务器
./stop_servers.sh
```

这个手册涵盖了MCP的核心概念和实用例子。按照这些模板，你可以快速创建自己的MCP服务器和客户端！