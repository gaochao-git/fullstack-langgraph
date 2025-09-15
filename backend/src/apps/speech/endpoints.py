"""
语音转文字 API 端点
使用硅基流动 SenseVoiceSmall 进行语音识别
"""
import os
import tempfile
import httpx
from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from ...shared.core.logging import get_logger
from ...shared.schemas.response import success_response, ResponseCode
from ...shared.core.exceptions import BusinessException
from ...shared.core.config import settings

logger = get_logger(__name__)

router = APIRouter(prefix="/speech-to-text", tags=["Speech"])

# 语音 API 配置（从settings获取）
if not settings.AUDIO_API_KEY or not settings.AUDIO_API_BASE_URL or not settings.AUDIO_MODEL_NAME:
    raise ValueError("必须在配置文件中设置 AUDIO_API_KEY, AUDIO_API_BASE_URL 和 AUDIO_MODEL_NAME")

AUDIO_API_KEY = settings.AUDIO_API_KEY
AUDIO_BASE_URL = settings.AUDIO_API_BASE_URL
AUDIO_MODEL_NAME = settings.AUDIO_MODEL_NAME


async def speech_to_text_siliconflow(audio: UploadFile, language: Optional[str] = None):
    """
    使用硅基流动的 SenseVoiceSmall 进行语音识别
    """
    # 检查文件大小（限制 10MB）
    max_size = 10 * 1024 * 1024  # 10MB
    contents = await audio.read()
    if len(contents) > max_size:
        raise BusinessException(
            code=ResponseCode.PARAM_ERROR,
            message="音频文件过大，请限制在 10MB 以内"
        )
    
    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio.filename or ".webm")[1]) as tmp_file:
        tmp_file.write(contents)
        tmp_path = tmp_file.name
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 准备文件上传
            with open(tmp_path, 'rb') as f:
                files = {
                    'file': (audio.filename or 'audio.webm', f, audio.content_type or 'audio/webm')
                }
                
                # 构建请求数据
                data = {
                    'model': AUDIO_MODEL_NAME
                }
                
                if language:
                    # SenseVoiceSmall 支持的语言代码映射
                    lang_map = {
                        'zh': 'zh',
                        'en': 'en', 
                        'ja': 'ja',
                        'ko': 'ko',
                        'yue': 'yue'  # 粤语
                    }
                    if language in lang_map:
                        data['language'] = lang_map[language]
                
                # 调用硅基流动 API
                logger.info(f"调用硅基流动 API 进行语音识别: {audio.filename}")
                response = await client.post(
                    f"{AUDIO_BASE_URL}/audio/transcriptions",
                    headers={
                        "Authorization": f"Bearer {AUDIO_API_KEY}"
                    },
                    files=files,
                    data=data
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"硅基流动 API 错误: {response.status_code} - {error_detail}")
                    raise BusinessException(
                        code=ResponseCode.INTERNAL_ERROR,
                        message=f"语音识别失败: {error_detail}"
                    )
                
                result = response.json()
                text = result.get("text", "").strip()
                
                logger.info(f"语音识别成功，文本长度: {len(text)}")
                
                return success_response({
                    "text": text,
                    "language": language or "auto",
                    "model": AUDIO_MODEL_NAME
                })
                
    except httpx.RequestError as e:
        logger.error(f"网络请求失败: {e}")
        raise BusinessException(
            code=ResponseCode.INTERNAL_ERROR,
            message=f"语音识别请求失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"语音转文字失败: {e}")
        raise BusinessException(
            code=ResponseCode.INTERNAL_ERROR,
            message=f"语音识别失败: {str(e)}"
        )
    finally:
        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass


@router.post("")
async def speech_to_text(
    audio: UploadFile = File(...),
    model: Optional[str] = Form("sensevoice"),
    language: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
):
    """
    将音频文件转换为文本
    
    Args:
        audio: 音频文件（支持格式：wav, mp3, webm, m4a等）
        model: 模型名称（默认 sensevoice）
        language: 语言代码（如 zh, en），不指定则自动检测
        prompt: 可选的提示文本（暂不支持）
    
    Returns:
        转换后的文本
    """
    # 使用硅基流动的 SenseVoiceSmall
    return await speech_to_text_siliconflow(audio, language)


@router.get("/models")
async def list_models():
    """获取可用的语音识别模型列表"""
    models = [
        {
            "id": "sensevoice",
            "name": "SenseVoiceSmall",
            "provider": "SiliconFlow",
            "languages": ["zh", "en", "ja", "ko", "yue"],
            "description": "硅基流动 FunAudioLLM/SenseVoiceSmall 高精度语音识别模型",
            "recommended": True,
            "available": True
        }
    ]
    
    return success_response({
        "models": models,
        "default_model": "sensevoice"
    })


# OpenAI API 兼容接口
@router.post("/v1/audio/transcriptions")
async def openai_compatible_transcription(
    file: UploadFile = File(...),
    model: str = Form("sensevoice"),
    language: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    response_format: Optional[str] = Form("json"),
    temperature: Optional[float] = Form(0),
):
    """
    OpenAI API 兼容的语音转文字接口
    方便直接使用 OpenAI SDK
    """
    # 调用主接口
    result = await speech_to_text(
        audio=file,
        model=model,
        language=language,
        prompt=prompt
    )
    
    # 根据响应格式返回
    if response_format == "text":
        return result["data"]["text"]
    else:
        return result