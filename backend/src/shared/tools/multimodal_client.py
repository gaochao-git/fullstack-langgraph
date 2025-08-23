"""
多模态服务客户端
提供统一的接口调用多模态服务
"""
import httpx
import base64
from typing import Dict, Any, Optional

from src.shared.core.config import settings
from src.shared.core.logging import get_logger
from src.shared.core.exceptions import BusinessException
from src.shared.schemas.response import ResponseCode

logger = get_logger(__name__)


class MultimodalClient:
    """多模态服务客户端"""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or settings.MULTIMODAL_SERVICE_URL
        self.api_key = api_key or settings.MULTIMODAL_SERVICE_API_KEY
        self.timeout = settings.MULTIMODAL_SERVICE_TIMEOUT
        
        if not self.base_url:
            logger.warning("未配置多模态服务 URL")
    
    async def is_available(self) -> bool:
        """检查服务是否可用"""
        if not self.base_url:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"多模态服务健康检查失败: {e}")
            return False
    
    async def process_image(
        self,
        image_data: bytes,
        mode: str = "auto",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理图片内容
        
        Args:
            image_data: 图片二进制数据
            mode: 处理模式 (ocr, ai_vision, auto)
            options: 额外选项
            
        Returns:
            {
                "success": bool,
                "content": str,
                "mode": str,
                "error": str (optional)
            }
        """
        if not self.base_url:
            raise BusinessException(
                "未配置多模态服务 URL",
                ResponseCode.CONFIG_ERROR
            )
        
        # 构建请求
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        # Base64 编码
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # 请求体
        data = {
            "image": base64_image,
            "mode": mode,
            "options": options or {}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/image/extract",
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    logger.error(f"多模态服务返回错误: {response.status_code}")
                    return {
                        "success": False,
                        "content": "",
                        "error": f"服务返回错误: {response.status_code}"
                    }
                
                result = response.json()
                return result
                
        except httpx.TimeoutException:
            logger.error("多模态服务请求超时")
            return {
                "success": False,
                "content": "",
                "error": "请求超时"
            }
        except Exception as e:
            logger.error(f"调用多模态服务失败: {e}")
            return {
                "success": False,
                "content": "",
                "error": str(e)
            }
    
    async def process(
        self,
        content_type: str,
        data: bytes,
        mode: str = "auto",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        通用处理接口
        
        Args:
            content_type: 内容类型 (image, video, audio, document)
            data: 内容二进制数据
            mode: 处理模式
            options: 额外选项
            
        Returns:
            处理结果
        """
        if not self.base_url:
            raise BusinessException(
                "未配置多模态服务 URL",
                ResponseCode.CONFIG_ERROR
            )
        
        # 构建请求
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        # Base64 编码
        base64_data = base64.b64encode(data).decode('utf-8')
        
        # 请求体
        request_data = {
            "type": content_type,
            "data": base64_data,
            "mode": mode,
            "options": options or {}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/process",
                    headers=headers,
                    json=request_data,
                    timeout=self.timeout
                )
                
                if response.status_code != 200:
                    logger.error(f"多模态服务返回错误: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"服务返回错误: {response.status_code}"
                    }
                
                result = response.json()
                return result
                
        except httpx.TimeoutException:
            logger.error("多模态服务请求超时")
            return {
                "success": False,
                "error": "请求超时"
            }
        except Exception as e:
            logger.error(f"调用多模态服务失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 全局客户端实例
multimodal_client = MultimodalClient()


async def extract_image_content(
    image_data: bytes,
    mode: str = "auto",
    options: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    提取图片内容的便捷函数
    
    Args:
        image_data: 图片数据
        mode: 处理模式
        options: 额外选项
        
    Returns:
        提取的文本内容，失败返回 None
    """
    try:
        result = await multimodal_client.process_image(image_data, mode, options)
        if result.get("success"):
            return result.get("content", "")
        else:
            logger.error(f"图片内容提取失败: {result.get('error', '未知错误')}")
            return None
    except Exception as e:
        logger.error(f"调用多模态服务异常: {e}")
        return None