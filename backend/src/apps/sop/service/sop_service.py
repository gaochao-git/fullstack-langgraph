"""
SOP统一服务层
同时支持静态方法（兼容现有API）和实例方法（新架构）
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from ....shared.db.dao import SOPDAO
from ....shared.db.models import SOPTemplate
from ....shared.db.transaction import transactional, sync_transactional
from ....shared.core.logging import get_logger
from ..schema.sop import SOPTemplateCreate, SOPTemplateUpdate, SOPQueryParams

logger = get_logger(__name__)


class SOPService:
    """SOP模板服务 - 支持新旧两种调用方式"""
    
    _instance = None
    _dao = None
    
    def __init__(self):
        if not self._dao:
            self._dao = SOPDAO()
    
    @classmethod
    def get_instance(cls):
        """获取单例实例"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance
    
    # ==================== 静态方法（兼容现有API） ====================
    
    @staticmethod
    async def create_sop(session: AsyncSession, sop_data: SOPTemplateCreate) -> SOPTemplate:
        """创建SOP模板（静态方法，兼容现有API）"""
        service = SOPService.get_instance()
        data = sop_data.dict() if hasattr(sop_data, 'dict') else sop_data
        
        # 处理字段名映射
        if 'steps' in data:
            data['sop_steps'] = data.pop('steps')
        
        return await service.create_sop_template(session, data)
    
    @staticmethod
    async def get_sop_by_id(session: AsyncSession, sop_id: str) -> Optional[SOPTemplate]:
        """根据ID获取SOP（静态方法）"""
        service = SOPService.get_instance()
        return await service._dao.get_by_sop_id(session, sop_id)
    
    @staticmethod 
    async def list_sops(session: AsyncSession, params: SOPQueryParams) -> Tuple[List[SOPTemplate], int]:
        """列出SOP模板（静态方法）"""
        service = SOPService.get_instance()
        
        # 构建过滤条件
        filters = {}
        if params.category:
            filters['sop_category'] = params.category
        if params.severity:
            filters['sop_severity'] = params.severity
        if params.team_name:
            filters['team_name'] = params.team_name
        
        # 如果有搜索词，使用搜索功能
        if params.search:
            templates = await service._dao.search_by_title(
                session,
                params.search,
                team_name=params.team_name,
                limit=params.limit,
                offset=params.offset
            )
            # 获取搜索结果总数（简化实现）
            all_results = await service._dao.search_by_title(session, params.search, team_name=params.team_name)
            total = len(all_results)
        else:
            # 获取数据
            templates = await service._dao.get_list(
                session,
                filters=filters if filters else None,
                limit=params.limit,
                offset=params.offset,
                order_by='create_time'
            )
            
            # 获取总数
            total = await service._dao.count(session, filters=filters if filters else None)
        
        return templates, total
    
    @staticmethod
    async def update_sop(session: AsyncSession, sop_id: str, sop_data: SOPTemplateUpdate) -> Optional[SOPTemplate]:
        """更新SOP模板（静态方法）"""
        service = SOPService.get_instance()
        data = sop_data.dict(exclude_unset=True) if hasattr(sop_data, 'dict') else sop_data
        
        # 处理字段名映射
        if 'steps' in data:
            data['sop_steps'] = data.pop('steps')
        
        return await service.update_sop_template(session, sop_id, data)
    
    @staticmethod
    async def delete_sop(session: AsyncSession, sop_id: str) -> bool:
        """删除SOP模板（静态方法）"""
        service = SOPService.get_instance()
        return await service.delete_sop_template(session, sop_id)
    
    @staticmethod
    async def get_categories(session: AsyncSession) -> List[str]:
        """获取所有分类（静态方法）"""
        result = await session.execute(
            select(SOPTemplate.sop_category).distinct()
        )
        categories = [row[0] for row in result.fetchall() if row[0]]
        return sorted(categories)
    
    @staticmethod
    async def get_teams(session: AsyncSession) -> List[str]:
        """获取所有团队（静态方法）"""
        result = await session.execute(
            select(SOPTemplate.team_name).distinct()
        )
        teams = [row[0] for row in result.fetchall() if row[0]]
        return sorted(teams)
    
    # ==================== 实例方法（新架构） ====================
    
    @transactional()
    async def create_sop_template(
        self, 
        session: AsyncSession,
        sop_data: Dict[str, Any]
    ) -> SOPTemplate:
        """创建SOP模板（实例方法）"""
        # 业务验证
        if not sop_data.get('sop_id'):
            raise ValueError("SOP ID is required")
        
        # 检查是否已存在
        existing = await self._dao.get_by_sop_id(session, sop_data['sop_id'])
        if existing:
            raise ValueError(f"SOP template with ID {sop_data['sop_id']} already exists")
        
        # 设置默认值
        sop_data.setdefault('sop_severity', 'medium')
        sop_data.setdefault('team_name', 'default')
        
        logger.info(f"Creating SOP template: {sop_data['sop_id']}")
        return await self._dao.create(session, sop_data)
    
    async def get_sop_by_id(
        self, 
        session: AsyncSession, 
        sop_id: str
    ) -> Optional[SOPTemplate]:
        """根据ID获取SOP模板（实例方法）"""
        return await self._dao.get_by_sop_id(session, sop_id)
    
    async def get_sop_list(
        self, 
        session: AsyncSession,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        team_name: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """获取SOP模板列表（实例方法）"""
        offset = (page - 1) * size
        
        # 构建过滤条件
        filters = {}
        if category:
            filters['sop_category'] = category
        if severity:
            filters['sop_severity'] = severity
        if team_name:
            filters['team_name'] = team_name
        
        # 获取数据和总数
        templates = await self._dao.get_list(
            session, 
            filters=filters if filters else None,
            limit=size, 
            offset=offset,
            order_by='create_time'
        )
        
        total = await self._dao.count(session, filters=filters if filters else None)
        
        return {
            'items': [template.to_dict() for template in templates],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size
        }
    
    async def search_sops(
        self, 
        session: AsyncSession,
        keyword: str,
        team_name: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> Dict[str, Any]:
        """搜索SOP模板（实例方法）"""
        offset = (page - 1) * size
        
        templates = await self._dao.search_by_title(
            session, 
            keyword,
            team_name=team_name,
            limit=size, 
            offset=offset
        )
        
        # 获取搜索结果总数（简化实现）
        all_results = await self._dao.search_by_title(session, keyword, team_name=team_name)
        total = len(all_results)
        
        return {
            'items': [template.to_dict() for template in templates],
            'total': total,
            'page': page,
            'size': size,
            'pages': (total + size - 1) // size,
            'keyword': keyword
        }
    
    @transactional()
    async def update_sop_template(
        self, 
        session: AsyncSession,
        sop_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[SOPTemplate]:
        """更新SOP模板（实例方法）"""
        # 检查是否存在
        existing = await self._dao.get_by_sop_id(session, sop_id)
        if not existing:
            raise ValueError(f"SOP template with ID {sop_id} not found")
        
        # 移除不可更新的字段
        update_data.pop('sop_id', None)
        update_data.pop('create_time', None)
        update_data.pop('create_by', None)
        
        logger.info(f"Updating SOP template: {sop_id}")
        return await self._dao.update_by_field(session, 'sop_id', sop_id, update_data)
    
    @transactional()
    async def delete_sop_template(
        self, 
        session: AsyncSession,
        sop_id: str
    ) -> bool:
        """删除SOP模板（实例方法）"""
        # 检查是否存在
        existing = await self._dao.get_by_sop_id(session, sop_id)
        if not existing:
            return False  # 不存在则返回False，而不是抛异常
        
        logger.info(f"Deleting SOP template: {sop_id}")
        return await self._dao.delete_by_field(session, 'sop_id', sop_id) > 0
    
    async def get_category_statistics(
        self, 
        session: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取分类统计（实例方法）"""
        # 使用数据库聚合查询而不是多次查询
        result = await session.execute(
            select(
                SOPTemplate.sop_category,
                func.count(SOPTemplate.id).label('count')
            ).group_by(SOPTemplate.sop_category)
        )
        
        stats = []
        for row in result.fetchall():
            if row.sop_category:  # 排除空分类
                stats.append({
                    'category': row.sop_category,
                    'count': row.count
                })
        
        return sorted(stats, key=lambda x: x['count'], reverse=True)
    
    # ==================== 同步业务方法（兼容） ====================
    
    @sync_transactional()
    def sync_create_sop_template(
        self, 
        session: Session,
        sop_data: Dict[str, Any]
    ) -> SOPTemplate:
        """同步创建SOP模板"""
        # 业务验证
        if not sop_data.get('sop_id'):
            raise ValueError("SOP ID is required")
        
        # 检查是否已存在
        existing = self._dao.sync_get_by_sop_id(session, sop_data['sop_id'])
        if existing:
            raise ValueError(f"SOP template with ID {sop_data['sop_id']} already exists")
        
        # 设置默认值
        sop_data.setdefault('sop_severity', 'medium')
        sop_data.setdefault('team_name', 'default')
        
        logger.info(f"Creating SOP template (sync): {sop_data['sop_id']}")
        return self._dao.sync_create(session, sop_data)


# 创建全局实例以支持导入使用
sop_service = SOPService()