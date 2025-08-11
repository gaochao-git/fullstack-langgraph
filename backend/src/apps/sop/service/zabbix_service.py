"""
Zabbix服务集成
用于与Zabbix API交互，获取监控指标等信息
"""
import httpx
import json
from typing import List, Dict, Any, Optional
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException, ResponseCode

logger = get_logger(__name__)


class ZabbixService:
    """Zabbix API服务类"""
    
    def __init__(self, url: str, username: str, password: str):
        """
        初始化Zabbix服务
        
        Args:
            url: Zabbix API URL
            username: 用户名
            password: 密码
        """
        self.url = url
        self.username = username
        self.password = password
        self.auth_token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.login()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.auth_token:
            try:
                await self.logout()
            except Exception as e:
                logger.warning(f"Zabbix logout failed: {e}")
        await self.client.aclose()
        
    async def _call_api(self, method: str, params: Dict[str, Any]) -> Any:
        """
        调用Zabbix API
        
        Args:
            method: API方法名
            params: 参数
            
        Returns:
            API响应结果
        """
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        # 如果有认证token，添加到请求中
        if self.auth_token and method != "user.login":
            request_data["auth"] = self.auth_token
            
        try:
            response = await self.client.post(
                self.url,
                json=request_data,
                headers={"Content-Type": "application/json-rpc"}
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                error_msg = result["error"].get("data", result["error"].get("message", "Unknown error"))
                logger.error(f"Zabbix API error: {error_msg}")
                raise BusinessException(
                    f"Zabbix API错误: {error_msg}",
                    ResponseCode.BAD_GATEWAY
                )
                
            return result.get("result")
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Zabbix API: {e}")
            raise BusinessException(
                f"调用Zabbix API失败: {str(e)}",
                ResponseCode.BAD_GATEWAY
            )
        except Exception as e:
            logger.error(f"Unexpected error calling Zabbix API: {e}")
            raise BusinessException(
                f"Zabbix服务异常: {str(e)}",
                ResponseCode.INTERNAL_ERROR
            )
            
    async def login(self) -> str:
        """
        登录Zabbix获取认证token
        
        Returns:
            认证token
        """
        params = {
            "user": self.username,
            "password": self.password
        }
        
        self.auth_token = await self._call_api("user.login", params)
        logger.info("Successfully logged in to Zabbix")
        return self.auth_token
        
    async def logout(self) -> bool:
        """
        登出Zabbix
        
        Returns:
            是否成功
        """
        if not self.auth_token:
            return True
            
        try:
            await self._call_api("user.logout", {})
            self.auth_token = None
            logger.info("Successfully logged out from Zabbix")
            return True
        except Exception as e:
            logger.error(f"Failed to logout from Zabbix: {e}")
            return False
            
    async def get_items(
        self,
        host_ids: Optional[List[str]] = None,
        search: Optional[Dict[str, str]] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        获取Zabbix监控项
        
        Args:
            host_ids: 主机ID列表，为空则获取所有主机
            search: 搜索条件，如 {"name": "CPU"}
            limit: 返回数量限制
            
        Returns:
            监控项列表
        """
        params = {
            "output": ["itemid", "name", "key_", "hostid", "status", "value_type", "units"],
            "selectHosts": ["hostid", "host", "name"],
            "sortfield": "name",
            "limit": limit
        }
        
        if host_ids:
            params["hostids"] = host_ids
            
        if search:
            params["search"] = search
            
        items = await self._call_api("item.get", params)
        
        # 处理返回数据，添加主机名称
        for item in items:
            if item.get("hosts"):
                item["hostname"] = item["hosts"][0].get("name", item["hosts"][0].get("host", ""))
            else:
                item["hostname"] = ""
                
        logger.info(f"Retrieved {len(items)} items from Zabbix")
        return items
        
    async def get_items_by_keys(self, item_keys: List[str]) -> List[Dict[str, Any]]:
        """
        根据item key列表获取监控项详细信息
        
        Args:
            item_keys: item key列表
            
        Returns:
            监控项列表
        """
        if not item_keys:
            return []
            
        params = {
            "output": ["itemid", "name", "key_", "hostid", "status", "value_type", "units"],
            "selectHosts": ["hostid", "host", "name"],
            "filter": {
                "key_": item_keys
            }
        }
        
        items = await self._call_api("item.get", params)
        
        # 处理返回数据
        for item in items:
            if item.get("hosts"):
                item["hostname"] = item["hosts"][0].get("name", item["hosts"][0].get("host", ""))
            else:
                item["hostname"] = ""
                
        return items
        
    async def get_common_items(self) -> List[Dict[str, str]]:
        """
        获取常用的监控项列表（用于前端选择）
        
        Returns:
            格式化的监控项列表，包含 value 和 label
        """
        # 定义常用的监控项搜索条件
        common_searches = [
            {"name": "CPU"},
            {"name": "Memory"},
            {"name": "Disk"},
            {"name": "Network"},
            {"key_": "mysql"},
            {"key_": "redis"},
            {"key_": "nginx"},
            {"key_": "apache"},
            {"key_": "system"},
            {"key_": "vfs"},
            {"key_": "vm"},
            {"key_": "net"},
            {"key_": "proc"}
        ]
        
        all_items = []
        seen_keys = set()
        
        # 分批获取不同类型的监控项
        for search in common_searches:
            try:
                items = await self.get_items(search=search, limit=100)
                for item in items:
                    key = item["key_"]
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_items.append({
                            "value": key,
                            "label": key
                        })
            except Exception as e:
                logger.warning(f"Failed to get items for search {search}: {e}")
                
        # 按key排序
        all_items.sort(key=lambda x: x["value"])
        
        logger.info(f"Retrieved {len(all_items)} common items from Zabbix")
        return all_items


# 单例实例管理
_zabbix_service: Optional[ZabbixService] = None


def get_zabbix_service() -> ZabbixService:
    """
    获取Zabbix服务实例（单例）
    
    Returns:
        ZabbixService实例
    """
    global _zabbix_service
    
    if _zabbix_service is None:
        # 从配置中读取Zabbix连接信息
        # TODO: 从配置文件或环境变量读取
        url = "http://82.156.146.51:8080/zabbix/api_jsonrpc.php"
        username = "Admin"
        password = "zabbix"
        
        _zabbix_service = ZabbixService(url, username, password)
        
    return _zabbix_service