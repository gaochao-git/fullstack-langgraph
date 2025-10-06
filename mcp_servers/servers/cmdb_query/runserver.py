#!/usr/bin/env python3
"""
CMDB Knowledge Graph Query MCP Server
提供CMDB知识图谱查询能力的MCP服务器
"""

import json
import logging
import sys
import os
from typing import Dict, Any, Optional
import asyncio

from fastmcp import FastMCP
from neo4j import AsyncGraphDatabase
from ..common.base_config import MCPServerConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("CMDB Knowledge Graph Query Server")

# 加载配置
config = MCPServerConfig('cmdb_query')

# Neo4j配置 - 从配置文件读取
NEO4J_URL = config.get('neo4j_url', 'bolt://82.156.146.51:7687')
NEO4J_USERNAME = config.get('neo4j_username', 'neo4j')
NEO4J_PASSWORD = config.get('neo4j_password', 'Neo4jPassword123')

# 创建Neo4j驱动
driver = AsyncGraphDatabase.driver(
    NEO4J_URL,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)


@mcp.tool()
async def query_cmdb_entity(entity_type: str, ci_id: str) -> str:
    """查询CMDB实体的详细信息

    Args:
        entity_type: 实体类型，可选值：
            - CMDB_Application: 应用
            - CMDB_Database: 数据库
            - CMDB_Cache: 缓存
            - CMDB_MessageQueue: 消息队列
            - CMDB_VirtualMachine: 虚拟机
            - CMDB_PhysicalServer: 物理服务器
            - CMDB_Rack: 机架
            - CMDB_Cabinet: 机柜
            - CMDB_DataCenter: 数据中心
        ci_id: 实体的CI ID

    Returns:
        实体详细信息的JSON字符串，如果不存在返回错误信息

    Examples:
        query_cmdb_entity("CMDB_Application", "DC-SH-001-CAB-01-RACK-01-SVR-01-VM-01-APP-1")
        query_cmdb_entity("CMDB_PhysicalServer", "DC-SH-001-CAB-01-RACK-01-SVR-01")
    """
    try:
        async with driver.session() as session:
            query = f"""
                MATCH (entity:{entity_type} {{ci_id: $ci_id}})
                RETURN entity
            """
            result = await session.run(query, ci_id=ci_id)
            record = await result.single()

            if record:
                entity_data = dict(record["entity"])
                return json.dumps(entity_data, ensure_ascii=False, indent=2)
            else:
                return json.dumps({
                    "error": "Entity not found",
                    "entity_type": entity_type,
                    "ci_id": ci_id
                }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"查询实体失败: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "entity_type": entity_type,
            "ci_id": ci_id
        }, ensure_ascii=False)


@mcp.tool()
async def query_application_dependencies(app_ci_id: str, direction: str = "upstream") -> str:
    """查询应用的依赖关系

    Args:
        app_ci_id: 应用的CI ID
        direction: 查询方向，可选值：
            - upstream: 上游依赖（查询该应用依赖的服务，如数据库、缓存等）
            - downstream: 下游影响（查询依赖该应用的其他服务）
            - both: 双向查询

    Returns:
        依赖关系的JSON字符串，包含依赖路径和相关服务信息

    Examples:
        query_application_dependencies("DC-SH-001-CAB-01-RACK-01-SVR-01-VM-01-APP-1", "upstream")
    """
    try:
        async with driver.session() as session:
            if direction == "upstream":
                # 查询上游依赖
                query = """
                    MATCH (app:CMDB_Application {ci_id: $app_ci_id})-[:DEPENDS_ON*1..3]->(dep)
                    RETURN
                        app.ci_id AS app_ci_id,
                        app.name AS app_name,
                        collect(DISTINCT {
                            ci_id: dep.ci_id,
                            name: dep.name,
                            type: labels(dep)[0],
                            status: dep.status
                        }) AS dependencies
                """
            elif direction == "downstream":
                # 查询下游影响
                query = """
                    MATCH (app:CMDB_Application {ci_id: $app_ci_id})<-[:DEPENDS_ON*1..3]-(dependent)
                    RETURN
                        app.ci_id AS app_ci_id,
                        app.name AS app_name,
                        collect(DISTINCT {
                            ci_id: dependent.ci_id,
                            name: dependent.name,
                            type: labels(dependent)[0],
                            status: dependent.status
                        }) AS dependents
                """
            else:  # both
                query = """
                    MATCH (app:CMDB_Application {ci_id: $app_ci_id})
                    OPTIONAL MATCH (app)-[:DEPENDS_ON*1..3]->(dep)
                    OPTIONAL MATCH (app)<-[:DEPENDS_ON*1..3]-(dependent)
                    RETURN
                        app.ci_id AS app_ci_id,
                        app.name AS app_name,
                        collect(DISTINCT dep) AS dependencies,
                        collect(DISTINCT dependent) AS dependents
                """

            result = await session.run(query, app_ci_id=app_ci_id)
            record = await result.single()

            if record:
                return json.dumps(dict(record), ensure_ascii=False, indent=2, default=str)
            else:
                return json.dumps({
                    "error": "Application not found",
                    "app_ci_id": app_ci_id
                }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"查询依赖关系失败: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "app_ci_id": app_ci_id
        }, ensure_ascii=False)


