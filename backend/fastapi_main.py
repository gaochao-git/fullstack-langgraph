"""
独立的FastAPI应用 - 完全脱离LangGraph CLI
支持诊断代理的标准HTTP API接口
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# 导入诊断代理
from src.agents.diagnostic_agent.graph import graph
from src.agents.diagnostic_agent.state import DiagnosticState
from src.agents.diagnostic_agent.configuration import Configuration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 请求和响应模型
class DiagnosticRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class DiagnosticResponse(BaseModel):
    thread_id: str
    messages: List[Dict[str, Any]]
    status: str
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# 全局配置
app_config = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的处理"""
    global app_config
    
    # 启动时初始化
    logger.info("初始化诊断代理...")
    app_config = Configuration(
        query_generator_model="deepseek-chat",
        answer_model="deepseek-chat", 
        question_analysis_temperature=0.1,
        tool_planning_temperature=0.2,
        final_report_temperature=0.1
    )
    logger.info("诊断代理初始化完成")
    
    yield
    
    # 关闭时清理
    logger.info("应用关闭，清理资源...")

# 创建FastAPI应用
app = FastAPI(
    title="诊断代理API",
    description="基于LangGraph的故障诊断系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="1.0.0"
    )

# 诊断接口
@app.post("/diagnose", response_model=DiagnosticResponse)
async def diagnose(request: DiagnosticRequest):
    """
    诊断接口 - 处理故障诊断请求
    """
    try:
        logger.info(f"收到诊断请求: {request.message[:50]}...")
        
        # 准备输入
        input_data = {
            "messages": [{"role": "user", "content": request.message}]
        }
        
        # 构建配置
        config = {
            "configurable": {
                "query_generator_model": "deepseek-chat",
                "answer_model": "deepseek-chat",
                "question_analysis_temperature": 0.1,
                "tool_planning_temperature": 0.2,
                "final_report_temperature": 0.1
            }
        }
        
        # 调用诊断图
        result = await graph.ainvoke(input_data, config=config)
        
        # 处理结果
        thread_id = request.thread_id or f"thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        response = DiagnosticResponse(
            thread_id=thread_id,
            messages=result.get("messages", []),
            status="completed",
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"诊断完成: {thread_id}")
        return response
        
    except Exception as e:
        logger.error(f"诊断过程出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"诊断失败: {str(e)}")

# 流式诊断接口
@app.post("/diagnose/stream")
async def diagnose_stream(request: DiagnosticRequest):
    """
    流式诊断接口 - 实时返回诊断过程
    """
    async def generate():
        try:
            logger.info(f"开始流式诊断: {request.message[:50]}...")
            
            # 准备输入
            input_data = {
                "messages": [{"role": "user", "content": request.message}]
            }
            
            # 构建配置
            config = {
                "configurable": {
                    "query_generator_model": "deepseek-chat",
                    "answer_model": "deepseek-chat",
                    "question_analysis_temperature": 0.1,
                    "tool_planning_temperature": 0.2,
                    "final_report_temperature": 0.1
                }
            }
            
            # 流式调用诊断图
            async for chunk in graph.astream(input_data, config=config):
                yield f"data: {chunk}\n\n"
                
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"流式诊断出错: {str(e)}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

# 获取诊断状态
@app.get("/diagnose/{thread_id}/status")
async def get_diagnosis_status(thread_id: str):
    """获取诊断状态"""
    # 这里可以集成数据库来跟踪诊断状态
    return {
        "thread_id": thread_id,
        "status": "unknown",  # 需要实现状态跟踪
        "timestamp": datetime.now().isoformat()
    }

# 中断诊断
@app.post("/diagnose/{thread_id}/interrupt")
async def interrupt_diagnosis(thread_id: str, approval: bool):
    """处理诊断中的审批请求"""
    # TODO: 实现中断处理逻辑
    logger.info(f"收到中断请求: {thread_id}, 审批: {approval}")
    return {
        "thread_id": thread_id,
        "action": "approved" if approval else "rejected",
        "timestamp": datetime.now().isoformat()
    }

# 获取可用工具列表
@app.get("/tools")
async def get_available_tools():
    """获取可用的诊断工具"""
    from src.agents.diagnostic_agent.tools import all_tools
    
    tools_info = []
    for tool in all_tools:
        tools_info.append({
            "name": tool.name,
            "description": tool.description,
            "parameters": getattr(tool, "args_schema", {})
        })
    
    return {"tools": tools_info}

# 根路径重定向
@app.get("/")
async def root():
    """根路径信息"""
    return {
        "message": "诊断代理API服务",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    # 生产环境配置
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    workers = int(os.getenv("WORKERS", 1))
    
    logger.info(f"启动诊断代理API服务: {host}:{port}")
    
    uvicorn.run(
        "fastapi_main:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,  # 生产环境不启用热重载
        access_log=True,
        log_level="info"
    )