"""
CMDB Service
提供 CMDB 数据的 CRUD 操作，包含自动 Schema 校验
"""
from typing import Dict, List, Optional, Any
from neo4j import AsyncGraphDatabase
from src.shared.core.config import settings
from src.shared.core.logging import get_logger
from ..schema_manager import get_schema_manager

logger = get_logger(__name__)


class CMDBService:
    """CMDB 服务"""

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URL,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        self.schema_manager = get_schema_manager()

    # ==================== 实体操作 ====================

    async def create_entity(self, entity_type: str, properties: Dict[str, Any]) -> Dict:
        """
        创建 CMDB 实体（带 Schema 校验）

        Args:
            entity_type: 实体类型（如 CMDB_Server）
            properties: 实体属性

        Returns:
            创建的实体数据

        Raises:
            ValueError: Schema 校验失败
        """
        # 1. Schema 校验
        validation = await self.schema_manager.validate_entity(entity_type, properties)
        if not validation["valid"]:
            raise ValueError(f"Schema 校验失败: {', '.join(validation['errors'])}")

        # 2. 创建实体
        async with self.driver.session() as session:
            # 自动添加时间戳
            properties["created_at"] = properties.get("created_at", "datetime()")
            properties["updated_at"] = properties.get("updated_at", "datetime()")

            # 构建 Cypher 语句
            query = f"""
                CREATE (entity:{entity_type} $properties)
                RETURN entity
            """

            result = await session.run(query, properties=properties)
            record = await result.single()

            if record:
                entity_data = dict(record["entity"])
                logger.info(f"创建实体成功: {entity_type} - {properties.get('ci_id')}")
                return entity_data
            else:
                raise Exception("创建实体失败")

    async def update_entity(self, entity_type: str, ci_id: str, properties: Dict[str, Any]) -> Dict:
        """
        更新 CMDB 实体

        Args:
            entity_type: 实体类型
            ci_id: 实体ID
            properties: 要更新的属性

        Returns:
            更新后的实体数据
        """
        # Schema 校验（只校验提供的字段）
        schema_config = await self.schema_manager.get_entity_schema(entity_type)
        if not schema_config:
            raise ValueError(f"未知的实体类型: {entity_type}")

        async with self.driver.session() as session:
            # 构建 SET 语句
            set_clauses = []
            for key, value in properties.items():
                set_clauses.append(f"entity.{key} = ${key}")

            set_statement = ", ".join(set_clauses)
            properties["updated_at"] = "datetime()"
            set_statement += ", entity.updated_at = datetime()"

            query = f"""
                MATCH (entity:{entity_type} {{ci_id: $ci_id}})
                SET {set_statement}
                RETURN entity
            """

            params = {"ci_id": ci_id, **properties}
            result = await session.run(query, params)
            record = await result.single()

            if record:
                entity_data = dict(record["entity"])
                logger.info(f"更新实体成功: {entity_type} - {ci_id}")
                return entity_data
            else:
                raise ValueError(f"未找到实体: {entity_type} - {ci_id}")

    async def get_entity(self, entity_type: str, ci_id: str) -> Optional[Dict]:
        """
        获取单个实体

        Args:
            entity_type: 实体类型
            ci_id: 实体ID

        Returns:
            实体数据，如果不存在返回 None
        """
        async with self.driver.session() as session:
            query = f"""
                MATCH (entity:{entity_type} {{ci_id: $ci_id}})
                RETURN entity
            """

            result = await session.run(query, ci_id=ci_id)
            record = await result.single()

            if record:
                return dict(record["entity"])
            else:
                return None

    async def delete_entity(self, entity_type: str, ci_id: str) -> bool:
        """
        删除实体（同时删除所有关系）

        Args:
            entity_type: 实体类型
            ci_id: 实体ID

        Returns:
            是否删除成功
        """
        async with self.driver.session() as session:
            query = f"""
                MATCH (entity:{entity_type} {{ci_id: $ci_id}})
                DETACH DELETE entity
                RETURN count(entity) AS deleted_count
            """

            result = await session.run(query, ci_id=ci_id)
            record = await result.single()

            deleted = record["deleted_count"] > 0
            if deleted:
                logger.info(f"删除实体成功: {entity_type} - {ci_id}")
            else:
                logger.warning(f"实体不存在: {entity_type} - {ci_id}")

            return deleted

    async def list_entities(
        self,
        entity_type: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict]:
        """
        列出实体（支持过滤）

        Args:
            entity_type: 实体类型
            filters: 过滤条件（如 {"status": "operational", "city": "上海"}）
            limit: 返回数量
            skip: 跳过数量

        Returns:
            实体列表
        """
        async with self.driver.session() as session:
            # 构建 WHERE 子句
            where_clauses = []
            params = {"limit": limit, "skip": skip}

            if filters:
                for key, value in filters.items():
                    where_clauses.append(f"entity.{key} = ${key}")
                    params[key] = value

            where_statement = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            query = f"""
                MATCH (entity:{entity_type})
                {where_statement}
                RETURN entity
                ORDER BY entity.created_at DESC
                SKIP $skip
                LIMIT $limit
            """

            result = await session.run(query, **params)

            entities = []
            async for record in result:
                entities.append(dict(record["entity"]))

            return entities

    # ==================== 关系操作 ====================

    async def create_relationship(
        self,
        relationship_type: str,
        from_ci_id: str,
        to_ci_id: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        创建关系（带 Schema 校验）

        Args:
            relationship_type: 关系类型（如 DEPENDS_ON）
            from_ci_id: 起始实体ID
            to_ci_id: 目标实体ID
            properties: 关系属性

        Returns:
            创建的关系数据
        """
        if properties is None:
            properties = {}

        async with self.driver.session() as session:
            # 1. 查询起始和目标实体的类型
            type_query = """
                MATCH (from {ci_id: $from_ci_id})
                MATCH (to {ci_id: $to_ci_id})
                RETURN labels(from) AS from_labels, labels(to) AS to_labels
            """

            type_result = await session.run(type_query, from_ci_id=from_ci_id, to_ci_id=to_ci_id)
            type_record = await type_result.single()

            if not type_record:
                raise ValueError(f"未找到实体: from={from_ci_id}, to={to_ci_id}")

            # 提取 CMDB_ 开头的标签
            from_labels = [l for l in type_record["from_labels"] if l.startswith("CMDB_")]
            to_labels = [l for l in type_record["to_labels"] if l.startswith("CMDB_")]

            if not from_labels or not to_labels:
                raise ValueError("实体缺少 CMDB 类型标签")

            from_entity_type = from_labels[0]
            to_entity_type = to_labels[0]

            # 2. Schema 校验
            validation = await self.schema_manager.validate_relationship(
                relationship_type, from_entity_type, to_entity_type
            )
            if not validation["valid"]:
                raise ValueError(f"Schema 校验失败: {', '.join(validation['errors'])}")

            # 3. 创建关系
            properties["created_at"] = properties.get("created_at", "datetime()")

            create_query = f"""
                MATCH (from {{ci_id: $from_ci_id}})
                MATCH (to {{ci_id: $to_ci_id}})
                CREATE (from)-[rel:{relationship_type} $properties]->(to)
                RETURN from, to, rel
            """

            result = await session.run(create_query, from_ci_id=from_ci_id, to_ci_id=to_ci_id, properties=properties)
            record = await result.single()

            if record:
                logger.info(f"创建关系成功: {from_ci_id} -[{relationship_type}]-> {to_ci_id}")
                return {
                    "from": dict(record["from"]),
                    "to": dict(record["to"]),
                    "relationship": dict(record["rel"])
                }
            else:
                raise Exception("创建关系失败")

    async def delete_relationship(
        self,
        relationship_type: str,
        from_ci_id: str,
        to_ci_id: str
    ) -> bool:
        """删除关系"""
        async with self.driver.session() as session:
            query = f"""
                MATCH (from {{ci_id: $from_ci_id}})-[rel:{relationship_type}]->(to {{ci_id: $to_ci_id}})
                DELETE rel
                RETURN count(rel) AS deleted_count
            """

            result = await session.run(query, from_ci_id=from_ci_id, to_ci_id=to_ci_id)
            record = await result.single()

            deleted = record["deleted_count"] > 0
            if deleted:
                logger.info(f"删除关系成功: {from_ci_id} -[{relationship_type}]-> {to_ci_id}")

            return deleted

    # ==================== 查询操作 ====================

    async def get_dependencies(
        self,
        ci_id: str,
        direction: str = "downstream",
        depth: int = 3
    ) -> Dict:
        """
        获取依赖图谱

        Args:
            ci_id: 实体ID
            direction: 方向（upstream 上游依赖 | downstream 下游影响 | both 双向）
            depth: 深度

        Returns:
            依赖路径列表
        """
        async with self.driver.session() as session:
            if direction == "downstream":
                # 找出所有依赖该 CI 的下游服务
                query = """
                    MATCH path = (ci {ci_id: $ci_id})<-[:DEPENDS_ON*1..$depth]-(dependent)
                    RETURN path
                """
            elif direction == "upstream":
                # 找出该 CI 依赖的所有上游服务
                query = """
                    MATCH path = (ci {ci_id: $ci_id})-[:DEPENDS_ON*1..$depth]->(dependency)
                    RETURN path
                """
            else:  # both
                query = """
                    MATCH path = (ci {ci_id: $ci_id})-[:DEPENDS_ON*1..$depth]-(related)
                    RETURN path
                """

            result = await session.run(query.replace("$depth", str(depth)), ci_id=ci_id)

            paths = []
            async for record in result:
                path = record["path"]
                paths.append({
                    "nodes": [dict(node) for node in path.nodes],
                    "relationships": [
                        {
                            "type": rel.type,
                            "properties": dict(rel)
                        }
                        for rel in path.relationships
                    ]
                })

            return {"ci_id": ci_id, "direction": direction, "paths": paths}

    async def get_physical_path(self, ci_id: str) -> Optional[Dict]:
        """
        获取完整物理路径（应用→虚拟机→物理服务器→机架→机柜→机房）

        Args:
            ci_id: 应用或数据库的 CI ID

        Returns:
            物理路径信息
        """
        async with self.driver.session() as session:
            query = """
                MATCH path = (app {ci_id: $ci_id})
                  -[:RUNS_ON]->(vm:CMDB_VirtualMachine)
                  <-[:HOSTS]-(physical:CMDB_PhysicalServer)
                  <-[:CONTAINS]-(rack:CMDB_Rack)
                  <-[:CONTAINS]-(cabinet:CMDB_Cabinet)
                  <-[:CONTAINS]-(dc:CMDB_DataCenter)
                RETURN
                  app.name AS application_name,
                  app.ci_type AS application_type,
                  vm.name AS vm_name,
                  vm.ip_address AS vm_ip,
                  physical.name AS server_name,
                  physical.ip_address AS server_ip,
                  rack.name AS rack_name,
                  cabinet.name AS cabinet_name,
                  dc.name AS datacenter_name,
                  dc.city AS city
            """

            result = await session.run(query, ci_id=ci_id)
            record = await result.single()

            if record:
                return dict(record)
            else:
                return None

    async def close(self):
        """关闭数据库连接"""
        await self.driver.close()


# ==================== 全局单例 ====================

_cmdb_service_instance = None


def get_cmdb_service() -> CMDBService:
    """获取 CMDB Service 单例"""
    global _cmdb_service_instance
    if _cmdb_service_instance is None:
        _cmdb_service_instance = CMDBService()
    return _cmdb_service_instance
