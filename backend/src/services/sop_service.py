"""SOP service layer for database operations."""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.exc import IntegrityError
import json
import logging

from ..db.models import SOPTemplate
from ..schemas.sop import SOPTemplateCreate, SOPTemplateUpdate, SOPQueryParams

logger = logging.getLogger(__name__)


class SOPService:
    """Service class for SOP operations."""

    @staticmethod
    async def create_sop(
        db: AsyncSession, 
        sop_data: SOPTemplateCreate, 
        created_by: str = "admin"
    ) -> SOPTemplate:
        """Create a new SOP template."""
        try:
            # Convert steps and tools to JSON strings
            steps_json = [step.dict() for step in sop_data.steps]
            
            db_sop = SOPTemplate(
                sop_id=sop_data.sop_id,
                sop_title=sop_data.sop_title,
                sop_category=sop_data.sop_category,
                sop_description=sop_data.sop_description,
                sop_severity=sop_data.sop_severity,
                sop_steps=steps_json,
                tools_required=sop_data.tools_required,
                sop_recommendations=sop_data.sop_recommendations,
                team_name=sop_data.team_name,
                create_by=created_by,
                update_by=created_by
            )
            
            db.add(db_sop)
            await db.commit()
            await db.refresh(db_sop)
            
            logger.info(f"Created SOP: {sop_data.sop_id}")
            return db_sop
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"SOP ID already exists: {sop_data.sop_id}")
            raise ValueError(f"SOP ID '{sop_data.sop_id}' already exists")
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating SOP: {e}")
            raise

    @staticmethod
    async def get_sop_by_id(db: AsyncSession, sop_id: str) -> Optional[SOPTemplate]:
        """Get SOP by sop_id."""
        try:
            result = await db.execute(
                select(SOPTemplate).where(SOPTemplate.sop_id == sop_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting SOP {sop_id}: {e}")
            raise

    @staticmethod
    async def get_sop_by_db_id(db: AsyncSession, db_id: int) -> Optional[SOPTemplate]:
        """Get SOP by database id."""
        try:
            result = await db.execute(
                select(SOPTemplate).where(SOPTemplate.id == db_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting SOP by ID {db_id}: {e}")
            raise

    @staticmethod
    async def update_sop(
        db: AsyncSession, 
        sop_id: str, 
        sop_data: SOPTemplateUpdate,
        updated_by: str = "admin"
    ) -> Optional[SOPTemplate]:
        """Update an existing SOP template."""
        try:
            db_sop = await SOPService.get_sop_by_id(db, sop_id)
            if not db_sop:
                return None
            
            # Update only provided fields
            update_data = sop_data.dict(exclude_unset=True)
            
            # Convert steps to JSON if provided
            if 'steps' in update_data:
                update_data['sop_steps'] = [step.dict() for step in sop_data.steps]
                del update_data['steps']
            
            # Set updated_by
            update_data['update_by'] = updated_by
            
            for field, value in update_data.items():
                setattr(db_sop, field, value)
            
            await db.commit()
            await db.refresh(db_sop)
            
            logger.info(f"Updated SOP: {sop_id}")
            return db_sop
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating SOP {sop_id}: {e}")
            raise

    @staticmethod
    async def delete_sop(db: AsyncSession, sop_id: str) -> bool:
        """Delete an SOP template."""
        try:
            db_sop = await SOPService.get_sop_by_id(db, sop_id)
            if not db_sop:
                return False
            
            await db.delete(db_sop)
            await db.commit()
            
            logger.info(f"Deleted SOP: {sop_id}")
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting SOP {sop_id}: {e}")
            raise

    @staticmethod
    async def list_sops(
        db: AsyncSession, 
        params: SOPQueryParams
    ) -> Tuple[List[SOPTemplate], int]:
        """List SOPs with filtering and pagination."""
        try:
            # Build base query
            query = select(SOPTemplate)
            count_query = select(func.count(SOPTemplate.id))
            
            # Add filters
            conditions = []
            
            if params.search:
                search_term = f"%{params.search}%"
                conditions.append(
                    or_(
                        SOPTemplate.sop_title.ilike(search_term),
                        SOPTemplate.sop_description.ilike(search_term),
                        SOPTemplate.sop_id.ilike(search_term)
                    )
                )
            
            if params.category:
                conditions.append(SOPTemplate.sop_category == params.category)
            
            if params.severity and params.severity != "all":
                conditions.append(SOPTemplate.sop_severity == params.severity)
            
            if params.team_name:
                conditions.append(SOPTemplate.team_name == params.team_name)
            
            # Apply filters
            if conditions:
                filter_condition = and_(*conditions)
                query = query.where(filter_condition)
                count_query = count_query.where(filter_condition)
            
            # Get total count
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # Add ordering and pagination
            query = query.order_by(desc(SOPTemplate.update_time))
            
            if params.limit:
                query = query.limit(params.limit)
            
            if params.offset:
                query = query.offset(params.offset)
            
            # Execute query
            result = await db.execute(query)
            sops = result.scalars().all()
            
            logger.info(f"Listed {len(sops)} SOPs out of {total} total")
            return list(sops), total
            
        except Exception as e:
            logger.error(f"Error listing SOPs: {e}")
            raise

    @staticmethod
    async def get_categories(db: AsyncSession) -> List[str]:
        """Get all unique categories."""
        try:
            result = await db.execute(
                select(SOPTemplate.sop_category)
                .distinct()
                .order_by(SOPTemplate.sop_category)
            )
            categories = [row[0] for row in result.all()]
            return categories
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            raise

    @staticmethod
    async def get_teams(db: AsyncSession) -> List[str]:
        """Get all unique team names."""
        try:
            result = await db.execute(
                select(SOPTemplate.team_name)
                .distinct()
                .order_by(SOPTemplate.team_name)
            )
            teams = [row[0] for row in result.all()]
            return teams
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            raise