@mcp.tool()
async def query_physical_topology(ci_id: str) -> str:
    """查询实体的完整物理拓扑路径

    从应用/数据库一直追溯到物理数据中心的完整路径：
    应用 → 虚拟机 → 物理服务器 → 机架 → 机柜 → 数据中心

    Args:
        ci_id: 应用、数据库、缓存、消息队列或虚拟机的CI ID

    Returns:
        完整物理路径的JSON字符串

    Examples:
        query_physical_topology("DC-SH-001-CAB-01-RACK-01-SVR-01-VM-01-APP-1")
    """
    try:
        async with driver.session() as session:
            query = """
                MATCH path = (app {ci_id: $ci_id})
                  -[:RUNS_ON]->(vm:CMDB_VirtualMachine)
                  <-[:HOSTS]-(server:CMDB_PhysicalServer)
                  <-[:CONTAINS]-(rack:CMDB_Rack)
                  <-[:CONTAINS]-(cabinet:CMDB_Cabinet)
                  <-[:CONTAINS]-(dc:CMDB_DataCenter)
                RETURN
                  app.name AS application_name,
                  app.ci_id AS application_ci_id,
                  labels(app)[0] AS application_type,
                  vm.name AS vm_name,
                  vm.ip_address AS vm_ip,
                  server.name AS server_name,
                  server.ip_address AS server_ip,
                  rack.name AS rack_name,
                  cabinet.name AS cabinet_name,
                  dc.name AS datacenter_name,
                  dc.city AS city
            """

            result = await session.run(query, ci_id=ci_id)
            record = await result.single()

            if record:
                return json.dumps(dict(record), ensure_ascii=False, indent=2)
            else:
                return json.dumps({
                    "error": "Physical topology not found",
                    "ci_id": ci_id,
                    "message": "该实体可能不是应用/数据库，或者拓扑数据不完整"
                }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"查询物理拓扑失败: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "ci_id": ci_id
        }, ensure_ascii=False)


@mcp.tool()
async def search_cmdb_entities(entity_type: str, filters: Optional[str] = None, limit: int = 10) -> str:
    """搜索CMDB实体

    Args:
        entity_type: 实体类型（如 CMDB_Application, CMDB_Database 等）
        filters: 过滤条件，JSON格式字符串，例如：
            '{"status": "operational", "city": "上海"}'
            '{"environment": "production"}'
        limit: 返回结果数量限制（默认10，最大100）

    Returns:
        匹配的实体列表JSON字符串

    Examples:
        search_cmdb_entities("CMDB_Application", '{"environment": "production"}', 5)
        search_cmdb_entities("CMDB_PhysicalServer", '{"city": "上海"}', 10)
    """
    try:
        # 限制最大返回数量
        limit = min(limit, 100)

        # 解析过滤条件
        filter_dict = {}
        if filters:
            filter_dict = json.loads(filters)

        async with driver.session() as session:
            # 构建WHERE子句
            where_clauses = []
            params = {"limit": limit}

            for key, value in filter_dict.items():
                where_clauses.append(f"entity.{key} = ${key}")
                params[key] = value

            where_statement = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            query = f"""
                MATCH (entity:{entity_type})
                {where_statement}
                RETURN entity
                ORDER BY entity.created_at DESC
                LIMIT $limit
            """

            result = await session.run(query, **params)

            entities = []
            async for record in result:
                entities.append(dict(record["entity"]))

            return json.dumps({
                "entity_type": entity_type,
                "filters": filter_dict,
                "count": len(entities),
                "entities": entities
            }, ensure_ascii=False, indent=2, default=str)

    except Exception as e:
        logger.error(f"搜索实体失败: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "entity_type": entity_type,
            "filters": filters
        }, ensure_ascii=False)


