"""
Agent服务层 - 纯异步实现
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, case, text, bindparam, exists
import uuid
import json
import secrets
import hashlib

from src.apps.agent.models import AgentConfig
from src.apps.user.models import RbacUser
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
            
            # agent_key 字段已移除，密钥管理通过 agent_permission 表进行
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
                # 查看团队智能体：需要先获取当前用户的团队信息
                # 子查询获取当前用户的团队名称
                user_team_subquery = select(RbacUser.group_name).where(
                    RbacUser.user_name == current_user
                ).scalar_subquery()
                
                permission_conditions.append(
                    or_(
                        # 1. 我的智能体
                        AgentConfig.agent_owner == current_user,
                        # 2. 团队成员的团队级别或更高权限的智能体
                        and_(
                            AgentConfig.visibility_type.in_(['team', 'department', 'public']),
                            exists(
                                select(1).where(
                                    and_(
                                        RbacUser.user_name == AgentConfig.agent_owner,
                                        RbacUser.group_name == user_team_subquery
                                    )
                                )
                            )
                        ),
                        # 3. 我在额外授权用户列表中
                        text("JSON_CONTAINS(visibility_additional_users, :user, '$')").bindparams(user=f'"{current_user}"')
                    )
                )
            elif owner_filter == 'department':
                # 查看部门智能体：需要先获取当前用户的部门信息
                # 子查询获取当前用户的部门名称
                user_dept_subquery = select(RbacUser.department_name).where(
                    RbacUser.user_name == current_user
                ).scalar_subquery()
                
                permission_conditions.append(
                    or_(
                        # 1. 我的智能体
                        AgentConfig.agent_owner == current_user,
                        # 2. 部门成员的部门级别或更高权限的智能体
                        and_(
                            AgentConfig.visibility_type.in_(['department', 'public']),
                            exists(
                                select(1).where(
                                    and_(
                                        RbacUser.user_name == AgentConfig.agent_owner,
                                        RbacUser.department_name == user_dept_subquery
                                    )
                                )
                            )
                        ),
                        # 3. 我在额外授权用户列表中
                        text("JSON_CONTAINS(visibility_additional_users, :user, '$')").bindparams(user=f'"{current_user}"')
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
                    # 3. 团队权限：同团队成员的team级别智能体
                    and_(
                        AgentConfig.visibility_type == 'team',
                        exists(
                            select(1).where(
                                and_(
                                    RbacUser.user_name == AgentConfig.agent_owner,
                                    RbacUser.group_name == select(RbacUser.group_name).where(
                                        RbacUser.user_name == current_user
                                    ).scalar_subquery()
                                )
                            )
                        )
                    ),
                    # 4. 部门权限：同部门成员的department级别智能体
                    and_(
                        AgentConfig.visibility_type == 'department',
                        exists(
                            select(1).where(
                                and_(
                                    RbacUser.user_name == AgentConfig.agent_owner,
                                    RbacUser.department_name == select(RbacUser.department_name).where(
                                        RbacUser.user_name == current_user
                                    ).scalar_subquery()
                                )
                            )
                        )
                    ),
                    # 5. 我在额外授权用户列表中
                    text("JSON_CONTAINS(visibility_additional_users, :user, '$')").bindparams(user=f'"{current_user}"')
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
        update_data: Dict[str, Any],
        current_username: Optional[str] = None
    ) -> Optional[AgentConfig]:
        """更新智能体配置"""
        async with db.begin():
            # 检查是否存在
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
            existing = result.scalar_one_or_none()
            if not existing: 
                raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 检查权限：只有所有者可以修改
            if current_username:
                if existing.agent_owner != current_username:
                    raise BusinessException("只有智能体所有者可以修改", ResponseCode.FORBIDDEN)
            
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
    
    async def delete_agent_with_permission_check(
        self, 
        db: AsyncSession,
        agent_id: str,
        current_username: Optional[str] = None
    ) -> bool:
        """删除智能体配置（带权限检查）"""
        async with db.begin():
            # 检查是否存在
            result = await db.execute(select(AgentConfig).where(AgentConfig.agent_id == agent_id))
            existing = result.scalar_one_or_none()
            if not existing: 
                raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 内置智能体也可以删除，因为有自动注册功能
            # if existing.is_builtin == 'yes': 
            #     raise BusinessException("不能删除内置智能体", ResponseCode.FORBIDDEN)
            
            # 检查权限：只有所有者可以删除
            if current_username:
                if existing.agent_owner != current_username:
                    raise BusinessException("只有智能体所有者可以删除", ResponseCode.FORBIDDEN)
            
            logger.info(f"Deleting agent: {agent_id} by user: {current_username}, is_builtin: {existing.is_builtin}")
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
        # 先获取当前配置，保留系统工具
        agent = await self.get_agent_by_id(db, agent_id)
        if not agent:
            return None
            
        current_tools_info = agent.tools_info or {}
        system_tools = current_tools_info.get('system_tools', [])
        
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
        
        # 构建完整工具配置，保留系统工具
        tools_info = {'system_tools': system_tools, 'mcp_tools': mcp_tools_config}
        update_data = {'tools_info': tools_info}
        return await self.update_agent(db, agent_id, update_data)
    
    
    @staticmethod
    def get_available_system_tools() -> List[Dict[str, str]]:
        """获取所有可用的系统工具列表 - 自动扫描工具目录"""
        import os
        import importlib
        import inspect
        from langchain_core.tools import BaseTool
        
        tools_list = []
        tools_dir = os.path.join(os.path.dirname(__file__), '..', 'tools')
        
        # 扫描tools目录下的所有Python文件
        for filename in os.listdir(tools_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]  # 移除.py后缀
                
                try:
                    # 动态导入模块
                    module_path = f'src.apps.agent.tools.{module_name}'
                    module = importlib.import_module(module_path)
                    
                    # 扫描模块中的所有工具
                    for name, obj in inspect.getmembers(module):
                        # 检查是否是LangChain工具对象
                        if (hasattr(obj, 'name') and 
                            hasattr(obj, 'description') and
                            hasattr(obj, 'run')):  # LangChain工具都有run方法
                            
                            # 获取工具信息
                            tool_info = {
                                'name': obj.name,
                                'display_name': obj.name.replace('_', ' ').title(),
                                'description': obj.description or '无描述',
                                'module': module_name
                            }
                            tools_list.append(tool_info)
                            logger.debug(f"发现系统工具: {tool_info['name']} from {module_name}")
                            
                except Exception as e:
                    logger.warning(f"加载工具模块 {module_name} 失败: {e}")
                    
        return tools_list
    
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
    
    async def increment_run_count(self, db: AsyncSession, agent_id: str) -> None:
        """增量更新运行次数和最后使用时间"""
        async with db.begin():
            # 使用SQL的原子操作，直接在数据库层面增加计数
            await db.execute(
                update(AgentConfig)
                .where(AgentConfig.agent_id == agent_id)
                .values(
                    total_runs=AgentConfig.total_runs + 1,
                    last_used=now_shanghai(),
                    update_time=now_shanghai()
                )
            )
            logger.info(f"Updated run count for agent: {agent_id}")
    
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
            
            # 检查新用户是否存在
            result = await db.execute(select(RbacUser).where(RbacUser.user_name == new_owner))
            new_user = result.scalar_one_or_none()
            if not new_user:
                raise BusinessException(f"用户 {new_owner} 不存在", ResponseCode.NOT_FOUND)
            
            # 不能转移给自己
            if new_owner == current_user:
                raise BusinessException("不能将所有权转移给自己", ResponseCode.BAD_REQUEST)
            
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
            text("JSON_CONTAINS(favorite_users, :user, '$')").bindparams(user=f'"{username}"')
        )
        
        # 排序
        query = query.order_by(AgentConfig.update_time.desc())
        
        # 计算总数
        count_query = select(func.count(AgentConfig.id)).where(
            text("JSON_CONTAINS(favorite_users, :user, '$')").bindparams(user=f'"{username}"')
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
    
    # reset_agent_key 方法已移除，密钥管理通过 agent_permission_service 进行


# 创建全局实例
agent_service = AgentService()