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
    
    async def get_problems(
        self,
        host_ids: Optional[List[str]] = None,
        severity_min: int = 0,
        recent_only: bool = True,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        获取当前活跃的问题（异常指标）
        
        Args:
            host_ids: 主机ID列表，为空则获取所有主机
            severity_min: 最小严重级别 (0:未分类, 1:信息, 2:警告, 3:一般, 4:严重, 5:灾难)
            recent_only: 是否只获取最近的问题
            limit: 返回数量限制
            
        Returns:
            问题列表，包含问题详情和相关的监控项信息
        """
        # 首先通过trigger.get获取活跃的触发器
        trigger_params = {
            "output": ["triggerid", "description", "priority", "lastchange", "value"],
            "selectHosts": ["hostid", "host", "name", "status"],
            "selectItems": ["itemid", "name", "key_", "lastvalue", "units"],
            "selectLastEvent": ["eventid", "name", "clock", "severity", "acknowledged"],
            "only_true": 1,  # 只获取当前触发的
            "active": 1,     # 只获取活跃的
            "sortfield": "lastchange",
            "sortorder": "DESC",
            "limit": limit
        }
        
        # 根据严重级别过滤
        if severity_min > 0:
            trigger_params["min_severity"] = severity_min
        
        # 根据主机过滤
        if host_ids:
            trigger_params["hostids"] = host_ids
        
        try:
            triggers = await self._call_api("trigger.get", trigger_params)
            
            # 处理返回数据，转换为问题格式
            severity_names = {
                "0": "未分类",
                "1": "信息",
                "2": "警告", 
                "3": "一般",
                "4": "严重",
                "5": "灾难"
            }
            
            problems = []
            for trigger in triggers:
                # 从触发器构建问题对象
                problem = {}
                
                # 使用lastEvent的信息
                if trigger.get("lastEvent"):
                    event = trigger["lastEvent"][0] if isinstance(trigger["lastEvent"], list) else trigger["lastEvent"]
                    problem["eventid"] = event.get("eventid", "")
                    problem["name"] = event.get("name", trigger.get("description", ""))
                    problem["clock"] = event.get("clock", str(trigger.get("lastchange", "")))
                    problem["severity"] = event.get("severity", trigger.get("priority", "0"))
                    problem["acknowledged"] = event.get("acknowledged", "0")
                else:
                    # 如果没有lastEvent，使用触发器信息
                    problem["eventid"] = f"trigger_{trigger.get('triggerid', '')}"
                    problem["name"] = trigger.get("description", "")
                    problem["clock"] = str(trigger.get("lastchange", ""))
                    problem["severity"] = trigger.get("priority", "0")
                    problem["acknowledged"] = "0"
                
                # 添加严重级别名称
                problem["severity_name"] = severity_names.get(problem["severity"], "未知")
                
                # 添加主机信息
                if trigger.get("hosts"):
                    host = trigger["hosts"][0] if isinstance(trigger["hosts"], list) else trigger["hosts"]
                    problem["hostname"] = host.get("name", host.get("host", ""))
                    problem["hostid"] = host.get("hostid", "")
                    problem["host"] = host.get("host", "")
                    
                    # 获取主机的IP地址
                    if host.get("hostid"):
                        try:
                            # 获取主机接口信息
                            host_params = {
                                "output": ["hostid"],
                                "selectInterfaces": ["ip", "dns", "main", "type"],
                                "hostids": [host["hostid"]]
                            }
                            host_details = await self._call_api("host.get", host_params)
                            if host_details and host_details[0].get("interfaces"):
                                # 找到主接口或第一个接口
                                interfaces = host_details[0]["interfaces"]
                                main_interface = next((i for i in interfaces if i.get("main") == "1"), interfaces[0])
                                if main_interface.get("ip") and main_interface["ip"] != "127.0.0.1":
                                    problem["host_ip"] = main_interface["ip"]
                                elif main_interface.get("dns"):
                                    problem["host_ip"] = main_interface["dns"]
                                else:
                                    problem["host_ip"] = main_interface.get("ip", "")
                            else:
                                problem["host_ip"] = ""
                        except:
                            problem["host_ip"] = ""
                    else:
                        problem["host_ip"] = ""
                else:
                    problem["hostname"] = ""
                    problem["hostid"] = ""
                    problem["host"] = ""
                    problem["host_ip"] = ""
                
                # 添加监控项信息
                if trigger.get("items"):
                    item = trigger["items"][0] if isinstance(trigger["items"], list) else trigger["items"]
                    problem["item_name"] = item.get("name", "")
                    problem["item_key"] = item.get("key_", "")
                    problem["last_value"] = item.get("lastvalue", "")
                    problem["units"] = item.get("units", "")
                else:
                    problem["item_name"] = ""
                    problem["item_key"] = ""
                    problem["last_value"] = ""
                    problem["units"] = ""
                
                # 添加触发器信息
                problem["trigger_description"] = trigger.get("description", "")
                problem["trigger_priority"] = trigger.get("priority", "0")
                problem["triggerid"] = trigger.get("triggerid", "")
                
                problems.append(problem)
            
            logger.info(f"Retrieved {len(problems)} problems from Zabbix")
            return problems
            
        except Exception as e:
            logger.error(f"Failed to get problems from Zabbix: {e}")
            raise BusinessException(
                f"获取Zabbix问题失败: {str(e)}",
                ResponseCode.BAD_GATEWAY
            )
    
    async def get_problem_items(self, limit: int = 1000) -> List[str]:
        """
        获取有问题的监控项key列表
        
        Args:
            limit: 返回数量限制
            
        Returns:
            有问题的监控项key列表（去重）
        """
        problems = await self.get_problems(limit=limit)
        
        # 提取所有有问题的item keys并去重
        item_keys = set()
        for problem in problems:
            item_key = problem.get("item_key", "")
            if item_key:
                item_keys.add(item_key)
        
        # 转换为有序列表
        item_keys_list = sorted(list(item_keys))
        
        logger.info(f"Found {len(item_keys_list)} unique problem item keys")
        return item_keys_list
    
    async def get_hosts(self) -> List[Dict[str, Any]]:
        """
        获取所有监控的主机列表
        
        Returns:
            主机列表
        """
        params = {
            "output": ["hostid", "host", "name", "status"],
            "sortfield": "name"
        }
        
        hosts = await self._call_api("host.get", params)
        
        # 处理返回数据
        for host in hosts:
            # 添加状态描述
            host["status_name"] = "启用" if host.get("status") == "0" else "禁用"
        
        logger.info(f"Retrieved {len(hosts)} hosts from Zabbix")
        return hosts


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