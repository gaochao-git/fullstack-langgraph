"""
API审计中间件
自动记录所有API操作的审计日志
"""

import json
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging import get_logger, request_id_ctx, user_id_ctx, LOCAL_IP


class APIAuditMiddleware(BaseHTTPMiddleware):
    """API审计中间件 - 记录所有API操作"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.audit_logger = get_logger("api_audit")
        self.sensitive_fields = {
            'password', 'passwd', 'pwd', 'secret', 'token', 'key',
            'api_key', 'auth_token', 'refresh_token', 'access_token',
            'credit_card', 'bank_account', 'ssn', 'id_card'
        }
        # 需要审计的HTTP方法
        self.audit_methods = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE'}
        # 排除的路径前缀
        self.exclude_paths = {
            '/docs', '/redoc', '/openapi.json', '/favicon.ico',
            '/health', '/metrics', '/static'
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # 检查是否需要审计
        if not self._should_audit(request):
            return await call_next(request)
        
        # 获取请求信息
        start_time = time.time()
        audit_data = await self._extract_request_data(request)
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 获取响应信息
            response_data = await self._extract_response_data(response)
            
            # 记录审计日志
            await self._log_audit(request, response, audit_data, response_data, process_time)
            
            return response
            
        except Exception as e:
            # 处理中间件级别的异常
            process_time = time.time() - start_time
            
            # 构造错误响应数据
            response_data = {
                'status_code': 500,
                'headers': {},
                'error': str(e)
            }
            
            # 创建一个假的响应对象用于日志记录
            class FakeResponse:
                def __init__(self, status_code):
                    self.status_code = status_code
                    self.headers = {}
            
            fake_response = FakeResponse(500)
            
            # 记录审计日志
            await self._log_audit(request, fake_response, audit_data, response_data, process_time)
            
            # 重新抛出异常，让其他异常处理器处理
            raise
    
    def _should_audit(self, request: Request) -> bool:
        """判断是否需要审计"""
        # 检查HTTP方法
        if request.method not in self.audit_methods:
            return False
        
        # 检查路径排除
        path = request.url.path
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return False
        
        # 对GET请求进行更严格的过滤
        if request.method == 'GET':
            # 只审计包含敏感操作的GET请求
            sensitive_get_patterns = [
                '/admin', '/config', '/user', '/auth', '/token',
                '/download', '/export', '/report'
            ]
            if not any(pattern in path.lower() for pattern in sensitive_get_patterns):
                return False
        
        return True
    
    async def _extract_request_data(self, request: Request) -> Dict[str, Any]:
        """提取请求数据"""
        data = {
            'method': request.method,
            'url': str(request.url),
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'headers': dict(request.headers),
            'client_ip': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent'),
            'content_type': request.headers.get('content-type'),
        }
        
        # 获取请求体
        if request.method in {'POST', 'PUT', 'PATCH'}:
            try:
                body = await request.body()
                if body:
                    content_type = request.headers.get('content-type', '')
                    if 'application/json' in content_type:
                        request_body = json.loads(body.decode())
                        data['request_body'] = self._sanitize_data(request_body)
                    elif 'application/x-www-form-urlencoded' in content_type:
                        # 处理表单数据
                        form_data = {}
                        try:
                            from urllib.parse import parse_qs
                            form_str = body.decode()
                            parsed = parse_qs(form_str)
                            # 简化多值字段
                            for key, values in parsed.items():
                                form_data[key] = values[0] if len(values) == 1 else values
                            data['request_body'] = self._sanitize_data(form_data)
                        except:
                            data['request_body'] = f"<表单数据, 长度: {len(body)}>"
                    elif 'multipart/form-data' in content_type:
                        data['request_body'] = f"<文件上传数据, 长度: {len(body)}>"
                    else:
                        data['request_body'] = f"<{content_type}数据, 长度: {len(body)}>"
            except Exception as e:
                data['request_body'] = f"<无法解析请求体: {str(e)}>"
        
        return data
    
    async def _extract_response_data(self, response: Response) -> Dict[str, Any]:
        """提取响应数据"""
        data = {
            'status_code': response.status_code,
            'headers': dict(response.headers),
        }
        
        # 对于修改操作，尝试提取响应内容
        if hasattr(response, 'body'):
            try:
                if response.headers.get('content-type', '').startswith('application/json'):
                    # 响应体通常不包含敏感信息，但仍需要适当处理
                    data['response_size'] = len(response.body) if response.body else 0
                    data['has_response_body'] = response.body is not None
            except Exception:
                pass
        
        return data
    
    async def _log_audit(
        self, 
        request: Request, 
        response: Response, 
        request_data: Dict[str, Any], 
        response_data: Dict[str, Any],
        process_time: float
    ):
        """记录审计日志"""
        # 提取用户信息
        user_id = (
            request.headers.get('X-User-ID') or 
            request.headers.get('x-user-id') or
            request.headers.get('User-ID') or
            request.headers.get('user-id')
        )
        
        # 如果没有专用的用户ID头，尝试从Authorization中提取
        if not user_id:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                user_id = token[:20] + '...' if len(token) > 20 else token
        
        # 从请求体中提取用户信息（作为备选）
        if not user_id and request_data.get('request_body'):
            body = request_data['request_body']
            if isinstance(body, dict):
                user_id = (
                    body.get('user_id') or 
                    body.get('create_by') or 
                    body.get('update_by')
                )
        
        # 提取资源信息
        resource_info = self._extract_resource_info(request.url.path, request_data.get('request_body'))
        
        # 构建完整的请求URL
        full_url = str(request.url)
        
        # 序列化请求参数（用于日志记录）
        request_params = {}
        if request_data['query_params']:
            request_params['query'] = request_data['query_params']
        if request_data.get('request_body'):
            request_params['body'] = request_data['request_body']
        
        # 构建审计日志
        audit_entry = {
            'resource': resource_info['resource'],
            'resource_id': resource_info['resource_id'],
            'user_id': user_id or 'anonymous',
            'client_ip': request_data['client_ip'],
            'user_agent': request_data.get('user_agent', ''),
            'method': request_data['method'],
            'path': request_data['path'],
            'full_url': full_url,
            'query_params': request_data['query_params'],
            'request_body': request_data.get('request_body'),
            'request_params': json.dumps(request_params, ensure_ascii=False) if request_params else '-',
            'status_code': response_data['status_code'],
            'process_time': f"{process_time:.3f}s",
            'trace_id': request_id_ctx.get() or '-',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'server_ip': LOCAL_IP,
        }
        
        # 记录日志
        log_level = 'WARNING' if response.status_code >= 400 else 'INFO'
        message = f"API请求: {request_data['method']} {resource_info['resource']}"
        if resource_info['resource_id']:
            message += f" (ID: {resource_info['resource_id']})"
        
        getattr(self.audit_logger, log_level.lower())(message, extra=audit_entry)
    
    def _determine_action(self, method: str, path: str, status_code: int) -> str:
        """确定操作类型"""
        if status_code >= 400:
            return f"{method}_FAILED"
        
        action_map = {
            'GET': 'READ',
            'POST': 'CREATE',
            'PUT': 'UPDATE', 
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE'
        }
        return action_map.get(method, method)
    
    def _extract_resource_info(self, path: str, request_body: Any) -> Dict[str, str]:
        """从路径和请求体中提取资源信息"""
        resource_info = {
            'resource': 'unknown',
            'resource_id': None
        }
        
        # 从路径提取资源名称和ID
        path_parts = [p for p in path.split('/') if p]
        
        if len(path_parts) >= 2 and path_parts[0] == 'api':
            # API路径格式: /api/v1/resource/id 或 /api/v1/resource/subresource/id
            if len(path_parts) >= 4:  # /api/v1/resource/id
                resource_info['resource'] = path_parts[2]  # 跳过api/v1
                resource_info['resource_id'] = path_parts[3]
                
                # 处理嵌套资源: /api/v1/mcp/servers/server-id
                if len(path_parts) >= 5:
                    resource_info['resource'] = f"{path_parts[2]}_{path_parts[3]}"  # mcp_servers
                    resource_info['resource_id'] = path_parts[4]  # server-id
            elif len(path_parts) >= 3:  # /api/v1/resource
                resource_info['resource'] = path_parts[2]
            elif len(path_parts) >= 2:
                resource_info['resource'] = path_parts[1]
        else:
            # 直接资源路径: /resource/id
            resource_info['resource'] = path_parts[0] if path_parts else 'root'
            if len(path_parts) >= 2:
                resource_info['resource_id'] = path_parts[1]
        
        # 从请求体中提取ID（用于POST创建操作）
        if not resource_info['resource_id'] and isinstance(request_body, dict):
            for id_field in ['id', 'sop_id', 'user_id', 'template_id']:
                if id_field in request_body:
                    resource_info['resource_id'] = str(request_body[id_field])
                    break
        
        return resource_info
    
    def _sanitize_data(self, data: Any) -> Any:
        """数据脱敏处理"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                key_lower = key.lower()
                if any(sensitive in key_lower for sensitive in self.sensitive_fields):
                    sanitized[key] = self._mask_sensitive_value(value)
                elif isinstance(value, dict):
                    sanitized[key] = self._sanitize_data(value)
                elif isinstance(value, list):
                    sanitized[key] = [self._sanitize_data(item) for item in value]
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        else:
            return data
    
    def _mask_sensitive_value(self, value: Any) -> str:
        """敏感值脱敏"""
        if value is None:
            return None
        
        value_str = str(value)
        if len(value_str) <= 4:
            return "***"
        elif len(value_str) <= 8:
            return value_str[:2] + "***" + value_str[-1:]
        else:
            return value_str[:3] + "***" + value_str[-2:]


