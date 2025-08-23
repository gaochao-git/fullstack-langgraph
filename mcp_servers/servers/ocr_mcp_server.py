#!/usr/bin/env python3
"""
OCR MCP Server - 提供 OCR 文字识别功能

功能：
1. 从图片中提取文字
2. 支持多语言识别
3. 返回文字和置信度
"""

import asyncio
import base64
import io
import logging
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from pydantic import AnyUrl

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Warning: pytesseract or PIL not installed. OCR functionality will be limited.")

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建服务器实例
server = Server("ocr-server")


# OCR 工具定义
OCR_EXTRACT_TEXT_TOOL = Tool(
    name="ocr_extract_text",
    description="使用 OCR 从图片中提取文字。支持多种语言。",
    inputSchema={
        "type": "object",
        "properties": {
            "image_data": {
                "type": "string",
                "description": "Base64 编码的图片数据"
            },
            "language": {
                "type": "string",
                "description": "OCR 语言代码，如 'eng' (英文), 'chi_sim' (简体中文), 'chi_sim+eng' (中英混合)",
                "default": "eng"
            },
            "return_confidence": {
                "type": "boolean",
                "description": "是否返回置信度信息",
                "default": False
            }
        },
        "required": ["image_data"]
    }
)

OCR_DETECT_TEXT_TOOL = Tool(
    name="ocr_detect_text",
    description="检测图片中是否包含文字，并返回文字区域信息",
    inputSchema={
        "type": "object",
        "properties": {
            "image_data": {
                "type": "string",
                "description": "Base64 编码的图片数据"
            }
        },
        "required": ["image_data"]
    }
)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出可用的 OCR 工具"""
    if not OCR_AVAILABLE:
        return []
    return [OCR_EXTRACT_TEXT_TOOL, OCR_DETECT_TEXT_TOOL]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """处理工具调用"""
    
    if not OCR_AVAILABLE:
        return [TextContent(
            type="text",
            text="OCR 功能不可用。请安装 pytesseract 和 pillow: pip install pytesseract pillow"
        )]
    
    try:
        if name == "ocr_extract_text":
            return await handle_extract_text(arguments)
        elif name == "ocr_detect_text":
            return await handle_detect_text(arguments)
        else:
            return [TextContent(
                type="text",
                text=f"未知的工具: {name}"
            )]
    except Exception as e:
        logger.error(f"OCR 工具调用失败: {str(e)}")
        return [TextContent(
            type="text",
            text=f"OCR 处理失败: {str(e)}"
        )]


async def handle_extract_text(arguments: dict) -> Sequence[TextContent]:
    """处理文字提取请求"""
    try:
        # 解码图片
        image_data = base64.b64decode(arguments["image_data"])
        image = Image.open(io.BytesIO(image_data))
        
        # OCR 参数
        language = arguments.get("language", "eng")
        return_confidence = arguments.get("return_confidence", False)
        
        # 执行 OCR
        if return_confidence:
            # 获取详细信息
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            
            # 提取有效文字和置信度
            words = []
            confidences = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                conf = float(data['conf'][i])
                if text and conf > 0:
                    words.append(text)
                    confidences.append(conf)
            
            # 计算平均置信度
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            result = {
                "text": " ".join(words),
                "word_count": len(words),
                "average_confidence": round(avg_confidence, 2),
                "language": language
            }
            
            return [TextContent(
                type="text",
                text=f"提取的文字内容：\n{result['text']}\n\n统计信息：\n- 词数：{result['word_count']}\n- 平均置信度：{result['average_confidence']}%\n- 语言：{result['language']}"
            )]
        else:
            # 简单提取文字
            text = pytesseract.image_to_string(image, lang=language)
            
            return [TextContent(
                type="text",
                text=f"提取的文字内容：\n{text.strip()}"
            )]
            
    except Exception as e:
        logger.error(f"文字提取失败: {str(e)}")
        return [TextContent(
            type="text",
            text=f"文字提取失败: {str(e)}"
        )]


async def handle_detect_text(arguments: dict) -> Sequence[TextContent]:
    """检测图片中的文字区域"""
    try:
        # 解码图片
        image_data = base64.b64decode(arguments["image_data"])
        image = Image.open(io.BytesIO(image_data))
        
        # 获取文字框信息
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # 统计文字区域
        text_regions = []
        total_words = 0
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if text:
                total_words += 1
                text_regions.append({
                    "text": text,
                    "left": data['left'][i],
                    "top": data['top'][i],
                    "width": data['width'][i],
                    "height": data['height'][i],
                    "confidence": data['conf'][i]
                })
        
        if total_words > 0:
            # 计算文字覆盖区域
            min_left = min(r['left'] for r in text_regions)
            min_top = min(r['top'] for r in text_regions)
            max_right = max(r['left'] + r['width'] for r in text_regions)
            max_bottom = max(r['top'] + r['height'] for r in text_regions)
            
            coverage_area = (max_right - min_left) * (max_bottom - min_top)
            image_area = image.width * image.height
            coverage_percent = (coverage_area / image_area) * 100
            
            result = f"检测到文字：是\n"
            result += f"文字数量：{total_words} 个词\n"
            result += f"文字覆盖率：{coverage_percent:.1f}%\n"
            result += f"文字区域：({min_left}, {min_top}) - ({max_right}, {max_bottom})\n"
            result += f"图片尺寸：{image.width} x {image.height}"
        else:
            result = "检测到文字：否\n图片中未检测到文字内容。"
        
        return [TextContent(
            type="text",
            text=result
        )]
        
    except Exception as e:
        logger.error(f"文字检测失败: {str(e)}")
        return [TextContent(
            type="text",
            text=f"文字检测失败: {str(e)}"
        )]


async def main():
    """主函数"""
    # 使用 stdio 传输
    from mcp.server.stdio import stdio_server
    
    logger.info("启动 OCR MCP 服务器...")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ocr-server",
                server_version="0.1.0"
            )
        )


if __name__ == "__main__":
    asyncio.run(main())