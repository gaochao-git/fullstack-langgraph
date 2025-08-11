"""
Zabbix Service - 独立的Zabbix监控数据服务
"""
import os
import logging
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting Zabbix Service...")
    yield
    logger.info("Shutting down Zabbix Service...")

app = FastAPI(
    title="Zabbix Service",
    description="独立的Zabbix监控数据服务，提供统一的告警数据接口",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入Zabbix服务
from src.zabbix_service import get_zabbix_service
from src.zabbix_adapter import ZabbixAlarmAdapter


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "zabbix_service"}


@app.get("/api/alarms")
async def get_alarms(
    alarm_level: Optional[List[str]] = Query(None, description="严重级别过滤，支持多选"),
    alarm_time: Optional[str] = Query(None, description="时间过滤，返回大于等于此时间的告警"),
    team_tag: Optional[List[str]] = Query(None, description="团队标签过滤，支持多选"),
    idc_tag: Optional[List[str]] = Query(None, description="机房标签过滤，支持多选"),
    alarm_ip: Optional[str] = Query(None, description="主机IP过滤"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=1000, description="每页数量")
) -> Dict[str, Any]:
    """
    获取Zabbix告警数据，返回统一格式，支持多条件过滤
    
    支持的过滤条件：
    - alarm_level: 严重级别过滤，支持多选
    - alarm_time: 时间过滤，返回大于等于此时间的告警
    - team_tag: 团队标签过滤，支持多选
    - idc_tag: 机房标签过滤，支持多选
    - alarm_ip: 主机IP过滤
    
    返回格式：
    {
        "total": 100,
        "page": 1,
        "page_size": 50,
        "data": [
            {
                "alarm_id": "事件ID",
                "alarm_source": "Zabbix",
                "alarm_key": "监控指标key",
                "alarm_name": "告警名称",
                "alarm_desc": "告警描述",
                "alarm_level": "严重级别",
                "alarm_time": "时间",
                "alarm_ip": "主机IP",
                "team_tag": "团队tag",
                "idc_tag": "机房tag"
            }
        ]
    }
    """
    try:
        logger.info(f"Getting alarms with filters: level={alarm_level}, time>={alarm_time}, team={team_tag}, idc={idc_tag}, ip={alarm_ip}")
        
        zabbix_service = get_zabbix_service()
        
        async with zabbix_service:
            # 获取所有问题（暂时不限制，后续在内存中过滤）
            problems = await zabbix_service.get_problems(
                host_ids=None,
                severity_min=0,
                recent_only=False,
                limit=1000  # 获取更多数据以支持过滤
            )
            
            # 使用适配器转换为统一格式
            adapter = ZabbixAlarmAdapter()
            all_alarms = [adapter.to_alarm_format(problem) for problem in problems]
            
            # 应用过滤条件
            filtered_alarms = all_alarms
            
            # 级别过滤
            if alarm_level:
                filtered_alarms = [
                    alarm for alarm in filtered_alarms 
                    if alarm.get("alarm_level") in alarm_level
                ]
            
            # 时间过滤
            if alarm_time:
                filtered_alarms = [
                    alarm for alarm in filtered_alarms 
                    if alarm.get("alarm_time", "") >= alarm_time
                ]
            
            # 团队标签过滤
            if team_tag:
                filtered_alarms = [
                    alarm for alarm in filtered_alarms 
                    if alarm.get("team_tag") in team_tag
                ]
            
            # 机房标签过滤
            if idc_tag:
                filtered_alarms = [
                    alarm for alarm in filtered_alarms 
                    if alarm.get("idc_tag") in idc_tag
                ]
            
            # IP过滤
            if alarm_ip:
                filtered_alarms = [
                    alarm for alarm in filtered_alarms 
                    if alarm.get("alarm_ip") == alarm_ip
                ]
            
            # 计算总数
            total = len(filtered_alarms)
            
            # 分页处理
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paged_alarms = filtered_alarms[start_idx:end_idx]
            
            logger.info(f"Filtered {total} alarms, returning page {page} with {len(paged_alarms)} items")
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "data": paged_alarms
            }
            
    except Exception as e:
        logger.error(f"Error getting alarms: {e}", exc_info=True)
        raise


@app.get("/api/zabbix/problems")
async def get_zabbix_problems(
    host_id: Optional[str] = Query(None, description="主机ID"),
    severity_min: int = Query(2, ge=0, le=5, description="最小严重级别"),
    recent_only: bool = Query(True, description="只获取最近的问题"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制")
):
    """获取Zabbix原始问题数据"""
    try:
        zabbix_service = get_zabbix_service()
        
        async with zabbix_service:
            host_ids = [host_id] if host_id else None
            problems = await zabbix_service.get_problems(
                host_ids=host_ids,
                severity_min=severity_min,
                recent_only=recent_only,
                limit=limit
            )
            return problems
            
    except Exception as e:
        logger.error(f"Error getting Zabbix problems: {e}", exc_info=True)
        raise


@app.get("/api/zabbix/hosts")
async def get_zabbix_hosts():
    """获取Zabbix监控的主机列表"""
    try:
        zabbix_service = get_zabbix_service()
        
        async with zabbix_service:
            hosts = await zabbix_service.get_hosts()
            return hosts
            
    except Exception as e:
        logger.error(f"Error getting Zabbix hosts: {e}", exc_info=True)
        raise


@app.get("/api/zabbix/items")
async def get_zabbix_items(
    search: Optional[str] = Query(None, description="搜索关键词"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制")
):
    """获取Zabbix监控项列表"""
    try:
        zabbix_service = get_zabbix_service()
        
        async with zabbix_service:
            if search:
                items = await zabbix_service.get_items(
                    search={"name": search},
                    limit=limit
                )
                options = [
                    {
                        "value": item["key_"],
                        "label": item["key_"]
                    }
                    for item in items
                ]
            else:
                options = await zabbix_service.get_common_items()
        
        return options
        
    except Exception as e:
        logger.error(f"Error getting Zabbix items: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取配置
    host = os.getenv("ZABBIX_SERVICE_HOST", "0.0.0.0")
    port = int(os.getenv("ZABBIX_SERVICE_PORT", "8001"))
    
    uvicorn.run(app, host=host, port=port)