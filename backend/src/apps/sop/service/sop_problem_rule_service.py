"""
SOP问题规则服务层
处理SOP与问题（Zabbix等）的映射规则
"""
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from src.apps.sop.models import SOPProblemRule, SOPTemplate
from src.apps.sop.schema import (
    SOPProblemRuleCreate,
    SOPProblemRuleUpdate,
    SOPProblemRuleResponse,
    SOPProblemRuleQuery
)
from src.shared.core.exceptions import BusinessException, ResponseCode
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class SOPProblemRuleService:
    """SOP问题规则服务"""
    
    async def create_rule(
        self,
        db: AsyncSession,
        rule_data: SOPProblemRuleCreate,
        created_by: str
    ) -> SOPProblemRule:
        """
        创建SOP问题规则
        
        Args:
            db: 数据库会话
            rule_data: 规则数据
            created_by: 创建人
            
        Returns:
            创建的规则
        """
        async with db.begin():
            # 检查SOP是否存在
            sop = await db.execute(
                select(SOPTemplate).where(SOPTemplate.sop_id == rule_data.sop_id)
            )
            if not sop.scalar_one_or_none():
                raise BusinessException(
                    f"SOP {rule_data.sop_id} 不存在",
                    ResponseCode.NOT_FOUND
                )
            
            # 检查规则名称是否重复
            existing = await db.execute(
                select(SOPProblemRule).where(SOPProblemRule.rule_name == rule_data.rule_name)
            )
            if existing.scalar_one_or_none():
                raise BusinessException(
                    f"规则名称 {rule_data.rule_name} 已存在",
                    ResponseCode.VALIDATION_ERROR
                )
            
            # 创建规则
            rule = SOPProblemRule(
                rule_name=rule_data.rule_name,
                sop_id=rule_data.sop_id,
                rules_info=rule_data.rules_info.model_dump(),
                is_enabled=1 if rule_data.is_enabled else 0,
                created_by=created_by
            )
            
            db.add(rule)
            await db.flush()
            await db.refresh(rule)
                    
            logger.info(f"Created SOP problem rule: {rule.rule_name} by {created_by}")
            return rule
        
    async def update_rule(
        self,
        db: AsyncSession,
        rule_id: int,
        rule_data: SOPProblemRuleUpdate,
        updated_by: str
    ) -> SOPProblemRule:
        """
        更新SOP问题规则
        
        Args:
            db: 数据库会话
            rule_id: 规则ID
            rule_data: 更新数据
            updated_by: 更新人
            
        Returns:
            更新后的规则
        """
        async with db.begin():
            # 获取现有规则
            result = await db.execute(
                select(SOPProblemRule).where(SOPProblemRule.id == rule_id)
            )
            rule = result.scalar_one_or_none()
            
            if not rule:
                raise BusinessException(
                    f"规则 {rule_id} 不存在",
                    ResponseCode.NOT_FOUND
                )
            
            # 如果更新规则名称，检查是否重复
            if rule_data.rule_name and rule_data.rule_name != rule.rule_name:
                existing = await db.execute(
                    select(SOPProblemRule).where(
                        and_(
                            SOPProblemRule.rule_name == rule_data.rule_name,
                            SOPProblemRule.id != rule_id
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    raise BusinessException(
                        f"规则名称 {rule_data.rule_name} 已存在",
                        ResponseCode.VALIDATION_ERROR
                    )
            
            # 如果更新SOP ID，检查SOP是否存在
            if rule_data.sop_id:
                sop = await db.execute(
                    select(SOPTemplate).where(SOPTemplate.sop_id == rule_data.sop_id)
                )
                if not sop.scalar_one_or_none():
                    raise BusinessException(
                        f"SOP {rule_data.sop_id} 不存在",
                        ResponseCode.NOT_FOUND
                    )
            
            # 更新字段
            update_dict = rule_data.model_dump(exclude_unset=True)
            if "rules_info" in update_dict and update_dict["rules_info"]:
                update_dict["rules_info"] = update_dict["rules_info"]
            if "is_enabled" in update_dict:
                update_dict["is_enabled"] = 1 if update_dict["is_enabled"] else 0
                
            for key, value in update_dict.items():
                setattr(rule, key, value)
            
            rule.updated_by = updated_by
            
            await db.flush()
            await db.refresh(rule)
                
            logger.info(f"Updated SOP problem rule: {rule.rule_name} by {updated_by}")
            return rule
        
    async def delete_rule(
        self,
        db: AsyncSession,
        rule_id: int
    ) -> bool:
        """
        删除SOP问题规则
        
        Args:
            db: 数据库会话
            rule_id: 规则ID
            
        Returns:
            是否成功
        """
        async with db.begin():
            result = await db.execute(
                select(SOPProblemRule).where(SOPProblemRule.id == rule_id)
            )
            rule = result.scalar_one_or_none()
            
            if not rule:
                raise BusinessException(
                    f"规则 {rule_id} 不存在",
                    ResponseCode.NOT_FOUND
                )
            
            await db.delete(rule)
                
            logger.info(f"Deleted SOP problem rule: {rule.rule_name}")
            return True
        
    async def get_rule(
        self,
        db: AsyncSession,
        rule_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        获取单个规则详情
        
        Args:
            db: 数据库会话
            rule_id: 规则ID
            
        Returns:
            规则详情
        """
        result = await db.execute(
            select(
                SOPProblemRule,
                SOPTemplate.sop_title.label("sop_name")
            ).outerjoin(
                SOPTemplate,
                SOPProblemRule.sop_id == SOPTemplate.sop_id
            ).where(SOPProblemRule.id == rule_id)
        )
        
        row = result.first()
        if not row:
            return None
            
        rule, sop_name = row
        rule_dict = rule.to_dict()
        rule_dict["sop_name"] = sop_name
        rule_dict["is_enabled"] = bool(rule_dict.get("is_enabled", 0))
        # Convert rules_info to JSON string if it's a dict
        if isinstance(rule_dict.get("rules_info"), dict):
            import json
            rule_dict["rules_info"] = json.dumps(rule_dict["rules_info"])
        
        return rule_dict
        
    async def list_rules(
        self,
        db: AsyncSession,
        query: SOPProblemRuleQuery
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        分页查询规则列表
        
        Args:
            db: 数据库会话
            query: 查询参数
            
        Returns:
            (规则列表, 总数)
        """
        # 构建查询
        stmt = select(
            SOPProblemRule,
            SOPTemplate.sop_title.label("sop_name")
        ).outerjoin(
            SOPTemplate,
            SOPProblemRule.sop_id == SOPTemplate.sop_id
        )
        
        # 添加过滤条件
        conditions = []
        
        if query.search:
            conditions.append(
                or_(
                    SOPProblemRule.rule_name.ilike(f"%{query.search}%"),
                    SOPProblemRule.sop_id.ilike(f"%{query.search}%")
                )
            )
            
        if query.sop_id:
            conditions.append(SOPProblemRule.sop_id == query.sop_id)
            
        if query.is_enabled is not None:
            conditions.append(SOPProblemRule.is_enabled == (1 if query.is_enabled else 0))
            
        if conditions:
            stmt = stmt.where(and_(*conditions))
            
        # 排序
        stmt = stmt.order_by(SOPProblemRule.create_time.desc())
        
        # 获取总数
        count_stmt = select(func.count()).select_from(SOPProblemRule)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total = await db.scalar(count_stmt)
        
        # 分页
        offset = (query.page - 1) * query.page_size
        stmt = stmt.offset(offset).limit(query.page_size)
        
        # 执行查询
        result = await db.execute(stmt)
        rows = result.all()
        
        # 格式化结果
        rules = []
        for row in rows:
            rule, sop_name = row
            rule_dict = rule.to_dict()
            rule_dict["sop_name"] = sop_name
            rule_dict["is_enabled"] = bool(rule_dict.get("is_enabled", 0))
            # Convert rules_info to JSON string if it's a dict
            if isinstance(rule_dict.get("rules_info"), dict):
                rule_dict["rules_info"] = json.dumps(rule_dict["rules_info"])
            rules.append(rule_dict)
            
        return rules, total
        
    async def get_rules_by_item_keys(
        self,
        db: AsyncSession,
        item_keys: List[str]
    ) -> List[Dict[str, Any]]:
        """
        根据item keys获取匹配的规则
        
        Args:
            db: 数据库会话
            item_keys: Zabbix item key列表
            
        Returns:
            匹配的规则列表
        """
        if not item_keys:
            return []
            
        # 获取所有启用的规则
        result = await db.execute(
            select(
                SOPProblemRule,
                SOPTemplate.sop_title.label("sop_name")
            ).outerjoin(
                SOPTemplate,
                SOPProblemRule.sop_id == SOPTemplate.sop_id
            ).where(SOPProblemRule.is_enabled == 1)
        )
        
        rows = result.all()
        matched_rules = []
        
        # 检查每个规则是否匹配
        for row in rows:
            rule, sop_name = row
            try:
                rules_info = rule._process_rules_info(rule.rules_info)
                rule_item_keys = rules_info.get("item_keys", [])
                
                # 检查是否有交集
                if any(key in rule_item_keys for key in item_keys):
                    rule_dict = rule.to_dict()
                    rule_dict["sop_name"] = sop_name
                    rule_dict["is_enabled"] = bool(rule_dict.get("is_enabled", 0))
                    # Convert rules_info to JSON string if it's a dict
                    if isinstance(rule_dict.get("rules_info"), dict):
                        rule_dict["rules_info"] = json.dumps(rule_dict["rules_info"])
                    matched_rules.append(rule_dict)
            except Exception as e:
                logger.warning(f"Failed to process rule {rule.id}: {e}")
                continue
                
        return matched_rules


# 单例实例
sop_problem_rule_service = SOPProblemRuleService()