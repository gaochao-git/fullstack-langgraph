"""扫描配置服务层"""

import json
import uuid
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func

from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from .models import ScanConfig
from .schema import ScanConfigCreate, ScanConfigUpdate, ScanExample

logger = get_logger(__name__)


class ScanConfigService:
    """扫描配置服务"""

    async def create_config(
        self,
        db: AsyncSession,
        config_data: ScanConfigCreate,
        create_by: str
    ) -> Dict[str, Any]:
        """创建扫描配置"""
        async with db.begin():
            # 生成配置ID
            config_id = f"config_{uuid.uuid4().hex[:12]}"

            # 如果设置为默认配置，先取消其他默认配置
            if config_data.is_default:
                await db.execute(
                    update(ScanConfig)
                    .where(ScanConfig.is_default == 1)
                    .values(is_default=0, update_time=now_shanghai())
                )

            # 转换examples为JSON字符串
            examples_json = None
            if config_data.examples:
                examples_json = json.dumps([ex.model_dump() for ex in config_data.examples], ensure_ascii=False)

            # 创建配置记录
            config = ScanConfig(
                config_id=config_id,
                config_name=config_data.config_name,
                config_description=config_data.config_description,
                prompt_description=config_data.prompt_description,
                examples_config=examples_json,
                is_default=1 if config_data.is_default else 0,
                status='active',
                create_by=create_by,
                create_time=now_shanghai(),
                update_time=now_shanghai()
            )

            db.add(config)
            await db.flush()
            await db.refresh(config)

            logger.info(f"创建扫描配置成功: {config_id}, 创建人: {create_by}")

            return self._config_to_dict(config)

    async def update_config(
        self,
        db: AsyncSession,
        config_id: str,
        config_data: ScanConfigUpdate,
        update_by: str
    ) -> Dict[str, Any]:
        """更新扫描配置"""
        async with db.begin():
            # 查询配置
            result = await db.execute(
                select(ScanConfig).where(ScanConfig.config_id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                raise BusinessException(ResponseCode.NOT_FOUND, f"配置不存在: {config_id}")

            # 如果设置为默认配置，先取消其他默认配置
            if config_data.is_default is True:
                await db.execute(
                    update(ScanConfig)
                    .where(and_(
                        ScanConfig.is_default == 1,
                        ScanConfig.config_id != config_id
                    ))
                    .values(is_default=0, update_time=now_shanghai())
                )

            # 更新字段
            if config_data.config_name is not None:
                config.config_name = config_data.config_name
            if config_data.config_description is not None:
                config.config_description = config_data.config_description
            if config_data.prompt_description is not None:
                config.prompt_description = config_data.prompt_description
            if config_data.examples is not None:
                config.examples_config = json.dumps(
                    [ex.model_dump() for ex in config_data.examples], ensure_ascii=False
                )
            if config_data.is_default is not None:
                config.is_default = 1 if config_data.is_default else 0
            if config_data.status is not None:
                config.status = config_data.status

            config.update_by = update_by
            config.update_time = now_shanghai()

            await db.flush()

            logger.info(f"更新扫描配置成功: {config_id}, 更新人: {update_by}")

            return self._config_to_dict(config)

    async def delete_config(
        self,
        db: AsyncSession,
        config_id: str
    ) -> None:
        """删除扫描配置"""
        async with db.begin():
            result = await db.execute(
                select(ScanConfig).where(ScanConfig.config_id == config_id)
            )
            config = result.scalar_one_or_none()

            if not config:
                raise BusinessException(ResponseCode.NOT_FOUND, f"配置不存在: {config_id}")

            if config.is_default == 1:
                raise BusinessException(ResponseCode.BUSINESS_ERROR, "默认配置不能删除")

            await db.delete(config)

            logger.info(f"删除扫描配置成功: {config_id}")

    async def get_config(
        self,
        db: AsyncSession,
        config_id: str
    ) -> Dict[str, Any]:
        """获取配置详情"""
        result = await db.execute(
            select(ScanConfig).where(ScanConfig.config_id == config_id)
        )
        config = result.scalar_one_or_none()

        if not config:
            raise BusinessException(ResponseCode.NOT_FOUND, f"配置不存在: {config_id}")

        return self._config_to_dict(config)

    async def get_default_config(
        self,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """获取默认配置"""
        result = await db.execute(
            select(ScanConfig).where(
                and_(ScanConfig.is_default == 1, ScanConfig.status == 'active')
            )
        )
        config = result.scalar_one_or_none()

        if config:
            return self._config_to_dict(config)
        return None

    async def list_configs(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        config_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """查询配置列表"""
        # 构建查询条件
        conditions = []
        if config_name:
            conditions.append(ScanConfig.config_name.contains(config_name))
        if status:
            conditions.append(ScanConfig.status == status)

        # 查询总数
        count_query = select(func.count(ScanConfig.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))

        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # 分页查询
        query = select(ScanConfig).order_by(
            ScanConfig.is_default.desc(),
            ScanConfig.create_time.desc()
        )
        if conditions:
            query = query.where(and_(*conditions))

        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)
        configs = result.scalars().all()

        config_list = [self._config_to_dict(config) for config in configs]

        return config_list, total

    def _config_to_dict(self, config: ScanConfig) -> Dict[str, Any]:
        """将配置对象转换为字典"""
        # 解析examples
        examples = None
        if config.examples_config:
            try:
                examples_data = json.loads(config.examples_config)
                examples = [ScanExample(**ex) for ex in examples_data]
            except:
                pass

        return {
            "config_id": config.config_id,
            "config_name": config.config_name,
            "config_description": config.config_description,
            "prompt_description": config.prompt_description,
            "examples": examples,
            "is_default": config.is_default == 1,
            "status": config.status,
            "create_by": config.create_by,
            "update_by": config.update_by,
            "create_time": config.create_time.strftime('%Y-%m-%d %H:%M:%S') if config.create_time else None,
            "update_time": config.update_time.strftime('%Y-%m-%d %H:%M:%S') if config.update_time else None
        }


# 创建服务实例
scan_config_service = ScanConfigService()
