"""
智能体权限管理服务
管理agent_key与agent_id、user_name的关联关系
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import string

from src.apps.agent.models import AgentPermission, AgentConfig
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode

logger = get_logger(__name__)


class AgentPermissionService:
    """智能体权限管理服务"""
    
    @staticmethod
    def generate_agent_key() -> str:
        """生成新的agent_key"""
        # 生成一个安全的随机字符串，总长度32位（sk-前缀3位 + 29位随机字符）
        alphabet = string.ascii_letters + string.digits
        random_string = ''.join(secrets.choice(alphabet) for _ in range(29))
        return f"sk-{random_string}"
    
    async def create_permission(
        self, 
        db: AsyncSession, 
        agent_id: str,
        user_name: str,
        mark_comment: str = '',
        create_by: str = 'system'
    ) -> AgentPermission:
        """
        创建智能体权限
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            user_name: 用户名
            mark_comment: 工单号
            create_by: 创建者
        
        Returns:
            创建的权限记录
        """
        async with db.begin():
            # 检查智能体是否存在
            agent_stmt = select(AgentConfig).where(AgentConfig.agent_id == agent_id)
            agent_result = await db.execute(agent_stmt)
            agent = agent_result.scalar_one_or_none()
            
            if not agent:
                raise BusinessException(f"智能体 {agent_id} 不存在", ResponseCode.NOT_FOUND)
            
            # 检查是否已存在相同的权限
            existing_stmt = select(AgentPermission).where(
                and_(
                    AgentPermission.agent_id == agent_id,
                    AgentPermission.user_name == user_name
                )
            )
            existing_result = await db.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                if existing.is_active:
                    raise BusinessException(
                        f"用户 {user_name} 已经拥有该智能体的访问权限",
                        ResponseCode.DUPLICATE_ERROR
                    )
                else:
                    # 重新激活已禁用的权限
                    existing.is_active = True
                    existing.agent_key = self.generate_agent_key()
                    existing.mark_comment = mark_comment
                    existing.update_by = create_by
                    await db.flush()
                    logger.info(f"重新激活权限: agent_id={agent_id}, user_name={user_name}")
                    return existing
            
            # 创建新权限
            permission = AgentPermission(
                agent_id=agent_id,
                agent_key=self.generate_agent_key(),
                user_name=user_name,
                mark_comment=mark_comment,
                is_active=True,
                create_by=create_by
            )
            db.add(permission)
            await db.flush()
            
            logger.info(f"创建智能体权限: agent_id={agent_id}, user_name={user_name}, key={permission.agent_key[:10]}...")
            return permission
    
    async def get_permission_by_key(
        self, 
        db: AsyncSession, 
        agent_key: str
    ) -> Optional[AgentPermission]:
        """
        通过agent_key获取权限信息
        
        Args:
            db: 数据库会话
            agent_key: 密钥
        
        Returns:
            权限信息
        """
        stmt = select(AgentPermission).where(
            and_(
                AgentPermission.agent_key == agent_key,
                AgentPermission.is_active == True
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_permissions(
        self,
        db: AsyncSession,
        agent_id: Optional[str] = None,
        user_name: Optional[str] = None,
        page: int = 1,
        size: int = 10
    ) -> tuple[List[AgentPermission], int]:
        """
        获取权限列表
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID过滤
            user_name: 用户名过滤
            page: 页码
            size: 每页大小
        
        Returns:
            (权限列表, 总数)
        """
        # 构建查询 - 不过滤状态，显示所有记录
        stmt = select(AgentPermission)
        count_stmt = select(func.count(AgentPermission.id))
        
        if agent_id:
            stmt = stmt.where(AgentPermission.agent_id == agent_id)
            count_stmt = count_stmt.where(AgentPermission.agent_id == agent_id)
        
        if user_name:
            stmt = stmt.where(AgentPermission.user_name == user_name)
            count_stmt = count_stmt.where(AgentPermission.user_name == user_name)
        
        # 获取总数
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one()
        
        # 分页查询
        offset = (page - 1) * size
        stmt = stmt.offset(offset).limit(size).order_by(AgentPermission.create_time.desc())
        
        result = await db.execute(stmt)
        permissions = result.scalars().all()
        
        return permissions, total
    
    async def revoke_permission(
        self,
        db: AsyncSession,
        permission_id: int,
        update_by: str = 'system'
    ) -> bool:
        """
        撤销权限（软删除）
        
        Args:
            db: 数据库会话
            permission_id: 权限ID
            update_by: 更新者
        
        Returns:
            是否成功
        """
        async with db.begin():
            stmt = select(AgentPermission).where(AgentPermission.id == permission_id)
            result = await db.execute(stmt)
            permission = result.scalar_one_or_none()
            
            if not permission:
                raise BusinessException("权限记录不存在", ResponseCode.NOT_FOUND)
            
            if not permission.is_active:
                raise BusinessException("权限已被撤销", ResponseCode.BAD_REQUEST)
            
            permission.is_active = False
            permission.update_by = update_by
            await db.flush()
            
            logger.info(f"撤销智能体权限: id={permission_id}, agent_id={permission.agent_id}, user_name={permission.user_name}")
            return True
    
    async def regenerate_key(
        self,
        db: AsyncSession,
        permission_id: int,
        update_by: str = 'system'
    ) -> str:
        """
        重新生成agent_key
        
        Args:
            db: 数据库会话
            permission_id: 权限ID
            update_by: 更新者
        
        Returns:
            新的agent_key
        """
        async with db.begin():
            stmt = select(AgentPermission).where(AgentPermission.id == permission_id)
            result = await db.execute(stmt)
            permission = result.scalar_one_or_none()
            
            if not permission:
                raise BusinessException("权限记录不存在", ResponseCode.NOT_FOUND)
            
            if not permission.is_active:
                raise BusinessException("权限已被撤销", ResponseCode.BAD_REQUEST)
            
            new_key = self.generate_agent_key()
            permission.agent_key = new_key
            permission.update_by = update_by
            await db.flush()
            
            logger.info(f"重新生成agent_key: id={permission_id}, agent_id={permission.agent_id}, user_name={permission.user_name}")
            return new_key
    
    async def toggle_permission_status(
        self,
        db: AsyncSession,
        permission_id: int,
        is_active: bool,
        update_by: str = 'system'
    ) -> AgentPermission:
        """
        切换权限状态（启用/禁用）
        
        Args:
            db: 数据库会话
            permission_id: 权限ID
            is_active: 是否启用
            update_by: 更新者
        
        Returns:
            更新后的权限对象
        """
        async with db.begin():
            stmt = select(AgentPermission).where(AgentPermission.id == permission_id)
            result = await db.execute(stmt)
            permission = result.scalar_one_or_none()
            
            if not permission:
                raise BusinessException("权限记录不存在", ResponseCode.NOT_FOUND)
            
            permission.is_active = is_active
            permission.update_by = update_by
            await db.flush()
            
            logger.info(f"更新权限状态: id={permission_id}, is_active={is_active}")
            return permission


# 创建单例服务
agent_permission_service = AgentPermissionService()