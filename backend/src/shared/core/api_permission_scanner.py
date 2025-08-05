"""
API权限自动扫描器
在应用启动时自动扫描所有FastAPI路由并同步到权限表
"""

import re
from typing import List, Dict, Any, Set, Optional
from fastapi import FastAPI
from fastapi.routing import APIRoute, APIRouter
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

try:
    from src.shared.core.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class APIPermission:
    """API权限数据结构"""
    permission_name: str
    permission_description: str
    http_method: str
    route_path: str
    tags: List[str]
    summary: str = ""
    deprecated: bool = False


class APIPermissionScanner:
    """API权限扫描器"""
    
    def __init__(self):
        self.permissions: List[APIPermission] = []
        self.excluded_paths: Set[str] = {
            "/docs", "/redoc", "/openapi.json", "/health", "/version",
            "/api/health", "/api/version"
        }
        self.excluded_patterns: List[str] = [
            r"^/static/.*",  # 静态文件
            r"^/favicon\.ico$",  # favicon
            r".*/__pycache__/.*",  # Python缓存
        ]
    
    def should_exclude_route(self, path: str) -> bool:
        """检查路由是否应该被排除"""
        # 检查完全匹配的排除路径
        if path in self.excluded_paths:
            return True
        
        # 检查正则表达式匹配的排除模式
        for pattern in self.excluded_patterns:
            if re.match(pattern, path):
                return True
        
        return False
    
    def extract_route_info(self, route: APIRoute) -> Optional[APIPermission]:
        """从FastAPI路由中提取权限信息"""
        try:
            # 获取路由基本信息
            path = route.path
            methods = route.methods
            
            # 排除不需要的路由
            if self.should_exclude_route(path):
                return None
            
            # 获取路由元数据
            summary = getattr(route, 'summary', '') or ''
            description = getattr(route, 'description', '') or summary
            tags = getattr(route, 'tags', []) or []
            deprecated = getattr(route, 'deprecated', False)
            
            # 为每个HTTP方法创建一个权限条目
            permissions = []
            for method in methods:
                if method in ['HEAD', 'OPTIONS']:  # 跳过这些方法
                    continue
                
                # 生成权限名称（直接使用路径，HTTP方法单独存储）
                permission_name = path
                
                # 生成权限描述
                if summary:
                    permission_desc = f"{summary} ({method})"
                else:
                    permission_desc = f"{method} {path}"
                
                permission = APIPermission(
                    permission_name=permission_name,
                    permission_description=permission_desc,
                    http_method=method,
                    route_path=path,
                    tags=tags,
                    summary=summary,
                    deprecated=deprecated
                )
                permissions.append(permission)
            
            return permissions
            
        except Exception as e:
            logger.error(f"提取路由信息失败: {route.path} - {e}")
            return None
    
    def scan_fastapi_routes(self, app: FastAPI) -> List[APIPermission]:
        """扫描FastAPI应用的所有路由"""
        self.permissions = []
        
        def scan_routes(routes, prefix: str = ""):
            """递归扫描路由"""
            for route in routes:
                if isinstance(route, APIRoute):
                    # 处理单个路由
                    full_path = prefix + route.path
                    route.path = full_path  # 临时设置完整路径
                    
                    permissions = self.extract_route_info(route)
                    if permissions:
                        if isinstance(permissions, list):
                            self.permissions.extend(permissions)
                        else:
                            self.permissions.append(permissions)
                    
                    route.path = route.path.replace(prefix, "")  # 恢复原路径
                
                elif hasattr(route, 'routes'):
                    # 处理子路由器
                    sub_prefix = prefix
                    if hasattr(route, 'prefix') and route.prefix:
                        sub_prefix += route.prefix
                    scan_routes(route.routes, sub_prefix)
        
        # 开始扫描
        scan_routes(app.routes)
        
        logger.info(f"扫描完成，发现 {len(self.permissions)} 个API权限")
        return self.permissions
    
    async def sync_permissions_to_db(self, db) -> Dict[str, int]:
        """将扫描到的权限同步到数据库"""
        stats = {"created": 0, "updated": 0, "skipped": 0, "orphaned": 0}
        
        try:
            # 获取现有权限
            existing_permissions = {}
            result = await db.execute(
                "SELECT permission_name, permission_id, permission_description, http_method FROM rbac_permissions WHERE is_deleted = 0"
            )
            for row in result.fetchall():
                existing_permissions[row[0]] = {
                    "permission_id": row[1],
                    "permission_description": row[2], 
                    "http_method": row[3]
                }
            
            # 收集当前代码中的权限名称
            code_permissions = {perm.permission_name for perm in self.permissions}
            
            # 检查数据库中是否有代码中不存在的权限（孤立权限）
            for db_perm_name in existing_permissions.keys():
                if db_perm_name not in code_permissions:
                    stats["orphaned"] += 1
                    logger.warning(f"⚠️ 数据库中存在但代码中不存在的权限: {db_perm_name}")
            
            # 只处理代码中存在的权限
            for permission in self.permissions:
                permission_name = permission.permission_name
                
                if permission_name in existing_permissions:
                    # 权限已存在，跳过（不更新现有权限描述）
                    stats["skipped"] += 1
                else:
                    # 创建新权限（只添加代码中有但表中没有的）
                    # 获取下一个权限ID
                    result = await db.execute("SELECT COALESCE(MAX(permission_id), 0) + 1 FROM rbac_permissions")
                    next_permission_id = result.scalar()
                    
                    await db.execute(
                        """INSERT INTO rbac_permissions 
                           (permission_id, permission_name, permission_description, http_method, 
                            release_disable, create_by, update_by) 
                           VALUES (:pid, :name, :desc, :method, 'off', 'api_scanner', 'api_scanner')""",
                        {
                            "pid": next_permission_id,
                            "name": permission_name,
                            "desc": permission.permission_description,
                            "method": permission.http_method
                        }
                    )
                    stats["created"] += 1
                    logger.info(f"➕ 新增权限: {permission_name}")
            
            await db.commit()
            
            # 汇总日志
            logger.info(f"✅ 权限同步完成: 新增 {stats['created']}, 跳过 {stats['skipped']}")
            if stats["orphaned"] > 0:
                logger.warning(f"⚠️ 发现 {stats['orphaned']} 个孤立权限（数据库有但代码中不存在）")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"权限同步失败: {e}")
            raise
        
        return stats
    
    async def sync_permissions_to_db(self, db: AsyncSession) -> Dict[str, int]:
        """将扫描到的权限同步到数据库"""
        stats = {"created": 0, "skipped": 0, "orphaned": 0}
        
        try:
            # 获取数据库中现有权限（按权限名称+HTTP方法组合）
            result = await db.execute(
                text("SELECT permission_name, permission_id, permission_description, http_method FROM rbac_permissions WHERE is_deleted = 0")
            )
            existing_permissions = set()
            db_permissions = {}
            
            for row in result.fetchall():
                permission_name = row[0]
                http_method = row[3]
                # 使用权限名称+HTTP方法作为唯一标识
                permission_key = f"{permission_name}:{http_method}"
                existing_permissions.add(permission_key)
                db_permissions[permission_key] = {
                    "permission_id": row[1],
                    "permission_description": row[2],
                    "http_method": http_method,
                    "permission_name": permission_name
                }
            
            # 收集代码中的权限（权限名称+HTTP方法组合）
            code_permissions = set()
            for perm in self.permissions:
                permission_key = f"{perm.permission_name}:{perm.http_method}"
                code_permissions.add(permission_key)
            
            # 检查孤立权限（数据库中有但代码中没有）
            orphaned_permissions = existing_permissions - code_permissions
            for orphaned_perm in orphaned_permissions:
                stats["orphaned"] += 1
                logger.warning(f"⚠️ 数据库中存在但代码中不存在的权限: {orphaned_perm}")
            
            # 只添加代码中有但表中没有的权限
            for permission in self.permissions:
                permission_key = f"{permission.permission_name}:{permission.http_method}"
                
                if permission_key in existing_permissions:
                    # 权限已存在，跳过
                    stats["skipped"] += 1
                else:
                    # 创建新权限
                    await self._create_permission(db, permission)
                    stats["created"] += 1
                    logger.info(f"➕ 新增权限: {permission.permission_name} ({permission.http_method})")
            
            await db.commit()
            
            # 汇总日志
            logger.info(f"✅ 权限同步完成: 新增 {stats['created']}, 跳过 {stats['skipped']}")
            if stats["orphaned"] > 0:
                logger.warning(f"⚠️ 发现 {stats['orphaned']} 个孤立权限（数据库有但代码中不存在）")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"❌ 权限同步失败: {e}")
            raise
        
        return stats
    
    async def _create_permission(self, db: AsyncSession, permission: APIPermission):
        """创建新权限记录"""
        # 获取下一个权限ID
        result = await db.execute(text("SELECT COALESCE(MAX(permission_id), 0) + 1 FROM rbac_permissions"))
        next_permission_id = result.scalar()
        
        await db.execute(
            text("""INSERT INTO rbac_permissions 
               (permission_id, permission_name, permission_description, http_method, 
                release_disable, create_by, update_by) 
               VALUES (:pid, :name, :desc, :method, 'off', 'api_scanner', 'api_scanner')"""),
            {
                "pid": next_permission_id,
                "name": permission.permission_name,
                "desc": permission.permission_description,
                "method": permission.http_method
            }
        )

    async def scan_and_sync(self, app: FastAPI) -> Dict[str, int]:
        """扫描并同步API权限到数据库"""
        logger.info("开始扫描API权限...")
        
        # 扫描路由
        self.scan_fastapi_routes(app)
        
        # 需要在调用处提供数据库连接
        try:
            from src.shared.db.config import get_async_db
            async for db in get_async_db():
                try:
                    return await self.sync_permissions_to_db(db)
                finally:
                    await db.close()
        except ImportError:
            logger.error("数据库模块未找到，跳过权限同步")
            return {"created": 0, "skipped": 0, "orphaned": 0}


# 全局扫描器实例
api_permission_scanner = APIPermissionScanner()


async def scan_and_sync_api_permissions(app: FastAPI) -> Dict[str, int]:
    """
    扫描并同步API权限到数据库
    在应用启动时调用
    """
    try:
        return await api_permission_scanner.scan_and_sync(app)
    except Exception as e:
        logger.error(f"API权限扫描失败: {e}")
        return {"created": 0, "skipped": 0, "orphaned": 0}


def get_all_api_permissions(app: FastAPI) -> List[Dict[str, Any]]:
    """
    获取所有API权限信息（不写入数据库）
    用于调试和查看
    """
    scanner = APIPermissionScanner()
    permissions = scanner.scan_fastapi_routes(app)
    
    return [
        {
            "permission_name": p.permission_name,
            "permission_description": p.permission_description,
            "http_method": p.http_method,
            "route_path": p.route_path,
            "tags": p.tags,
            "summary": p.summary,
            "deprecated": p.deprecated
        }
        for p in permissions
    ]