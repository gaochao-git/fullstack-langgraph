"""SOP API routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from src.shared.db.config import get_async_db
from src.apps.sop.schema.sop import (
    SOPTemplateCreate, SOPTemplateUpdate, SOPTemplateResponse,
    SOPQueryParams, SOPListResponse, ApiResponse
)
from src.apps.sop.service.sop_service import SOPService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["SOP Management"])


@router.post("/sops", response_model=ApiResponse)
async def create_sop(
    sop_data: SOPTemplateCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new SOP template."""
    try:
        db_sop = await SOPService.create_sop(db, sop_data)
        return ApiResponse(
            success=True,
            data=db_sop.to_dict(),
            message="SOP created successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating SOP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SOP"
        )


@router.post("/sops/list", response_model=ApiResponse)
async def list_sops(
    params: SOPQueryParams,
    db: AsyncSession = Depends(get_async_db)
):
    """List SOPs with filtering and pagination."""
    try:
        sops, total = await SOPService.list_sops(db, params)
        
        sop_list = [sop.to_dict() for sop in sops]
        
        return ApiResponse(
            success=True,
            data={
                "data": sop_list,
                "total": total
            }
        )
    except Exception as e:
        logger.error(f"Error listing SOPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list SOPs"
        )


@router.get("/sops/{sop_id}", response_model=ApiResponse)
async def get_sop(
    sop_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Get a specific SOP by ID."""
    try:
        db_sop = await SOPService.get_sop_by_id(db, sop_id)
        if not db_sop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOP not found"
            )
        
        return ApiResponse(
            success=True,
            data=db_sop.to_dict()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting SOP {sop_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get SOP"
        )


@router.put("/sops/{sop_id}", response_model=ApiResponse)
async def update_sop(
    sop_id: str,
    sop_data: SOPTemplateUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """Update an existing SOP template."""
    try:
        db_sop = await SOPService.update_sop(db, sop_id, sop_data)
        if not db_sop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOP not found"
            )
        
        return ApiResponse(
            success=True,
            data=db_sop.to_dict(),
            message="SOP updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating SOP {sop_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update SOP"
        )


@router.delete("/sops/{sop_id}", response_model=ApiResponse)
async def delete_sop(
    sop_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Delete an SOP template."""
    try:
        success = await SOPService.delete_sop(db, sop_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOP not found"
            )
        
        return ApiResponse(
            success=True,
            data=True,
            message="SOP deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting SOP {sop_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete SOP"
        )


@router.get("/sops/meta/categories", response_model=ApiResponse)
async def get_categories(
    db: AsyncSession = Depends(get_async_db)
):
    """Get all available SOP categories."""
    try:
        categories = await SOPService.get_categories(db)
        return ApiResponse(
            success=True,
            data=categories
        )
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get categories"
        )


@router.get("/sops/meta/teams", response_model=ApiResponse)
async def get_teams(
    db: AsyncSession = Depends(get_async_db)
):
    """Get all available team names."""
    try:
        teams = await SOPService.get_teams(db)
        return ApiResponse(
            success=True,
            data=teams
        )
    except Exception as e:
        logger.error(f"Error getting teams: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get teams"
        )