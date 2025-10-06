"""
CMDB Schema 管理器
负责将 Schema 定义同步到 Neo4j，并提供校验功能
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from neo4j import AsyncGraphDatabase
from src.shared.core.config import settings
from src.shared.core.logging import get_logger
from .config import CMDB_ENTITY_TYPES, CMDB_RELATIONSHIP_TYPES, CMDB_ENUMS

logger = get_logger(__name__)


class CMDBSchemaManager:
    """CMDB Schema 管理器"""

    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URL,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )

    async def initialize_schema(self):
        """
        初始化 CMDB Schema

        步骤：
        1. 创建 Schema 元数据节点
        2. 创建唯一性约束
        3. 创建索引
        """
        async with self.driver.session() as session:
            # 1. 同步实体类型定义到图数据库
            await self._sync_entity_types(session)

            # 2. 同步关系类型定义到图数据库
            await self._sync_relationship_types(session)

            # 3. 创建约束和索引
            await self._create_constraints_and_indexes(session)

            logger.info("CMDB Schema 初始化完成")

    async def _sync_entity_types(self, session):
        """同步实体类型定义到 Neo4j"""
        logger.info("同步实体类型定义...")

        for entity_type, config in CMDB_ENTITY_TYPES.items():
            # 创建或更新 EntityTypeSchema 节点
            await session.run("""
                MERGE (schema:CMDB_Schema:EntityTypeSchema {entity_type: $entity_type})
                SET schema.label = $label,
                    schema.properties = $properties,
                    schema.required = $required,
                    schema.indexes = $indexes,
                    schema.updated_at = datetime()
            """,
            entity_type=entity_type,
            label=config.get("label", ""),
            properties=config.get("properties", []),
            required=config.get("required", []),
            indexes=config.get("indexes", [])
            )

            logger.debug(f"已同步实体类型: {entity_type}")

    async def _sync_relationship_types(self, session):
        """同步关系类型定义到 Neo4j"""
        logger.info("同步关系类型定义...")

        for rel_type, config in CMDB_RELATIONSHIP_TYPES.items():
            # 创建或更新 RelationshipTypeSchema 节点
            # 将 allowed_pairs (嵌套列表) 转为 JSON 字符串，因为 Neo4j 不支持嵌套集合
            allowed_pairs_json = json.dumps(config.get("allowed_pairs", []))

            await session.run("""
                MERGE (schema:CMDB_Schema:RelationshipTypeSchema {relationship_type: $relationship_type})
                SET schema.label = $label,
                    schema.description = $description,
                    schema.allowed_pairs_json = $allowed_pairs_json,
                    schema.properties = $properties,
                    schema.updated_at = datetime()
            """,
            relationship_type=rel_type,
            label=config.get("label", ""),
            description=config.get("description", ""),
            allowed_pairs_json=allowed_pairs_json,
            properties=config.get("properties", [])
            )

            logger.debug(f"已同步关系类型: {rel_type}")

    async def _create_constraints_and_indexes(self, session):
        """创建约束和索引"""
        logger.info("创建约束和索引...")

        # 为每个实体类型创建唯一性约束和索引
        for entity_type, config in CMDB_ENTITY_TYPES.items():
            # 1. 创建 ci_id 唯一性约束
            try:
                await session.run(f"""
                    CREATE CONSTRAINT {entity_type}_ci_id_unique IF NOT EXISTS
                    FOR (n:{entity_type})
                    REQUIRE n.ci_id IS UNIQUE
                """)
                logger.debug(f"创建约束: {entity_type}.ci_id")
            except Exception as e:
                logger.warning(f"创建约束失败 {entity_type}.ci_id: {e}")

            # 2. 为配置的索引字段创建索引
            for index_field in config.get("indexes", []):
                if index_field != "ci_id":  # ci_id 已经通过约束创建了索引
                    try:
                        await session.run(f"""
                            CREATE INDEX {entity_type}_{index_field}_index IF NOT EXISTS
                            FOR (n:{entity_type})
                            ON (n.{index_field})
                        """)
                        logger.debug(f"创建索引: {entity_type}.{index_field}")
                    except Exception as e:
                        logger.warning(f"创建索引失败 {entity_type}.{index_field}: {e}")

    async def validate_entity(self, entity_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        校验实体数据是否符合 Schema 定义

        Args:
            entity_type: 实体类型（如 CMDB_Server）
            properties: 实体属性

        Returns:
            校验结果：{"valid": True/False, "errors": [...]}
        """
        errors = []

        # 1. 检查实体类型是否存在
        if entity_type not in CMDB_ENTITY_TYPES:
            return {
                "valid": False,
                "errors": [f"未知的实体类型: {entity_type}"]
            }

        config = CMDB_ENTITY_TYPES[entity_type]

        # 2. 检查必填字段
        for required_field in config.get("required", []):
            if required_field not in properties or properties[required_field] is None:
                errors.append(f"缺少必填字段: {required_field}")

        # 3. 检查字段是否在允许的属性列表中
        allowed_properties = config.get("properties", [])
        for prop_name in properties.keys():
            if prop_name not in allowed_properties:
                errors.append(f"未定义的属性: {prop_name} (允许的属性: {allowed_properties})")

        # 4. 检查枚举值（如果适用）
        for prop_name, prop_value in properties.items():
            if prop_name in CMDB_ENUMS and prop_value is not None:
                if prop_value not in CMDB_ENUMS[prop_name]:
                    errors.append(
                        f"字段 {prop_name} 的值 '{prop_value}' 不在允许的枚举值中: {CMDB_ENUMS[prop_name]}"
                    )

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    async def validate_relationship(
        self,
        relationship_type: str,
        from_entity_type: str,
        to_entity_type: str
    ) -> Dict[str, Any]:
        """
        校验关系是否符合 Schema 定义

        Args:
            relationship_type: 关系类型（如 DEPENDS_ON）
            from_entity_type: 起始实体类型
            to_entity_type: 目标实体类型

        Returns:
            校验结果：{"valid": True/False, "errors": [...]}
        """
        errors = []

        # 1. 检查关系类型是否存在
        if relationship_type not in CMDB_RELATIONSHIP_TYPES:
            return {
                "valid": False,
                "errors": [f"未知的关系类型: {relationship_type}"]
            }

        config = CMDB_RELATIONSHIP_TYPES[relationship_type]

        # 2. 检查实体对是否允许
        allowed_pairs = config.get("allowed_pairs", [])
        if (from_entity_type, to_entity_type) not in allowed_pairs:
            errors.append(
                f"不允许的关系: {from_entity_type} -[{relationship_type}]-> {to_entity_type}. "
                f"允许的配对: {allowed_pairs}"
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    async def get_entity_schema(self, entity_type: str) -> Optional[Dict]:
        """获取实体类型的 Schema 定义"""
        return CMDB_ENTITY_TYPES.get(entity_type)

    async def get_relationship_schema(self, relationship_type: str) -> Optional[Dict]:
        """获取关系类型的 Schema 定义"""
        return CMDB_RELATIONSHIP_TYPES.get(relationship_type)

    async def get_all_entity_types(self) -> List[Dict]:
        """获取所有实体类型"""
        return [
            {
                "entity_type": entity_type,
                "label": config.get("label", ""),
                "properties": config.get("properties", []),
                "required": config.get("required", []),
            }
            for entity_type, config in CMDB_ENTITY_TYPES.items()
        ]

    async def get_all_relationship_types(self) -> List[Dict]:
        """获取所有关系类型"""
        return [
            {
                "relationship_type": rel_type,
                "label": config.get("label", ""),
                "description": config.get("description", ""),
                "allowed_pairs": config.get("allowed_pairs", []),
            }
            for rel_type, config in CMDB_RELATIONSHIP_TYPES.items()
        ]

    async def query_schema_from_graph(self) -> Dict:
        """从 Neo4j 图数据库中查询 Schema 定义"""
        async with self.driver.session() as session:
            # 查询实体类型 Schema
            entity_result = await session.run("""
                MATCH (schema:EntityTypeSchema)
                RETURN schema.entity_type AS entity_type,
                       schema.label AS label,
                       schema.properties AS properties,
                       schema.required AS required,
                       schema.indexes AS indexes
                ORDER BY entity_type
            """)

            entity_types = []
            async for record in entity_result:
                entity_types.append({
                    "entity_type": record["entity_type"],
                    "label": record["label"],
                    "properties": record["properties"],
                    "required": record["required"],
                    "indexes": record["indexes"],
                })

            # 查询关系类型 Schema
            rel_result = await session.run("""
                MATCH (schema:RelationshipTypeSchema)
                RETURN schema.relationship_type AS relationship_type,
                       schema.label AS label,
                       schema.description AS description,
                       schema.allowed_pairs_json AS allowed_pairs_json,
                       schema.properties AS properties
                ORDER BY relationship_type
            """)

            relationship_types = []
            async for record in rel_result:
                # 将 JSON 字符串转回列表
                allowed_pairs = json.loads(record["allowed_pairs_json"]) if record["allowed_pairs_json"] else []
                relationship_types.append({
                    "relationship_type": record["relationship_type"],
                    "label": record["label"],
                    "description": record["description"],
                    "allowed_pairs": allowed_pairs,
                    "properties": record["properties"],
                })

            return {
                "entity_types": entity_types,
                "relationship_types": relationship_types
            }

    async def export_schema_to_cypher(self, output_file: str = "cmdb_schema_init.cypher"):
        """
        导出 Schema 为 Cypher 脚本

        用于：
        1. 版本控制
        2. 其他环境初始化
        3. 灾难恢复
        """
        cypher_lines = [
            "// ==================== CMDB Schema 初始化脚本 ====================",
            "// 自动生成时间: " + str(datetime.now()),
            "",
            "// ==================== 创建实体类型 Schema ====================",
        ]

        for entity_type, config in CMDB_ENTITY_TYPES.items():
            cypher_lines.append(f"""
MERGE (schema:CMDB_Schema:EntityTypeSchema {{entity_type: '{entity_type}'}})
SET schema.label = '{config.get('label', '')}',
    schema.properties = {config.get('properties', [])},
    schema.required = {config.get('required', [])},
    schema.indexes = {config.get('indexes', [])};
""")

        cypher_lines.append("\n// ==================== 创建关系类型 Schema ====================")

        for rel_type, config in CMDB_RELATIONSHIP_TYPES.items():
            allowed_pairs_json = json.dumps(config.get('allowed_pairs', []))
            cypher_lines.append(f"""
MERGE (schema:CMDB_Schema:RelationshipTypeSchema {{relationship_type: '{rel_type}'}})
SET schema.label = '{config.get('label', '')}',
    schema.description = '{config.get('description', '')}',
    schema.allowed_pairs_json = '{allowed_pairs_json}',
    schema.properties = {config.get('properties', [])};
""")

        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cypher_lines))

        logger.info(f"Schema 已导出到: {output_file}")
        return output_file

    async def close(self):
        """关闭数据库连接"""
        await self.driver.close()


