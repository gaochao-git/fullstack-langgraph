"""SOP服务层 - 简化的纯异步实现"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.sop.dao.sop_dao import SOPDAO
from src.apps.sop.models import SOPTemplate
from src.shared.db.transaction import transactional
from src.shared.core.logging import get_logger
from src.apps.sop.schema.sop import SOPTemplateCreate, SOPTemplateUpdate, SOPQueryParams

logger = get_logger(__name__)


class SOPService:
    """SOP服务 - 清晰的单一职责实现"""
    
    def __init__(self):
        self._dao = SOPDAO()
    
    @transactional()
    async def create_sop(
        self, 
        session: AsyncSession, 
        sop_data: SOPTemplateCreate
    ) -> SOPTemplate:
        """创建SOP模板"""
        # 业务验证
        existing = await self._dao.get_by_sop_id(session, sop_data.sop_id)
        if existing:
            raise ValueError(f"SOP template with ID {sop_data.sop_id} already exists")
        
        # 转换数据
        data = sop_data.dict()
        if 'steps' in data:
            data['sop_steps'] = data.pop('steps')
        
        # 设置默认值
        data.setdefault('create_by', 'system')
        
        logger.info(f"Creating SOP template: {sop_data.sop_id}")
        return await self._dao.create(session, data)
    
    async def get_sop_by_id(
        self, 
        session: AsyncSession, 
        sop_id: str
    ) -> Optional[SOPTemplate]:
        """根据ID获取SOP模板"""
        return await self._dao.get_by_sop_id(session, sop_id)
    
    async def list_sops(
        self, 
        session: AsyncSession, 
        params: SOPQueryParams
    ) -> Tuple[List[SOPTemplate], int]:
        """列出SOP模板"""
        # 构建过滤条件
        filters = {}
        if params.category:
            filters['sop_category'] = params.category
        if params.severity:
            filters['sop_severity'] = params.severity
        if params.team_name:
            filters['team_name'] = params.team_name
        
        # 搜索功能
        if params.search:
            templates = await self._dao.search_by_title(
                session,
                params.search,
                team_name=params.team_name,
                limit=params.limit,
                offset=params.offset
            )
            # 获取搜索总数
            all_results = await self._dao.search_by_title(
                session, 
                params.search, 
                team_name=params.team_name
            )
            total = len(all_results)
        else:
            # 普通查询
            templates = await self._dao.get_list(
                session,
                filters=filters if filters else None,
                limit=params.limit,
                offset=params.offset,
                order_by='create_time'
            )
            total = await self._dao.count(session, filters=filters if filters else None)
        
        return templates, total
    
    @transactional()
    async def update_sop(
        self, 
        session: AsyncSession, 
        sop_id: str, 
        sop_data: SOPTemplateUpdate
    ) -> Optional[SOPTemplate]:
        """更新SOP模板"""
        # 检查是否存在
        existing = await self._dao.get_by_sop_id(session, sop_id)
        if not existing:
            raise ValueError(f"SOP template with ID {sop_id} not found")
        
        # 转换数据
        data = sop_data.dict(exclude_unset=True)
        if 'steps' in data:
            data['sop_steps'] = data.pop('steps')
        
        # 移除不可更新字段
        data.pop('sop_id', None)
        data.pop('create_time', None)
        data.pop('create_by', None)
        data['update_by'] = 'system'
        
        logger.info(f"Updating SOP template: {sop_id}")
        return await self._dao.update_by_field(session, 'sop_id', sop_id, data)
    
    @transactional()
    async def delete_sop(
        self, 
        session: AsyncSession, 
        sop_id: str
    ) -> bool:
        """删除SOP模板"""
        existing = await self._dao.get_by_sop_id(session, sop_id)
        if not existing:
            return False
        
        logger.info(f"Deleting SOP template: {sop_id}")
        return await self._dao.delete_by_field(session, 'sop_id', sop_id) > 0
    
    # ========== 旧格式方法 - 向后兼容 ==========
    async def get_categories(self, session: AsyncSession) -> List[str]:
        """获取所有分类 - 字符串数组格式（向后兼容）"""
        return await self._dao.get_all_categories(session)
    
    async def get_teams(self, session: AsyncSession) -> List[str]:  
        """获取所有团队 - 字符串数组格式（向后兼容）"""
        return await self._dao.get_all_teams(session)
    
    async def get_category_statistics(
        self, 
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取分类统计 - 原有格式（向后兼容）"""
        return await self._dao.get_category_statistics(session)
    
    # ========== 新格式方法 - 统一标准格式 ==========
    async def get_category_options(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取分类选项 - 统一对象格式"""
        return await self._dao.get_category_options(session)
    
    async def get_team_options(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取团队选项 - 统一对象格式"""
        return await self._dao.get_team_options(session)
    
    async def get_severity_options(self, session: AsyncSession) -> List[Dict[str, Any]]:
        """获取严重程度选项 - 统一对象格式"""
        return await self._dao.get_severity_options(session)
    
    # ========== 优化列表查询 - 使用BaseModel批量转换 ==========
    async def list_sops_dict(
        self, 
        session: AsyncSession, 
        params: SOPQueryParams
    ) -> Tuple[List[Dict[str, Any]], int]:
        """列出SOP模板 - 返回字典格式"""
        templates, total = await self.list_sops(session, params)
        
        # 使用BaseModel的批量转换方法
        from src.shared.db.models import BaseModel
        template_data = BaseModel.bulk_to_dict(templates)
        
        return template_data, total


# 全局实例
sop_service = SOPService()