"""SOP服务层 - 简化的纯异步实现"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, func, case, distinct

from src.apps.sop.models import SOPTemplate
from src.shared.db.models import now_shanghai
from src.shared.core.logging import get_logger
from src.apps.sop.schema import SOPTemplateCreate, SOPTemplateUpdate, SOPQueryParams
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode

logger = get_logger(__name__)


class SOPService:
    """SOP服务 - 清晰的单一职责实现"""
    
    async def create_sop(
        self, 
        db: AsyncSession, 
        sop_data: SOPTemplateCreate
    ) -> SOPTemplate:
        """创建SOP模板"""
        async with db.begin():
            # 业务验证
            result = await db.execute(
                select(SOPTemplate).where(SOPTemplate.sop_id == sop_data.sop_id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                raise BusinessException(f"SOP template with ID {sop_data.sop_id} already exists", ResponseCode.CONFLICT)
            
            # 转换数据
            data = sop_data.dict()
            
            # 设置默认值
            data.setdefault('create_by', 'system')
            data.setdefault('create_time', now_shanghai())
            data.setdefault('update_time', now_shanghai())
            
            logger.info(f"Creating SOP template: {sop_data.sop_id}")
            instance = SOPTemplate(**data)
            db.add(instance)
            await db.flush()
            await db.refresh(instance)
            return instance
    
    async def get_sop_by_id(
        self, 
        db: AsyncSession, 
        sop_id: str
    ) -> Optional[SOPTemplate]:
        """根据ID获取SOP模板"""
        result = await db.execute(
            select(SOPTemplate).where(SOPTemplate.sop_id == sop_id)
        )
        return result.scalar_one_or_none()
    
    async def list_sops(
        self, 
        db: AsyncSession, 
        params: SOPQueryParams
    ) -> Tuple[List[SOPTemplate], int]:
        """列出SOP模板"""
        # 构建查询
        query = select(SOPTemplate)
        conditions = []
        
        # 搜索条件
        if params.search:
            conditions.append(
                SOPTemplate.sop_title.contains(params.search) |
                SOPTemplate.sop_id.contains(params.search)
            )
        
        
        # 应用条件
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序和分页
        query = query.order_by(SOPTemplate.create_time.desc())
        query = query.offset(params.offset).limit(params.limit)
        result = await db.execute(query)
        templates = list(result.scalars().all())
        
        # 计算总数
        count_query = select(func.count(SOPTemplate.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        return templates, total
    
    async def update_sop(
        self, 
        db: AsyncSession, 
        sop_id: str, 
        sop_data: SOPTemplateUpdate
    ) -> Optional[SOPTemplate]:
        """更新SOP模板"""
        async with db.begin():
            # 检查是否存在
            result = await db.execute(
                select(SOPTemplate).where(SOPTemplate.sop_id == sop_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                raise BusinessException(f"SOP template with ID {sop_id} not found", ResponseCode.NOT_FOUND)
            
            # 转换数据
            data = sop_data.dict(exclude_unset=True)
            
            # 移除不可更新字段
            data.pop('sop_id', None)
            data.pop('create_time', None)
            data.pop('create_by', None)
            data['update_by'] = 'system'
            data['update_time'] = now_shanghai()
            
            logger.info(f"Updating SOP template: {sop_id}")
            await db.execute(
                update(SOPTemplate).where(SOPTemplate.sop_id == sop_id).values(**data)
            )
            
            # 返回更新后的数据
            result = await db.execute(
                select(SOPTemplate).where(SOPTemplate.sop_id == sop_id)
            )
            return result.scalar_one_or_none()
    
    async def delete_sop(
        self, 
        db: AsyncSession, 
        sop_id: str
    ) -> bool:
        """删除SOP模板"""
        async with db.begin():
            # 检查是否存在
            result = await db.execute(
                select(SOPTemplate).where(SOPTemplate.sop_id == sop_id)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                return False
            
            logger.info(f"Deleting SOP template: {sop_id}")
            result = await db.execute(
                delete(SOPTemplate).where(SOPTemplate.sop_id == sop_id)
            )
            return result.rowcount > 0
    
    # ========== 旧格式方法 - 向后兼容 ==========
    async def get_teams(self, db: AsyncSession) -> List[str]:  
        """获取所有团队 - 字符串数组格式（向后兼容）"""
        result = await db.execute(
            select(distinct(SOPTemplate.team_name)).where(
                SOPTemplate.team_name.isnot(None)
            )
        )
        return [row[0] for row in result.fetchall()]
    
    # ========== 新格式方法 - 统一标准格式 ==========
    async def get_team_options(self, db: AsyncSession):
        """获取团队选项 - 返回原始查询结果"""
        return await db.execute(
            select(
                SOPTemplate.team_name.label('value'),
                SOPTemplate.team_name.label('label'),
                func.count(SOPTemplate.id).label('count')
            )
            .where(SOPTemplate.team_name.isnot(None))
            .group_by(SOPTemplate.team_name)
        )
    
    async def get_severity_options(self, db: AsyncSession):
        """获取严重程度选项 - 返回原始查询结果"""
        return await db.execute(
            select(
                SOPTemplate.sop_severity.label('value'),
                SOPTemplate.sop_severity.label('label'),
                func.count(SOPTemplate.id).label('count')
            )
            .where(SOPTemplate.sop_severity.isnot(None))
            .group_by(SOPTemplate.sop_severity)
        )
    
    # ========== 优化列表查询 - 使用BaseModel批量转换 ==========
    async def list_sops_dict(
        self, 
        db: AsyncSession, 
        params: SOPQueryParams
    ) -> Tuple[List[Dict[str, Any]], int]:
        """列出SOP模板 - 返回字典格式"""
        templates, total = await self.list_sops(db, params)
        
        # 使用BaseModel的批量转换方法
        from src.shared.db.models import BaseModel
        template_data = BaseModel.bulk_to_dict(templates)
        
        return template_data, total


# 全局实例
sop_service = SOPService()