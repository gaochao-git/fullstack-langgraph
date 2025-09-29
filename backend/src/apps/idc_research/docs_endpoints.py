"""
IDC Research API Documentation routes
"""

import os
from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

router = APIRouter()


@router.get("/docs", include_in_schema=False)
async def idc_research_docs():
    """Serve Swagger UI bound to the IDC Research OpenAPI spec (YAML)."""
    # Swagger UI can load YAML specs; we point it to our YAML route
    return get_swagger_ui_html(
        openapi_url="/api/v1/idc-research/docs/openapi.yaml",
        title="IDC Research API Docs",
    )


@router.get("/docs/openapi.yaml", include_in_schema=False)
async def idc_research_openapi_yaml():
    """Serve the IDC Research OpenAPI YAML file."""
    yaml_path = os.path.join(os.path.dirname(__file__), "openapi-idc-research.yaml")
    return FileResponse(path=yaml_path, media_type="application/yaml", filename="openapi-idc-research.yaml")


@router.get("/redoc", include_in_schema=False)
async def idc_research_redoc():
    """Serve ReDoc bound to the IDC Research OpenAPI spec (YAML)."""
    # ReDoc prefers JSON, but can accept YAML URL as well; most deployments proxy YAML correctly.
    return get_redoc_html(
        openapi_url="/api/v1/idc-research/docs/openapi.yaml",
        title="IDC Research ReDoc",
    )