@mcp.tool()
async def query_server_vms(server_ci_id: str) -> str:
    """查询物理服务器上运行的所有虚拟机

    Args:
        server_ci_id: 物理服务器的CI ID

    Returns:
        该服务器上所有虚拟机的列表JSON字符串

    Examples:
        query_server_vms("DC-SH-001-CAB-01-RACK-01-SVR-01")
    """
    try:
        async with driver.session() as session:
            query = """
                MATCH (server:CMDB_PhysicalServer {ci_id: $server_ci_id})
                      -[:HOSTS]->(vm:CMDB_VirtualMachine)
                RETURN
                    server.ci_id AS server_ci_id,
                    server.name AS server_name,
                    collect({
                        ci_id: vm.ci_id,
                        name: vm.name,
                        ip_address: vm.ip_address,
                        vcpu: vm.vcpu,
                        vram_gb: vm.vram_gb,
                        status: vm.status
                    }) AS vms
            """

            result = await session.run(query, server_ci_id=server_ci_id)
            record = await result.single()

            if record:
                data = dict(record)
                data['vm_count'] = len(data['vms'])
                return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                return json.dumps({
                    "error": "Server not found or has no VMs",
                    "server_ci_id": server_ci_id
                }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"查询服务器虚拟机失败: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "server_ci_id": server_ci_id
        }, ensure_ascii=False)


@mcp.tool()
async def query_vm_applications(vm_ci_id: str) -> str:
    """查询虚拟机上运行的所有应用和服务

    Args:
        vm_ci_id: 虚拟机的CI ID

    Returns:
        该虚拟机上所有应用、数据库、缓存、消息队列的列表JSON字符串

    Examples:
        query_vm_applications("DC-SH-001-CAB-01-RACK-01-SVR-01-VM-01")
    """
    try:
        async with driver.session() as session:
            query = """
                MATCH (vm:CMDB_VirtualMachine {ci_id: $vm_ci_id})
                      <-[:RUNS_ON]-(app)
                WHERE 'CMDB_Application' IN labels(app)
                   OR 'CMDB_Database' IN labels(app)
                   OR 'CMDB_Cache' IN labels(app)
                   OR 'CMDB_MessageQueue' IN labels(app)
                RETURN
                    vm.ci_id AS vm_ci_id,
                    vm.name AS vm_name,
                    collect({
                        ci_id: app.ci_id,
                        name: app.name,
                        type: [l IN labels(app) WHERE l STARTS WITH 'CMDB_'][0],
                        status: app.status,
                        port: COALESCE(app.service_port, app.port)
                    }) AS applications
            """

            result = await session.run(query, vm_ci_id=vm_ci_id)
            record = await result.single()

            if record:
                data = dict(record)
                data['application_count'] = len(data['applications'])
                return json.dumps(data, ensure_ascii=False, indent=2)
            else:
                return json.dumps({
                    "error": "VM not found or has no applications",
                    "vm_ci_id": vm_ci_id
                }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"查询虚拟机应用失败: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "vm_ci_id": vm_ci_id
        }, ensure_ascii=False)


if __name__ == "__main__":
    # 运行MCP服务器
    port = config.get('port', 3009)
    logger.info("Starting CMDB Knowledge Graph Query MCP Server...")
    logger.info(f"Neo4j URL: {NEO4J_URL}")
    logger.info(f"Server port: {port}")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
