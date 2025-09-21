"""
消息反馈服务
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.dialects.mysql import insert

from src.apps.agent.models import AgentMessageFeedback, AgentConfig
from src.apps.user.models import UserThread
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode
from src.shared.db.models import now_shanghai

logger = get_logger(__name__)


class FeedbackService:
    """消息反馈服务"""
    
    async def submit_feedback(
        self,
        db: AsyncSession,
        thread_id: str,
        message_id: str,
        user_name: str,
        feedback_type: str,
        feedback_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提交消息反馈
        
        Args:
            db: 数据库会话
            thread_id: 会话ID
            message_id: 消息ID
            user_name: 用户名
            feedback_type: 反馈类型 (thumbs_up/thumbs_down)
            feedback_content: 反馈内容（预留）
            
        Returns:
            包含反馈信息和智能体统计数据的字典
        """
        async with db.begin():
            # 从数据库查询agent_id
            user_thread_stmt = select(UserThread.agent_id).where(
                UserThread.thread_id == thread_id
            )
            result = await db.execute(user_thread_stmt)
            agent_id = result.scalar_one_or_none()
            
            if not agent_id:
                raise BusinessException("无法找到对应的智能体信息", ResponseCode.BAD_REQUEST)
            # 检查是否已有反馈记录
            existing_stmt = select(AgentMessageFeedback).where(
                and_(
                    AgentMessageFeedback.user_name == user_name,
                    AgentMessageFeedback.message_id == message_id
                )
            )
            result = await db.execute(existing_stmt)
            existing_feedback = result.scalar_one_or_none()
            
            # 记录原有的反馈类型
            old_feedback_type = None
            if existing_feedback:
                old_feedback_type = existing_feedback.feedback_type
                
            # 使用 INSERT ... ON DUPLICATE KEY UPDATE 来处理
            stmt = insert(AgentMessageFeedback).values(
                thread_id=thread_id,
                message_id=message_id,
                agent_id=agent_id,
                user_name=user_name,
                feedback_type=feedback_type,
                feedback_content=feedback_content,
                create_by=user_name,
                update_by=user_name,
                create_time=now_shanghai(),
                update_time=now_shanghai()
            )
            
            # 如果存在则更新
            stmt = stmt.on_duplicate_key_update(
                feedback_type=feedback_type,
                feedback_content=feedback_content,
                update_by=user_name,
                update_time=now_shanghai()
            )
            
            await db.execute(stmt)
            
            # 更新智能体统计数据
            await self._update_agent_stats(db, agent_id, feedback_type, old_feedback_type)
            
            # 获取更新后的智能体统计数据
            agent_stats = await self._get_agent_stats(db, agent_id)
            
            # 返回结果
            return {
                "thread_id": thread_id,
                "message_id": message_id,
                "agent_id": agent_id,
                "user_name": user_name,
                "feedback_type": feedback_type,
                "feedback_content": feedback_content,
                "agent_stats": agent_stats
            }
    
    
    async def _update_agent_stats(
        self,
        db: AsyncSession,
        agent_id: str,
        new_feedback_type: str,
        old_feedback_type: Optional[str] = None
    ):
        """更新智能体统计数据"""
        # 构建更新语句
        if old_feedback_type is None:
            # 新增反馈
            if new_feedback_type == "thumbs_up":
                stmt = update(AgentConfig).where(
                    AgentConfig.agent_id == agent_id
                ).values(
                    thumbs_up_count=AgentConfig.thumbs_up_count + 1
                )
            else:
                stmt = update(AgentConfig).where(
                    AgentConfig.agent_id == agent_id
                ).values(
                    thumbs_down_count=AgentConfig.thumbs_down_count + 1
                )
        else:
            # 更新反馈
            if old_feedback_type == "thumbs_up" and new_feedback_type == "thumbs_down":
                # 从点赞改为点踩
                stmt = update(AgentConfig).where(
                    AgentConfig.agent_id == agent_id
                ).values(
                    thumbs_up_count=AgentConfig.thumbs_up_count - 1,
                    thumbs_down_count=AgentConfig.thumbs_down_count + 1
                )
            elif old_feedback_type == "thumbs_down" and new_feedback_type == "thumbs_up":
                # 从点踩改为点赞
                stmt = update(AgentConfig).where(
                    AgentConfig.agent_id == agent_id
                ).values(
                    thumbs_up_count=AgentConfig.thumbs_up_count + 1,
                    thumbs_down_count=AgentConfig.thumbs_down_count - 1
                )
            else:
                # 相同的反馈类型，不需要更新
                return
        
        await db.execute(stmt)
    
    async def _get_agent_stats(self, db: AsyncSession, agent_id: str) -> Dict[str, Any]:
        """获取智能体统计数据"""
        stmt = select(
            AgentConfig.thumbs_up_count,
            AgentConfig.thumbs_down_count,
            AgentConfig.total_runs
        ).where(AgentConfig.agent_id == agent_id)
        
        result = await db.execute(stmt)
        row = result.one_or_none()
        
        if not row:
            return {
                "thumbs_up_count": 0,
                "thumbs_down_count": 0,
                "total_runs": 0,
                "satisfaction_rate": 0.0
            }
        
        thumbs_up = row.thumbs_up_count or 0
        thumbs_down = row.thumbs_down_count or 0
        total_feedback = thumbs_up + thumbs_down
        
        # 计算满意度
        satisfaction_rate = 0.0
        if total_feedback > 0:
            satisfaction_rate = (thumbs_up / total_feedback) * 100
        
        return {
            "thumbs_up_count": thumbs_up,
            "thumbs_down_count": thumbs_down,
            "total_runs": row.total_runs or 0,
            "satisfaction_rate": round(satisfaction_rate, 1),
            "total_feedback": total_feedback
        }


# 创建服务实例
feedback_service = FeedbackService()