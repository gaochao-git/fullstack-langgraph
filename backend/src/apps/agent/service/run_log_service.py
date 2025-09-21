"""
智能体运行日志服务
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, and_, desc
from sqlalchemy.orm import aliased

from src.apps.agent.models import AgentRunLog, AgentConfig
from src.apps.user.models import RbacUser
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.db.models import now_shanghai

logger = get_logger(__name__)


class RunLogService:
    """运行日志服务"""
    
    async def create_run_log(
        self,
        db: AsyncSession,
        agent_id: str,
        thread_id: str,
        user_name: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AgentRunLog:
        """
        创建运行日志记录
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            thread_id: 会话ID
            user_name: 用户名
            ip_address: 用户IP地址
            user_agent: 用户浏览器信息
            
        Returns:
            创建的运行日志记录
        """
        async with db.begin():
            # 创建运行日志
            run_log = AgentRunLog(
                agent_id=agent_id,
                thread_id=thread_id,
                user_name=user_name,
                run_status='running',
                start_time=now_shanghai(),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            db.add(run_log)
            await db.flush()
            
            # 更新智能体运行次数
            update_stmt = update(AgentConfig).where(
                AgentConfig.agent_id == agent_id
            ).values(
                total_runs=AgentConfig.total_runs + 1,
                last_used=now_shanghai()
            )
            await db.execute(update_stmt)
            
            logger.info(f"创建运行日志: agent_id={agent_id}, thread_id={thread_id}, user={user_name}")
            return run_log
    
    async def update_run_log(
        self,
        db: AsyncSession,
        thread_id: str,
        run_status: str,
        end_time: Optional[datetime] = None,
        error_message: Optional[str] = None,
        token_usage: Optional[int] = None,
        message_count: Optional[int] = None
    ) -> bool:
        """
        更新运行日志
        
        Args:
            db: 数据库会话
            thread_id: 会话ID
            run_status: 运行状态
            end_time: 结束时间
            error_message: 错误信息
            token_usage: Token使用量
            message_count: 消息数量
            
        Returns:
            是否更新成功
        """
        async with db.begin():
            # 查找最新的运行日志
            stmt = select(AgentRunLog).where(
                AgentRunLog.thread_id == thread_id
            ).order_by(desc(AgentRunLog.id)).limit(1)
            
            result = await db.execute(stmt)
            run_log = result.scalar_one_or_none()
            
            if not run_log:
                logger.warning(f"未找到thread_id={thread_id}的运行日志")
                return False
            
            # 更新日志信息
            run_log.run_status = run_status
            if end_time:
                run_log.end_time = end_time
                # 计算运行时长
                duration = (end_time - run_log.start_time).total_seconds() * 1000
                run_log.duration_ms = int(duration)
            
            if error_message:
                run_log.error_message = error_message
            if token_usage is not None:
                run_log.token_usage = token_usage
            if message_count is not None:
                run_log.message_count = message_count
            
            logger.info(f"更新运行日志: thread_id={thread_id}, status={run_status}")
            return True
    
    async def get_agent_run_logs(
        self,
        db: AsyncSession,
        agent_id: str,
        limit: int = 20,
        offset: int = 0,
        user_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取智能体运行日志
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            limit: 返回条数
            offset: 偏移量
            user_name: 用户名筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            运行日志列表和统计信息
        """
        # 构建查询条件
        conditions = [AgentRunLog.agent_id == agent_id]
        if user_name:
            conditions.append(AgentRunLog.user_name == user_name)
        if start_date:
            conditions.append(AgentRunLog.start_time >= start_date)
        if end_date:
            conditions.append(AgentRunLog.start_time <= end_date)
        
        # 查询日志列表，关联用户表获取display_name
        stmt = select(
            AgentRunLog,
            RbacUser.display_name.label('user_display_name')
        ).join(
            RbacUser, RbacUser.user_name == AgentRunLog.user_name, isouter=True
        ).where(
            and_(*conditions)
        ).order_by(desc(AgentRunLog.start_time)).limit(limit).offset(offset)
        
        result = await db.execute(stmt)
        rows = result.all()
        
        # 查询总数
        count_stmt = select(func.count(AgentRunLog.id)).where(and_(*conditions))
        count_result = await db.execute(count_stmt)
        total = count_result.scalar() or 0
        
        # 统计信息
        from sqlalchemy import case
        stats_stmt = select(
            func.count(func.distinct(AgentRunLog.user_name)).label('unique_users'),
            func.count(AgentRunLog.id).label('total_runs'),
            func.sum(case((AgentRunLog.run_status == 'success', 1), else_=0)).label('success_runs'),
            func.sum(case((AgentRunLog.run_status == 'failed', 1), else_=0)).label('failed_runs'),
            func.avg(AgentRunLog.duration_ms).label('avg_duration'),
            func.sum(AgentRunLog.token_usage).label('total_tokens')
        ).where(and_(*conditions))
        
        stats_result = await db.execute(stats_stmt)
        stats = stats_result.one()
        
        # 获取运行用户统计
        user_stats_stmt = select(
            AgentRunLog.user_name,
            RbacUser.display_name.label('user_display_name'),
            func.count(AgentRunLog.id).label('run_count'),
            func.max(AgentRunLog.start_time).label('last_run_time')
        ).join(
            RbacUser, RbacUser.user_name == AgentRunLog.user_name, isouter=True
        ).where(
            and_(*conditions)
        ).group_by(
            AgentRunLog.user_name,
            RbacUser.display_name
        ).order_by(desc('run_count')).limit(10)
        
        user_stats_result = await db.execute(user_stats_stmt)
        user_stats = user_stats_result.all()
        
        # 格式化日志数据，添加display_name
        logs_data = []
        for row in rows:
            log = row.AgentRunLog
            log_dict = log.to_dict()
            log_dict['user_display_name'] = row.user_display_name or log.user_name
            logs_data.append(log_dict)
        
        return {
            "logs": logs_data,
            "total": total,
            "stats": {
                "unique_users": int(stats.unique_users or 0),
                "total_runs": int(stats.total_runs or 0),
                "success_runs": int(stats.success_runs or 0),
                "failed_runs": int(stats.failed_runs or 0),
                "success_rate": float(stats.success_runs or 0) / float(stats.total_runs) * 100 if stats.total_runs > 0 else 0,
                "avg_duration_ms": int(stats.avg_duration or 0),
                "total_tokens": int(stats.total_tokens or 0)
            },
            "user_stats": [
                {
                    "user_name": row.user_name,
                    "user_display_name": row.user_display_name or row.user_name,
                    "run_count": int(row.run_count or 0),
                    "last_run_time": row.last_run_time.isoformat() if row.last_run_time else None
                } for row in user_stats
            ]
        }
    
    async def get_user_run_summary(
        self,
        db: AsyncSession,
        agent_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取用户运行统计摘要
        
        Args:
            db: 数据库会话
            agent_id: 智能体ID
            days: 统计天数
            
        Returns:
            用户运行统计列表
        """
        start_date = now_shanghai() - timedelta(days=days)
        
        from sqlalchemy import case
        stmt = select(
            AgentRunLog.user_name,
            RbacUser.display_name.label('user_display_name'),
            func.count(AgentRunLog.id).label('total_runs'),
            func.sum(case((AgentRunLog.run_status == 'success', 1), else_=0)).label('success_runs'),
            func.avg(AgentRunLog.duration_ms).label('avg_duration'),
            func.sum(AgentRunLog.token_usage).label('total_tokens'),
            func.max(AgentRunLog.start_time).label('last_run_time')
        ).join(
            RbacUser, RbacUser.user_name == AgentRunLog.user_name, isouter=True
        ).where(
            and_(
                AgentRunLog.agent_id == agent_id,
                AgentRunLog.start_time >= start_date
            )
        ).group_by(
            AgentRunLog.user_name,
            RbacUser.display_name
        ).order_by(desc('total_runs'))
        
        result = await db.execute(stmt)
        rows = result.all()
        
        return [
            {
                "user_name": row.user_name,
                "user_display_name": row.user_display_name or row.user_name,
                "total_runs": int(row.total_runs or 0),
                "success_runs": int(row.success_runs or 0),
                "success_rate": float(row.success_runs or 0) / float(row.total_runs) * 100 if row.total_runs > 0 else 0,
                "avg_duration_ms": int(row.avg_duration or 0),
                "total_tokens": int(row.total_tokens or 0),
                "last_run_time": row.last_run_time.isoformat() if row.last_run_time else None
            } for row in rows
        ]


# 创建服务实例
run_log_service = RunLogService()