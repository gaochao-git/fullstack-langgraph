"""OpenAPI MCP配置服务"""

from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from src.apps.mcp.models import OpenAPIMCPConfig
from src.apps.mcp.schema import OpenAPIMCPConfigCreate, OpenAPIMCPConfigUpdate
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class OpenAPIMCPConfigService:
    """OpenAPI MCP配置服务类"""
    
    async def create_config(
        self, 
        db: AsyncSession, 
        config_data: OpenAPIMCPConfigCreate
    ) -> OpenAPIMCPConfig:
        """创建OpenAPI MCP配置"""
        try:
            # 检查唯一约束：mcp_server_prefix + mcp_tool_name 不能重复
            stmt = select(OpenAPIMCPConfig).where(
                and_(
                    OpenAPIMCPConfig.mcp_server_prefix == config_data.mcp_server_prefix,
                    OpenAPIMCPConfig.mcp_tool_name == config_data.mcp_tool_name,
                    OpenAPIMCPConfig.is_deleted == 0
                )
            )
            existing = await db.execute(stmt)
            if existing.scalars().first():
                raise ValueError(f"配置已存在：{config_data.mcp_server_prefix}/{config_data.mcp_tool_name}")
            
            # 创建新配置
            config = OpenAPIMCPConfig(
                mcp_server_prefix=config_data.mcp_server_prefix,
                mcp_tool_name=config_data.mcp_tool_name,
                mcp_tool_enabled=config_data.mcp_tool_enabled,
                openapi_schema=config_data.openapi_schema,
                auth_config=config_data.auth_config,
                extra_config=config_data.extra_config,
                create_by=config_data.create_by,
                is_deleted=0
            )
            
            db.add(config)
            await db.commit()
            await db.refresh(config)
            
            logger.info(f"创建OpenAPI MCP配置成功: {config.id}")
            return config
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建OpenAPI MCP配置失败: {str(e)}")
            raise
    
    async def get_config(self, db: AsyncSession, config_id: int) -> Optional[OpenAPIMCPConfig]:
        """获取单个配置"""
        try:
            stmt = select(OpenAPIMCPConfig).where(
                and_(
                    OpenAPIMCPConfig.id == config_id,
                    OpenAPIMCPConfig.is_deleted == 0
                )
            )
            result = await db.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"获取OpenAPI MCP配置失败: {str(e)}")
            raise
    
    async def list_configs(
        self,
        db: AsyncSession,
        offset: int = 0,
        limit: int = 10,
        mcp_server_prefix: Optional[str] = None,
        mcp_tool_enabled: Optional[int] = None
    ) -> Tuple[List[OpenAPIMCPConfig], int]:
        """获取配置列表"""
        try:
            # 构建查询条件
            conditions = [OpenAPIMCPConfig.is_deleted == 0]
            
            if mcp_server_prefix:
                conditions.append(OpenAPIMCPConfig.mcp_server_prefix.like(f"%{mcp_server_prefix}%"))
            
            if mcp_tool_enabled is not None:
                conditions.append(OpenAPIMCPConfig.mcp_tool_enabled == mcp_tool_enabled)
            
            where_clause = and_(*conditions)
            
            # 获取总数
            count_stmt = select(func.count(OpenAPIMCPConfig.id)).where(where_clause)
            total_result = await db.execute(count_stmt)
            total = total_result.scalar()
            
            # 获取数据
            stmt = (
                select(OpenAPIMCPConfig)
                .where(where_clause)
                .order_by(OpenAPIMCPConfig.create_time.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await db.execute(stmt)
            configs = result.scalars().all()
            
            return list(configs), total
            
        except Exception as e:
            logger.error(f"获取OpenAPI MCP配置列表失败: {str(e)}")
            raise
    
    async def update_config(
        self,
        db: AsyncSession,
        config_id: int,
        config_data: OpenAPIMCPConfigUpdate
    ) -> Optional[OpenAPIMCPConfig]:
        """更新配置"""
        try:
            # 获取现有配置
            config = await self.get_config(db, config_id)
            if not config:
                return None
            
            # 如果更新了前缀或工具名，检查唯一约束
            if config_data.mcp_server_prefix or config_data.mcp_tool_name:
                new_prefix = config_data.mcp_server_prefix or config.mcp_server_prefix
                new_tool_name = config_data.mcp_tool_name or config.mcp_tool_name
                
                # 检查是否与其他配置冲突
                if new_prefix != config.mcp_server_prefix or new_tool_name != config.mcp_tool_name:
                    stmt = select(OpenAPIMCPConfig).where(
                        and_(
                            OpenAPIMCPConfig.mcp_server_prefix == new_prefix,
                            OpenAPIMCPConfig.mcp_tool_name == new_tool_name,
                            OpenAPIMCPConfig.is_deleted == 0,
                            OpenAPIMCPConfig.id != config_id
                        )
                    )
                    existing = await db.execute(stmt)
                    if existing.scalars().first():
                        raise ValueError(f"配置已存在：{new_prefix}/{new_tool_name}")
            
            # 更新字段
            update_data = config_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(config, field, value)
            
            await db.commit()
            await db.refresh(config)
            
            logger.info(f"更新OpenAPI MCP配置成功: {config.id}")
            return config
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新OpenAPI MCP配置失败: {str(e)}")
            raise
    
    async def delete_config(self, db: AsyncSession, config_id: int) -> bool:
        """软删除配置"""
        try:
            config = await self.get_config(db, config_id)
            if not config:
                return False
            
            config.is_deleted = 1
            await db.commit()
            
            logger.info(f"删除OpenAPI MCP配置成功: {config_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"删除OpenAPI MCP配置失败: {str(e)}")
            raise
    
    async def toggle_enable(self, db: AsyncSession, config_id: int, enabled: bool) -> Optional[OpenAPIMCPConfig]:
        """启用/禁用配置"""
        try:
            config = await self.get_config(db, config_id)
            if not config:
                return None
            
            config.mcp_tool_enabled = 1 if enabled else 0
            await db.commit()
            await db.refresh(config)
            
            logger.info(f"切换OpenAPI MCP配置状态成功: {config_id} -> {enabled}")
            return config
            
        except Exception as e:
            await db.rollback()
            logger.error(f"切换OpenAPI MCP配置状态失败: {str(e)}")
            raise
    
    async def get_enabled_configs_by_prefix(self, db: AsyncSession, prefix: str) -> List[OpenAPIMCPConfig]:
        """根据前缀获取启用的配置"""
        try:
            stmt = select(OpenAPIMCPConfig).where(
                and_(
                    OpenAPIMCPConfig.mcp_server_prefix == prefix,
                    OpenAPIMCPConfig.mcp_tool_enabled == 1,
                    OpenAPIMCPConfig.is_deleted == 0
                )
            ).order_by(OpenAPIMCPConfig.create_time.desc())
            
            result = await db.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"获取启用配置失败: {str(e)}")
            raise
    
    async def get_all_enabled_configs(self, db: AsyncSession) -> List[OpenAPIMCPConfig]:
        """获取所有启用的配置"""
        try:
            stmt = select(OpenAPIMCPConfig).where(
                and_(
                    OpenAPIMCPConfig.mcp_tool_enabled == 1,
                    OpenAPIMCPConfig.is_deleted == 0
                )
            ).order_by(OpenAPIMCPConfig.mcp_server_prefix, OpenAPIMCPConfig.create_time.desc())
            
            result = await db.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"获取所有启用配置失败: {str(e)}")
            raise
    
    async def get_prefixes(self, db: AsyncSession) -> List[str]:
        """获取所有使用的前缀"""
        try:
            stmt = select(OpenAPIMCPConfig.mcp_server_prefix).where(
                and_(
                    OpenAPIMCPConfig.mcp_tool_enabled == 1,
                    OpenAPIMCPConfig.is_deleted == 0
                )
            ).distinct()
            
            result = await db.execute(stmt)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"获取前缀列表失败: {str(e)}")
            raise