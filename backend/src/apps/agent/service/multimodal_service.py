"""
多模态内容处理服务

支持图片的 AI 视觉识别
"""
import base64
from typing import Dict, Any, Optional
import httpx

from src.shared.core.config import settings
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


class MultimodalService:
    """多模态内容处理服务"""
    
    def __init__(self):
        # 增加超时时间，大模型处理图片需要更长时间
        self.timeout = httpx.Timeout(
            timeout=120.0,  # 总超时时间 120 秒
            connect=10.0,   # 连接超时 10 秒
            read=120.0,     # 读取超时 120 秒
            write=30.0      # 写入超时 30 秒
        )
    
    async def extract_image_content(
        self,
        image_data: bytes,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        提取图片内容
        
        Args:
            image_data: 图片二进制数据
            options: 额外选项
                - prompt: 自定义提示词
            
        Returns:
            {
                "success": bool,
                "content": str,
                "model": str,
                "error": str (optional)
            }
        """
        return await self._process_with_ai_vision(image_data, options)
    
    async def _process_with_ai_vision(
        self,
        image_data: bytes,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用 AI 视觉模型处理图片"""
        try:
            # 获取配置
            prompt = options.get("prompt", "请详细描述这张图片的内容") if options else "请详细描述这张图片的内容"
            
            # 检查是否配置了 API Key
            if not settings.VISION_API_KEY:
                return {
                    "success": False,
                    "mode": "ai_vision",
                    "content": "",
                    "error": "未配置 VISION_API_KEY"
                }
            
            # 将图片转换为 base64
            image_base64 = base64.b64encode(image_data).decode()
            
            # 调用视觉 API（使用 OpenAI 兼容格式）
            return await self._call_vision_api(image_base64, prompt)
            
        except Exception as e:
            logger.error(f"AI 视觉处理失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "content": "",
                "error": f"AI 视觉处理失败: {str(e)}"
            }
    
    async def _call_vision_api(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """调用视觉 API（OpenAI 兼容格式）"""
        try:
            # 记录API调用信息
            logger.info(f"调用视觉 API: {settings.VISION_API_BASE_URL}/chat/completions")
            logger.info(f"使用模型: {settings.VISION_MODEL_NAME}")
            logger.info(f"图片大小: {len(image_base64)} 字符 (base64编码)")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{settings.VISION_API_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.VISION_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": settings.VISION_MODEL_NAME,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 4096
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "content": content,
                        "model": settings.VISION_MODEL_NAME
                    }
                else:
                    error_detail = f"HTTP {response.status_code}"
                    try:
                        error_body = response.json()
                        error_detail = f"HTTP {response.status_code}: {error_body.get('error', {}).get('message', response.text)}"
                    except:
                        error_detail = f"HTTP {response.status_code}: {response.text}"
                    
                    logger.error(f"视觉 API 返回错误: {error_detail}")
                    return {
                        "success": False,
                        "content": "",
                        "error": f"API 调用失败: {error_detail}"
                    }
                    
        except httpx.TimeoutException as e:
            logger.error(f"视觉 API 请求超时: {str(e)}", exc_info=True)
            return {
                "success": False,
                "content": "",
                "error": "API 请求超时，图片处理时间过长。请稍后重试或使用较小的图片。"
            }
        except httpx.ConnectError as e:
            logger.error(f"视觉 API 连接失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "content": "",
                "error": "无法连接到视觉 API 服务器，请检查网络连接。"
            }
        except Exception as e:
            error_msg = str(e) if str(e) else f"{type(e).__name__}"
            logger.error(f"视觉 API 调用失败: {error_msg}", exc_info=True)
            return {
                "success": False,
                "content": "",
                "error": f"API 调用失败: {error_msg}"
            }



# 创建全局实例
multimodal_service = MultimodalService()