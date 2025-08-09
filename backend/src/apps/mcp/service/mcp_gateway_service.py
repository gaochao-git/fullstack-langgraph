"""
MCP Gateway配置服务层
"""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, or_, and_
from sqlalchemy.exc import IntegrityError
import json
import uuid

from src.apps.mcp.models import MCPConfig
from src.apps.mcp.schema import (
    MCPGatewayConfigCreate, MCPGatewayConfigUpdate, MCPGatewayConfigQueryParams
)
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class MCPGatewayConfigService:
    """MCP Gateway配置服务"""

    async def create_config(
        self, 
        db: AsyncSession, 
        config_data: MCPGatewayConfigCreate
    ) -> MCPConfig:
        """创建MCP Gateway配置"""
        try:
            # 检查名称是否已存在
            existing = await db.execute(
                select(MCPConfig).where(
                    and_(
                        MCPConfig.tenant == config_data.tenant,
                        MCPConfig.name == config_data.name,
                        MCPConfig.is_deleted == 0
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise BusinessException(
                    f"配置名称 '{config_data.name}' 在租户 '{config_data.tenant}' 中已存在",
                    ResponseCode.BAD_REQUEST
                )

            # 创建新配置
            new_config = MCPConfig(
                config_id=str(uuid.uuid4()),
                name=config_data.name,
                tenant=config_data.tenant,
                routers=json.dumps(config_data.routers or [], ensure_ascii=False),
                servers=json.dumps(config_data.servers or [], ensure_ascii=False),
                tools=json.dumps(config_data.tools or [], ensure_ascii=False),
                prompts=json.dumps(config_data.prompts or [], ensure_ascii=False),
                mcp_servers=json.dumps(config_data.mcp_servers or [], ensure_ascii=False),
                create_by=config_data.create_by
            )

            db.add(new_config)
            await db.commit()
            await db.refresh(new_config)

            logger.info(f"创建MCP Gateway配置成功: {config_data.name}")
            return new_config

        except IntegrityError as e:
            await db.rollback()
            logger.error(f"创建MCP Gateway配置失败，数据完整性错误: {str(e)}")
            raise BusinessException("配置名称已存在", ResponseCode.BAD_REQUEST)
        except Exception as e:
            await db.rollback()
            logger.error(f"创建MCP Gateway配置失败: {str(e)}")
            raise BusinessException("创建配置失败", ResponseCode.INTERNAL_ERROR)

    async def get_config_by_id(self, db: AsyncSession, config_id: int) -> Optional[MCPConfig]:
        """根据ID获取配置"""
        result = await db.execute(
            select(MCPConfig).where(
                and_(MCPConfig.id == config_id, MCPConfig.is_deleted == 0)
            )
        )
        return result.scalar_one_or_none()

    async def get_config_by_name_tenant(
        self, 
        db: AsyncSession, 
        name: str, 
        tenant: str
    ) -> Optional[MCPConfig]:
        """根据名称和租户获取配置"""
        result = await db.execute(
            select(MCPConfig).where(
                and_(
                    MCPConfig.name == name,
                    MCPConfig.tenant == tenant,
                    MCPConfig.is_deleted == 0
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_configs(
        self, 
        db: AsyncSession, 
        params: MCPGatewayConfigQueryParams
    ) -> Tuple[List[MCPConfig], int]:
        """获取配置列表"""
        try:
            # 构建查询条件
            conditions = [MCPConfig.is_deleted == 0]
            
            if params.name:
                conditions.append(MCPConfig.name.contains(params.name))
            
            if params.tenant:
                conditions.append(MCPConfig.tenant == params.tenant)
            
            if params.create_by:
                conditions.append(MCPConfig.create_by.contains(params.create_by))

            # 查询总数
            count_query = select(func.count(MCPConfig.id)).where(and_(*conditions))
            total_result = await db.execute(count_query)
            total = total_result.scalar()

            # 查询数据
            query = (
                select(MCPConfig)
                .where(and_(*conditions))
                .order_by(MCPConfig.update_time.desc())
                .limit(params.limit)
                .offset(params.offset)
            )
            
            result = await db.execute(query)
            configs = result.scalars().all()
            
            return list(configs), total

        except Exception as e:
            logger.error(f"获取MCP Gateway配置列表失败: {str(e)}")
            raise BusinessException("获取配置列表失败", ResponseCode.INTERNAL_ERROR)

    async def update_config(
        self, 
        db: AsyncSession, 
        config_id: int, 
        config_data: MCPGatewayConfigUpdate
    ) -> Optional[MCPConfig]:
        """更新配置"""
        try:
            # 检查配置是否存在
            config = await self.get_config_by_id(db, config_id)
            if not config:
                return None

            # 如果要修改名称或租户，检查是否冲突
            if config_data.name or config_data.tenant:
                new_name = config_data.name or config.name
                new_tenant = config_data.tenant or config.tenant
                
                # 只有当名称或租户确实发生变化时才检查冲突
                if new_name != config.name or new_tenant != config.tenant:
                    existing = await db.execute(
                        select(MCPConfig).where(
                            and_(
                                MCPConfig.tenant == new_tenant,
                                MCPConfig.name == new_name,
                                MCPConfig.id != config_id,
                                MCPConfig.is_deleted == 0
                            )
                        )
                    )
                    if existing.scalar_one_or_none():
                        raise BusinessException(
                            f"配置名称 '{new_name}' 在租户 '{new_tenant}' 中已存在",
                            ResponseCode.BAD_REQUEST
                        )

            # 构建更新数据
            update_data = {}
            if config_data.name is not None:
                update_data['name'] = config_data.name
            if config_data.tenant is not None:
                update_data['tenant'] = config_data.tenant
            if config_data.routers is not None:
                update_data['routers'] = json.dumps(config_data.routers, ensure_ascii=False)
            if config_data.servers is not None:
                update_data['servers'] = json.dumps(config_data.servers, ensure_ascii=False)
            if config_data.tools is not None:
                update_data['tools'] = json.dumps(config_data.tools, ensure_ascii=False)
            if config_data.prompts is not None:
                update_data['prompts'] = json.dumps(config_data.prompts, ensure_ascii=False)
            if config_data.mcp_servers is not None:
                update_data['mcp_servers'] = json.dumps(config_data.mcp_servers, ensure_ascii=False)
            if config_data.update_by is not None:
                update_data['update_by'] = config_data.update_by

            if update_data:
                await db.execute(
                    update(MCPConfig)
                    .where(MCPConfig.id == config_id)
                    .values(**update_data)
                )
                await db.commit()
                
                # 重新获取更新后的配置
                config = await self.get_config_by_id(db, config_id)

            logger.info(f"更新MCP Gateway配置成功: {config_id}")
            return config

        except BusinessException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"更新MCP Gateway配置失败: {str(e)}")
            raise BusinessException("更新配置失败", ResponseCode.INTERNAL_ERROR)

    async def delete_config(self, db: AsyncSession, config_id: int) -> bool:
        """软删除配置"""
        try:
            config = await self.get_config_by_id(db, config_id)
            if not config:
                return False

            await db.execute(
                update(MCPConfig)
                .where(MCPConfig.id == config_id)
                .values(is_deleted=1)
            )
            await db.commit()

            logger.info(f"删除MCP Gateway配置成功: {config_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"删除MCP Gateway配置失败: {str(e)}")
            raise BusinessException("删除配置失败", ResponseCode.INTERNAL_ERROR)

    async def get_all_active_configs(self, db: AsyncSession) -> List[MCPConfig]:
        """获取所有激活的配置"""
        try:
            result = await db.execute(
                select(MCPConfig)
                .where(MCPConfig.is_deleted == 0)
                .order_by(MCPConfig.update_time.desc())
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"获取所有激活配置失败: {str(e)}")
            raise BusinessException("获取配置失败", ResponseCode.INTERNAL_ERROR)

    async def get_configs_by_tenant(self, db: AsyncSession, tenant: str) -> List[MCPConfig]:
        """根据租户获取配置"""
        try:
            result = await db.execute(
                select(MCPConfig)
                .where(and_(MCPConfig.tenant == tenant, MCPConfig.is_deleted == 0))
                .order_by(MCPConfig.update_time.desc())
            )
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"根据租户获取配置失败: {str(e)}")
            raise BusinessException("获取配置失败", ResponseCode.INTERNAL_ERROR)


# 创建服务实例
mcp_gateway_service = MCPGatewayConfigService()