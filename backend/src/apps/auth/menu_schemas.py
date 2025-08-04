"""
菜单相关的数据模式定义
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class MenuCreateRequest(BaseModel):
    """创建菜单请求"""
    menu_name: str = Field(..., min_length=1, max_length=50, description="菜单名称")
    menu_icon: Optional[str] = Field("default", max_length=50, description="菜单图标")
    parent_id: Optional[int] = Field(-1, description="父菜单ID，-1表示根菜单")
    route_path: str = Field(..., min_length=1, max_length=200, description="路由路径")
    redirect_path: Optional[str] = Field("", max_length=200, description="重定向路径")
    menu_component: str = Field(..., min_length=1, max_length=100, description="组件名称")
    show_menu: Optional[int] = Field(1, description="是否显示菜单：1-显示，0-隐藏")
    sort_order: Optional[int] = Field(0, description="排序顺序：数字越小越靠前")


class MenuUpdateRequest(BaseModel):
    """更新菜单请求"""
    menu_name: Optional[str] = Field(None, min_length=1, max_length=50, description="菜单名称")
    menu_icon: Optional[str] = Field(None, max_length=50, description="菜单图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    route_path: Optional[str] = Field(None, min_length=1, max_length=200, description="路由路径")
    redirect_path: Optional[str] = Field(None, max_length=200, description="重定向路径")
    menu_component: Optional[str] = Field(None, min_length=1, max_length=100, description="组件名称")
    show_menu: Optional[int] = Field(None, description="是否显示菜单：1-显示，0-隐藏")
    sort_order: Optional[int] = Field(None, description="排序顺序：数字越小越靠前")


class MenuResponse(BaseModel):
    """菜单响应"""
    id: int = Field(..., description="数据库主键ID")
    menu_id: int = Field(..., description="菜单ID")
    menu_name: str = Field(..., description="菜单名称")
    menu_icon: str = Field(..., description="菜单图标")
    parent_id: int = Field(..., description="父菜单ID")
    route_path: str = Field(..., description="路由路径")
    redirect_path: str = Field(..., description="重定向路径")
    menu_component: str = Field(..., description="组件名称")
    show_menu: int = Field(..., description="是否显示菜单")
    sort_order: int = Field(..., description="排序顺序")
    create_time: Optional[str] = Field(None, description="创建时间")
    update_time: Optional[str] = Field(None, description="更新时间")


class MenuTreeResponse(MenuResponse):
    """菜单树响应"""
    children: List['MenuTreeResponse'] = Field(default_factory=list, description="子菜单")


class MenuListResponse(BaseModel):
    """菜单列表响应"""
    menus: List[MenuTreeResponse] = Field(..., description="菜单树")
    total: int = Field(..., description="菜单总数")


class UserMenuResponse(BaseModel):
    """用户菜单响应"""
    menus: List[MenuTreeResponse] = Field(..., description="用户可访问的菜单树")


# 解决前向引用问题
MenuTreeResponse.model_rebuild()