"""
Agent服务层 - 纯异步实现
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, case, text
import uuid
import json

from src.apps.agent.models import AgentConfig
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.db.models import now_shanghai

logger = get_logger(__name__)



class AgentService:
    """Agent服务层 - 纯异步实现"""
    
    # ==================== 核心业务方法 ====================
    
    async def create_agent(
        self, 
        db: AsyncSession,
        agent_data: Dict[str, Any]
    ) -> AgentConfig:
        """创建智能体配置"""
        async with db.begin():
            # 生成agent_id（如果未提供）
            if not agent_data.get('agent_id'): agent_data['agent_id'] = f"custom_{uuid.uuid4().hex[:8]}"
            # 检查是否已存在
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_data['agent_id']))
            existing = result.scalar_one_or_none()
            if existing: raise BusinessException(f"智能体ID {agent_data['agent_id']} 已存在", ResponseCode.DUPLICATE_RESOURCE)
            
            
            # 设置默认值
            agent_data.setdefault('agent_status', 'stopped')
            agent_data.setdefault('agent_enabled', 'yes')
            agent_data.setdefault('agent_icon', 'Bot')
            agent_data.setdefault('is_builtin', 'no')
            agent_data.setdefault('create_by', 'system')
            agent_data.setdefault('total_runs', 0)
            agent_data.setdefault('success_rate', 0.0)
            agent_data.setdefault('avg_response_time', 0.0)
            agent_data.setdefault('create_time', now_shanghai())
            agent_data.setdefault('update_time', now_shanghai()) 
            # 处理capabilities字段映射
            if 'capabilities' in agent_data and isinstance(agent_data['capabilities'], list):agent_data['agent_capabilities'] = agent_data.pop('capabilities')
            
            # 处理JSON字段 - 转换为JSON字符串
            if 'visibility_additional_users' in agent_data:
                if isinstance(agent_data['visibility_additional_users'], list):
                    agent_data['visibility_additional_users'] = json.dumps(agent_data['visibility_additional_users'])
                elif agent_data['visibility_additional_users'] is None:
                    agent_data['visibility_additional_users'] = json.dumps([])
            
            # 设置默认的权限相关字段
            agent_data.setdefault('agent_owner', 'system')
            agent_data.setdefault('visibility_type', 'public')
            
            logger.info(f"Creating agent: {agent_data['agent_id']}")
            instance = AgentConfig(**agent_data)
            db.add(instance)
            await db.flush()
            await db.refresh(instance)
            return instance
    
    async def get_agent_by_id(
        self, 
        db: AsyncSession, 
        agent_id: str,
        current_user: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """根据ID获取智能体配置"""
        result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
        db_agent = result.scalar_one_or_none()
        if db_agent:
            agent_dict = db_agent.to_dict()
            # 确保有mcp_config字段
            if 'mcp_config' not in agent_dict:
                agent_dict['mcp_config'] = {
                    'enabled_servers': [],
                    'selected_tools': [],
                    'total_tools': 0
                }
            
            # 添加当前用户是否收藏的标记
            if current_user:
                favorite_users = db_agent._process_favorite_users(db_agent.favorite_users)
                agent_dict['is_favorited'] = current_user in favorite_users
            else:
                agent_dict['is_favorited'] = False
                
            return agent_dict

        return None
    
    async def list_agents(
        self, 
        db: AsyncSession,
        page: int = 1,
        size: int = 10,
        search: Optional[str] = None,
        status: Optional[str] = None,
        enabled_only: bool = False,
        create_by: Optional[str] = None,
        current_user: Optional[str] = None,
        owner_filter: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取智能体列表"""
        offset = (page - 1) * size
        
        # 构建基础过滤条件
        filters = {}
        if enabled_only:
            filters['agent_enabled'] = 'yes'
            filters['is_active'] = True
        if status:
            filters['agent_status'] = status
        if create_by:
            filters['create_by'] = create_by
        
        # 构建权限过滤条件
        permission_conditions = []
        if current_user and owner_filter:
            if owner_filter == 'mine':
                # 只看我的智能体
                permission_conditions.append(AgentConfig.agent_owner == current_user)
            elif owner_filter == 'team':
                # 查看团队智能体：我的 + 团队成员的公开智能体
                # TODO: 需要从用户表获取团队成员信息
                permission_conditions.append(
                    and_(
                        AgentConfig.visibility_type.in_(['team', 'department', 'public']),
                        # 这里应该加入团队成员判断
                    )
                )
            elif owner_filter == 'department':
                # 查看部门智能体：我的 + 部门成员的公开智能体
                # TODO: 需要从用户表获取部门成员信息
                permission_conditions.append(
                    and_(
                        AgentConfig.visibility_type.in_(['department', 'public']),
                        # 这里应该加入部门成员判断
                    )
                )
        elif current_user:
            # 默认权限过滤：可以看到的智能体
            permission_conditions.append(
                or_(
                    # 1. 我是所有者
                    AgentConfig.agent_owner == current_user,
                    # 2. 公开的智能体
                    AgentConfig.visibility_type == 'public',
                    # 3. 我在额外授权用户列表中
                    text(f"JSON_CONTAINS(visibility_additional_users, '\"{current_user}\"', '$')")
                )
            )
        
        # 获取数据库中的智能体
        # 构建查询
        query = select(AgentConfig)
        conditions = []
        
        # 添加搜索条件
        if search:
            conditions.append(AgentConfig.agent_name.contains(search))
        
        # 添加基础过滤条件
        for field_name, field_value in filters.items():
            if hasattr(AgentConfig, field_name):
                field = getattr(AgentConfig, field_name)
                conditions.append(field == field_value)
        
        # 添加权限过滤条件
        if permission_conditions:
            conditions.extend(permission_conditions)
        
        # 应用所有条件
        if conditions:
            query = query.where(and_(*conditions))
        
        # 排序
        query = query.order_by(AgentConfig.create_time.desc())
        
        # 计算总数
        count_query = select(func.count(AgentConfig.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 分页
        query = query.offset(offset).limit(size)
        result = await db.execute(query)
        db_agents = list(result.scalars().all())
        
        # 转换为字典格式
        all_agents = []
        for agent in db_agents:
            agent_dict = agent.to_dict()
            # 确保有mcp_config字段
            if 'mcp_config' not in agent_dict:
                agent_dict['mcp_config'] = {
                    'enabled_servers': [],
                    'selected_tools': [],
                    'total_tools': 0
                }
            
            # 添加当前用户是否收藏的标记
            if current_user:
                favorite_users = agent._process_favorite_users(agent.favorite_users)
                agent_dict['is_favorited'] = current_user in favorite_users
            else:
                agent_dict['is_favorited'] = False
                
            all_agents.append(agent_dict)
        
        return all_agents, total
    
    async def update_agent(
        self, 
        db: AsyncSession,
        agent_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[AgentConfig]:
        """更新智能体配置"""
        async with db.begin():
            # 检查是否存在
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
            existing = result.scalar_one_or_none()
            if not existing: raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 移除不可更新的字段
            update_data = {k: v for k, v in update_data.items() if k not in ['agent_id', 'create_time', 'create_by']}
            # 设置更新时间
            update_data['update_time'] = now_shanghai()
            # 处理capabilities字段映射
            if 'capabilities' in update_data and isinstance(update_data['capabilities'], list): 
                update_data['agent_capabilities'] = update_data.pop('capabilities')
            
            # 处理JSON字段 - 转换为JSON字符串
            if 'visibility_additional_users' in update_data:
                if isinstance(update_data['visibility_additional_users'], list):
                    update_data['visibility_additional_users'] = json.dumps(update_data['visibility_additional_users'])
                elif update_data['visibility_additional_users'] is None:
                    update_data['visibility_additional_users'] = json.dumps([])
            
            logger.info(f"Updating agent: {agent_id}")
            await db.execute(update(AgentConfig).where(AgentConfig.agent_id == agent_id).values(**update_data))
            
            # 返回更新后的数据
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
            return result.scalar_one_or_none()
    
    async def delete_agent(
        self, 
        db: AsyncSession,
        agent_id: str
    ) -> bool:
        """删除智能体配置"""
        async with db.begin():
            # 检查是否存在
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
            existing = result.scalar_one_or_none()
            if not existing: raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 检查是否为内置智能体
            if existing.is_builtin == 'yes': raise BusinessException(f"不能删除内置智能体: {agent_id}", ResponseCode.FORBIDDEN)
            
            logger.info(f"Deleting agent: {agent_id}")
            result = await db.execute(delete(AgentConfig).where(AgentConfig.agent_id == agent_id))
            return result.rowcount > 0
    
    async def update_mcp_config(
        self,
        db: AsyncSession,
        agent_id: str,
        enabled_servers: List[str],
        selected_tools: List[str]
    ) -> Optional[AgentConfig]:
        """更新智能体MCP配置"""
        # 构建MCP工具配置
        mcp_tools_config = []
        for server_id in enabled_servers:
            # 获取该服务器的工具
            server_tools = [tool for tool in selected_tools if tool.startswith(f"{server_id}:")]
            if server_tools:
                mcp_tools_config.append({
                    'server_id': server_id,
                    'tools': [tool.split(':', 1)[1] for tool in server_tools]  # 移除server_id前缀
                })
        
        # 构建完整工具配置
        tools_info = {'system_tools': [], 'mcp_tools': mcp_tools_config}
        update_data = {'tools_info': tools_info}
        return await self.update_agent(db, agent_id, update_data)
    
    async def update_agent_status(
        self,
        db: AsyncSession,
        agent_id: str,
        status: str
    ) -> Optional[AgentConfig]:
        """更新智能体状态"""
        async with db.begin():
            update_data = {'agent_status': status,'update_time': now_shanghai()}
            await db.execute(update(AgentConfig).where(AgentConfig.agent_id == agent_id).values(**update_data))
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
            return result.scalar_one_or_none()
    
    async def update_statistics(
        self,
        db: AsyncSession,
        agent_id: str,
        total_runs: int,
        success_rate: float,
        avg_response_time: float
    ) -> Optional[AgentConfig]:
        """更新运行统计信息"""
        async with db.begin():
            update_data = {
                'total_runs': total_runs,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'last_used': now_shanghai(),
                'update_time': now_shanghai()
            }
            await db.execute(update(AgentConfig).where(AgentConfig.agent_id == agent_id).values(**update_data))
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
            return result.scalar_one_or_none()
    
    async def get_statistics(self, db: AsyncSession):
        """获取智能体统计信息 - 返回原始查询结果让响应层处理"""
        result = await db.execute(
            select(
                func.count(AgentConfig.id).label('total'),
                func.sum(
                    case((and_(AgentConfig.agent_enabled == 'yes', AgentConfig.is_active == True), 1),else_=0)
                ).label('enabled'),
                func.sum(
                    case((AgentConfig.agent_status == 'running', 1), else_=0)
                ).label('running'),
                func.sum(
                    case((AgentConfig.is_builtin == 'yes', 1), else_=0)
                ).label('builtin')
            )
        )
        
        # 从原始结果中获取第一行数据
        stats_row = result.first()
        if stats_row:
            stats_dict = dict(stats_row)
            # 添加业务逻辑计算
            stats_dict['custom'] = stats_dict['total'] - stats_dict['builtin']
            return stats_dict
        
        # 如果没有数据，返回默认统计
        return {'total': 0,'enabled': 0,'running': 0,'builtin': 0,'custom': 0}
    
    async def search_agents(
        self,
        db: AsyncSession,
        keyword: str,
        page: int = 1,
        size: int = 10
    ) -> Tuple[List[Dict[str, Any]], int]:
        """搜索智能体"""
        offset = (page - 1) * size
        
        # 搜索数据库中的智能体
        query = select(AgentConfig).where(AgentConfig.agent_name.contains(keyword)
        ).where(and_(AgentConfig.agent_enabled == 'yes',AgentConfig.is_active == True)
        ).offset(offset).limit(size)
        
        result = await db.execute(query)
        db_agents = list(result.scalars().all())
        
        # 转换数据库结果
        all_matches = []
        for agent in db_agents:
            agent_dict = agent.to_dict()
            if 'mcp_config' not in agent_dict:
                agent_dict['mcp_config'] = {'enabled_servers': [],'selected_tools': [],'total_tools': 0}
            all_matches.append(agent_dict)
        
        return all_matches, len(all_matches)
    
    async def transfer_ownership(
        self,
        db: AsyncSession,
        agent_id: str,
        new_owner: str,
        current_user: str,
        reason: Optional[str] = None
    ) -> Optional[AgentConfig]:
        """转移智能体所有权"""
        async with db.begin():
            # 检查智能体是否存在
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
            agent = result.scalar_one_or_none()
            if not agent:
                raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 检查当前用户是否为所有者
            if agent.agent_owner != current_user:
                raise BusinessException("只有智能体所有者才能转移所有权", ResponseCode.FORBIDDEN)
            
            # 更新所有者
            update_data = {
                'agent_owner': new_owner,
                'update_time': now_shanghai(),
                'update_by': current_user
            }
            
            logger.info(f"Transferring ownership of agent {agent_id} from {current_user} to {new_owner}. Reason: {reason}")
            
            await db.execute(
                update(AgentConfig)
                .where(AgentConfig.agent_id == agent_id)
                .values(**update_data)
            )
            
            # 返回更新后的数据
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
            return result.scalar_one_or_none()
    
    async def toggle_favorite(
        self,
        db: AsyncSession,
        agent_id: str,
        username: str,
        is_favorite: bool
    ) -> bool:
        """切换智能体收藏状态"""
        async with db.begin():
            # 检查智能体是否存在
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
            agent = result.scalar_one_or_none()
            if not agent:
                raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 获取当前收藏用户列表
            current_favorites = agent._process_favorite_users(agent.favorite_users)
            
            if is_favorite:
                # 添加收藏
                if username not in current_favorites:
                    current_favorites.append(username)
                    logger.info(f"User {username} favorited agent {agent_id}")
            else:
                # 取消收藏
                if username in current_favorites:
                    current_favorites.remove(username)
                    logger.info(f"User {username} unfavorited agent {agent_id}")
            
            # 更新收藏列表
            await db.execute(
                update(AgentConfig)
                .where(AgentConfig.agent_id == agent_id)
                .values(favorite_users=json.dumps(current_favorites))
            )
            
            return is_favorite
    
    async def get_user_favorites(
        self,
        db: AsyncSession,
        username: str,
        page: int = 1,
        size: int = 10
    ) -> Tuple[List[Dict[str, Any]], int]:
        """获取用户收藏的智能体列表"""
        offset = (page - 1) * size
        
        # 使用JSON_CONTAINS查询包含该用户的收藏
        query = select(AgentConfig).where(
            text(f"JSON_CONTAINS(favorite_users, '\"{username}\"', '$')")
        )
        
        # 排序
        query = query.order_by(AgentConfig.update_time.desc())
        
        # 计算总数
        count_query = select(func.count(AgentConfig.id)).where(
            text(f"JSON_CONTAINS(favorite_users, '\"{username}\"', '$')")
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        
        # 分页
        query = query.offset(offset).limit(size)
        result = await db.execute(query)
        db_agents = list(result.scalars().all())
        
        # 转换为字典格式
        agents = []
        for agent in db_agents:
            agent_dict = agent.to_dict()
            # 确保有mcp_config字段
            if 'mcp_config' not in agent_dict:
                agent_dict['mcp_config'] = {
                    'enabled_servers': [],
                    'selected_tools': [],
                    'total_tools': 0
                }
            agents.append(agent_dict)
        
        return agents, total


# 创建全局实例
agent_service = AgentService()