# 配置专用的审计日志格式化器
class APIAuditFormatter:
    """API审计日志格式化器"""
    
    @staticmethod
    def format_audit_log(record) -> str:
        """格式化审计日志为结构化格式"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # 提取审计字段
        extra = getattr(record, '__dict__', {})
        action = extra.get('action', 'UNKNOWN')
        resource = extra.get('resource', 'unknown')
        resource_id = extra.get('resource_id', '-')
        user_id = extra.get('user_id', 'anonymous')
        client_ip = extra.get('client_ip', '-')
        status_code = extra.get('status_code', '-')
        process_time = extra.get('process_time', '-')
        trace_id = extra.get('trace_id', '-')
        server_ip = extra.get('server_ip', LOCAL_IP)
        
        # 构建审计格式：时间|操作|资源|资源ID|用户|客户端IP|服务器IP|状态码|处理时间|跟踪ID|消息
        return f"{timestamp}|{action}|{resource}|{resource_id}|{user_id}|{client_ip}|{server_ip}|{status_code}|{process_time}|{trace_id}|{record.getMessage()}"


def setup_api_audit_middleware(app):
    """设置API审计中间件"""
    app.add_middleware(APIAuditMiddleware)
    
    # 为api_audit logger配置专门的处理器
    from .logging import logger_manager
    audit_logger = logger_manager.get_logger("api_audit")
    
    # 这里可以添加专门的审计日志处理器
    # 比如写入专门的审计数据库或文件


"""
使用示例：

# 在main.py中启用
from shared.core.api_audit import setup_api_audit_middleware

def create_app():
    app = FastAPI()
    
    # 设置API审计中间件
    setup_api_audit_middleware(app)
    
    return app

# 审计日志示例输出：
2025-08-01 23:15:00.123|CREATE|sop_templates|SOP-001|user_123|192.168.1.5|192.168.1.100|201|0.156s|req_abc|API操作: CREATE sop_templates (ID: SOP-001)

2025-08-01 23:16:00.456|UPDATE|sop_templates|SOP-002|admin_001|192.168.1.5|192.168.1.100|200|0.089s|req_def|API操作: UPDATE sop_templates (ID: SOP-002)

2025-08-01 23:17:00.789|DELETE|users|user_456|admin_001|192.168.1.5|192.168.1.100|200|0.045s|req_ghi|API操作: DELETE users (ID: user_456)
"""