# ==================== 全局单例 ====================

_schema_manager_instance = None


def get_schema_manager() -> CMDBSchemaManager:
    """获取 Schema 管理器单例"""
    global _schema_manager_instance
    if _schema_manager_instance is None:
        _schema_manager_instance = CMDBSchemaManager()
    return _schema_manager_instance


# ==================== 初始化脚本 ====================

async def init_cmdb_schema():
    """
    初始化 CMDB Schema

    使用方式:
    python -m src.apps.cmdb.schema_manager
    """
    from datetime import datetime

    logger.info("开始初始化 CMDB Schema...")

    manager = get_schema_manager()

    try:
        # 1. 同步 Schema 到 Neo4j
        await manager.initialize_schema()

        # 2. 查询并验证
        schema = await manager.query_schema_from_graph()
        logger.info(f"已加载 {len(schema['entity_types'])} 个实体类型")
        logger.info(f"已加载 {len(schema['relationship_types'])} 个关系类型")

        # 3. 导出 Cypher 脚本
        script_file = await manager.export_schema_to_cypher()
        logger.info(f"Schema 脚本已导出: {script_file}")

        logger.info("✅ CMDB Schema 初始化成功")

    except Exception as e:
        logger.error(f"❌ CMDB Schema 初始化失败: {e}", exc_info=True)
        raise
    finally:
        await manager.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_cmdb_schema())
