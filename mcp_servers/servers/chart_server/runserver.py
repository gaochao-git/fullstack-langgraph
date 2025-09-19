#!/usr/bin/env python3
"""
Chart Visualization MCP Server
基于matplotlib和plotly的图表生成MCP服务器
"""

import json
import logging
import base64
import io
from typing import Dict, Any, Optional, List
import os
from fastmcp import FastMCP
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from ..common.base_config import MCPServerConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("Chart Visualization Server")

# 设置生成图表的目录
CHART_DIR = os.path.join(os.path.dirname(__file__), "generated_charts")
os.makedirs(CHART_DIR, exist_ok=True)

# 加载配置
config = MCPServerConfig('chart_server')

# 设置中文字体支持
# 根据操作系统选择合适的中文字体
import platform
system = platform.system()
if system == 'Darwin':  # macOS
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti SC', 'STHeiti', 'PingFang SC']
elif system == 'Windows':
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun']
else:  # Linux
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']

plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def validate_figsize(figsize: tuple, default: tuple = (10, 6)) -> tuple:
    """验证并限制图表大小
    
    Args:
        figsize: 用户指定的图表大小
        default: 默认大小
    
    Returns:
        验证后的图表大小
    """
    # 定义最小和最大尺寸限制
    MIN_SIZE = 4  # 最小4英寸
    MAX_SIZE = 20  # 最大20英寸
    
    try:
        width, height = figsize
        # 限制在合理范围内
        width = max(MIN_SIZE, min(MAX_SIZE, width))
        height = max(MIN_SIZE, min(MAX_SIZE, height))
        return (width, height)
    except:
        # 如果格式不对，返回默认值
        return default

def save_and_return_url(fig, title: str, chart_type: str = "chart") -> str:
    """保存图表并返回Markdown格式的URL
    
    Args:
        fig: matplotlib figure对象
        title: 图表标题
        chart_type: 图表类型前缀
    
    Returns:
        Markdown格式的图片链接
    """
    import uuid
    from datetime import datetime
    
    # 生成唯一文件名
    filename = f"{chart_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(CHART_DIR, filename)
    
    # 保存图片
    fig.savefig(filepath, format='png', dpi=100)
    plt.close(fig)
    
    # 返回可访问的URL（静态文件服务器端口）
    port = int(os.environ.get('MCP_SERVER_PORT', '3007'))
    static_port = port + 1000  # 静态文件服务器端口
    url = f"http://localhost:{static_port}/{filename}"
    
    # 返回Markdown格式
    return f"![{title}]({url})"

@mcp.tool()
async def create_line_chart(
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    title: str = "Line Chart",
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    style: str = "default",
    color: str = "blue",
    figsize: tuple = (10, 6)
) -> str:
    """创建折线图
    
    Args:
        data: 数据列表，每个元素是包含x和y字段的字典
        x_field: x轴数据字段名
        y_field: y轴数据字段名
        title: 图表标题
        x_label: x轴标签（如果不提供，使用字段名）
        y_label: y轴标签（如果不提供，使用字段名）
        style: matplotlib样式
        color: 线条颜色
        figsize: 图表大小
    
    Returns:
        Markdown格式的图片链接
    """
    try:
        # 设置样式
        if style != "default":
            plt.style.use(style)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 验证图表大小
        validated_figsize = validate_figsize(figsize, default=(10, 6))
        
        # 创建图表
        fig, ax = plt.subplots(figsize=validated_figsize)
        ax.plot(df[x_field], df[y_field], color=color, linewidth=2, marker='o')
        
        # 设置标题和标签
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_label or x_field, fontsize=12)
        ax.set_ylabel(y_label or y_field, fontsize=12)
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存并返回URL
        return save_and_return_url(fig, title, "line_chart")
        
    except Exception as e:
        logger.error(f"创建折线图失败: {str(e)}")
        return f"错误: {str(e)}"

@mcp.tool()
async def create_bar_chart(
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    title: str = "Bar Chart",
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    style: str = "default",
    color: str = "steelblue",
    figsize: tuple = (10, 6),
    orientation: str = "vertical"
) -> str:
    """创建柱状图
    
    Args:
        data: 数据列表
        x_field: x轴数据字段名
        y_field: y轴数据字段名
        title: 图表标题
        x_label: x轴标签
        y_label: y轴标签
        style: matplotlib样式
        color: 柱子颜色
        figsize: 图表大小
        orientation: 方向（vertical或horizontal）
    
    Returns:
        Markdown格式的图片链接
    """
    try:
        if style != "default":
            plt.style.use(style)
        df = pd.DataFrame(data)
        
        # 验证图表大小
        validated_figsize = validate_figsize(figsize, default=(10, 6))
        
        fig, ax = plt.subplots(figsize=validated_figsize)
        
        if orientation == "horizontal":
            ax.barh(df[x_field], df[y_field], color=color)
            ax.set_xlabel(y_label or y_field, fontsize=12)
            ax.set_ylabel(x_label or x_field, fontsize=12)
        else:
            ax.bar(df[x_field], df[y_field], color=color)
            ax.set_xlabel(x_label or x_field, fontsize=12)
            ax.set_ylabel(y_label or y_field, fontsize=12)
            
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y' if orientation == "vertical" else 'x')
        
        plt.tight_layout()
        
        # 保存并返回URL
        return save_and_return_url(fig, title, "bar_chart")
        
    except Exception as e:
        logger.error(f"创建柱状图失败: {str(e)}")
        return f"错误: {str(e)}"

@mcp.tool()
async def create_pie_chart(
    data: List[Dict[str, Any]],
    label_field: str,
    value_field: str,
    title: str = "Pie Chart",
    figsize: tuple = (8, 8),
    autopct: str = '%1.1f%%',
    startangle: int = 90,
    colors: Optional[List[str]] = None
) -> str:
    """创建饼图
    
    Args:
        data: 数据列表
        label_field: 标签字段名
        value_field: 数值字段名
        title: 图表标题
        figsize: 图表大小
        autopct: 百分比格式
        startangle: 起始角度
        colors: 颜色列表
    
    Returns:
        Markdown格式的图片链接
    """
    try:
        df = pd.DataFrame(data)
        
        # 验证图表大小
        validated_figsize = validate_figsize(figsize, default=(8, 8))
        
        fig, ax = plt.subplots(figsize=validated_figsize)
        
        # 使用seaborn调色板如果没有指定颜色
        if colors is None:
            colors = sns.color_palette("husl", len(df))
        
        ax.pie(df[value_field], labels=df[label_field], autopct=autopct,
               startangle=startangle, colors=colors)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        # 保存并返回URL
        return save_and_return_url(fig, title, "pie_chart")
        
    except Exception as e:
        logger.error(f"创建饼图失败: {str(e)}")
        return f"错误: {str(e)}"

@mcp.tool()
async def create_scatter_plot(
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    title: str = "Scatter Plot",
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    style: str = "default",
    color: str = "blue",
    size: int = 50,
    alpha: float = 0.6,
    figsize: tuple = (10, 6)
) -> str:
    """创建散点图
    
    Args:
        data: 数据列表
        x_field: x轴数据字段名
        y_field: y轴数据字段名
        title: 图表标题
        x_label: x轴标签
        y_label: y轴标签
        style: matplotlib样式
        color: 点的颜色
        size: 点的大小
        alpha: 透明度
        figsize: 图表大小
    
    Returns:
        Markdown格式的图片链接
    """
    try:
        if style != "default":
            plt.style.use(style)
        df = pd.DataFrame(data)
        
        # 验证图表大小
        validated_figsize = validate_figsize(figsize, default=(10, 6))
        
        fig, ax = plt.subplots(figsize=validated_figsize)
        ax.scatter(df[x_field], df[y_field], c=color, s=size, alpha=alpha)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_label or x_field, fontsize=12)
        ax.set_ylabel(y_label or y_field, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存并返回URL
        return save_and_return_url(fig, title, "scatter_plot")
        
    except Exception as e:
        logger.error(f"创建散点图失败: {str(e)}")
        return f"错误: {str(e)}"

@mcp.tool()
async def create_heatmap(
    data: List[List[float]],
    x_labels: Optional[List[str]] = None,
    y_labels: Optional[List[str]] = None,
    title: str = "Heatmap",
    cmap: str = "coolwarm",
    annot: bool = True,
    fmt: str = ".2f",
    figsize: tuple = (10, 8)
) -> str:
    """创建热力图
    
    Args:
        data: 二维数据列表
        x_labels: x轴标签列表
        y_labels: y轴标签列表
        title: 图表标题
        cmap: 颜色映射
        annot: 是否显示数值
        fmt: 数值格式
        figsize: 图表大小
    
    Returns:
        Markdown格式的图片链接
    """
    try:
        # 转换为numpy数组
        data_array = np.array(data)
        
        # 验证图表大小
        validated_figsize = validate_figsize(figsize, default=(10, 8))
        
        fig, ax = plt.subplots(figsize=validated_figsize)
        
        # 创建热力图
        sns.heatmap(data_array, annot=annot, fmt=fmt, cmap=cmap,
                    xticklabels=x_labels, yticklabels=y_labels,
                    cbar=True, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        # 保存并返回URL
        return save_and_return_url(fig, title, "heatmap")
        
    except Exception as e:
        logger.error(f"创建热力图失败: {str(e)}")
        return f"错误: {str(e)}"

@mcp.tool()
async def create_multi_series_chart(
    data: Dict[str, List[Dict[str, Any]]],
    x_field: str,
    y_field: str,
    chart_type: str = "line",
    title: str = "Multi-Series Chart",
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    style: str = "default",
    figsize: tuple = (12, 6),
    legend_loc: str = "best"
) -> str:
    """创建多系列图表（支持多条线、多组柱等）
    
    Args:
        data: 字典，key为系列名称，value为该系列的数据列表
        x_field: x轴数据字段名
        y_field: y轴数据字段名
        chart_type: 图表类型（line, bar）
        title: 图表标题
        x_label: x轴标签
        y_label: y轴标签
        style: matplotlib样式
        figsize: 图表大小
        legend_loc: 图例位置
    
    Returns:
        Markdown格式的图片链接
    """
    try:
        if style != "default":
            plt.style.use(style)
        
        # 验证图表大小
        validated_figsize = validate_figsize(figsize, default=(12, 6))
        
        fig, ax = plt.subplots(figsize=validated_figsize)
        
        # 颜色循环
        colors = sns.color_palette("husl", len(data))
        
        for idx, (series_name, series_data) in enumerate(data.items()):
            df = pd.DataFrame(series_data)
            color = colors[idx]
            
            if chart_type == "line":
                ax.plot(df[x_field], df[y_field], label=series_name, 
                       color=color, linewidth=2, marker='o')
            elif chart_type == "bar":
                # 为多系列柱状图调整位置
                x_pos = np.arange(len(df))
                width = 0.8 / len(data)
                offset = width * idx - (width * len(data) / 2) + width / 2
                ax.bar(x_pos + offset, df[y_field], width, label=series_name, color=color)
                if idx == 0:
                    ax.set_xticks(x_pos)
                    ax.set_xticklabels(df[x_field])
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_label or x_field, fontsize=12)
        ax.set_ylabel(y_label or y_field, fontsize=12)
        ax.legend(loc=legend_loc)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存并返回URL
        return save_and_return_url(fig, title, "multi_series_chart")
        
    except Exception as e:
        logger.error(f"创建多系列图表失败: {str(e)}")
        return f"错误: {str(e)}"

def start_static_server():
    """启动静态文件服务器"""
    import threading
    import http.server
    import socketserver
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=CHART_DIR, **kwargs)
        
        def log_message(self, format, *args):
            # 减少日志输出
            pass
    
    port = int(os.environ.get('MCP_SERVER_PORT', '3007'))
    static_port = port + 1000  # 使用 4007 端口提供静态文件
    
    with socketserver.TCPServer(("", static_port), Handler) as httpd:
        logger.info(f"静态文件服务器运行在: http://localhost:{static_port}")
        httpd.serve_forever()

if __name__ == "__main__":
    # 启动静态文件服务器（在后台线程）
    import threading
    static_thread = threading.Thread(target=start_static_server, daemon=True)
    static_thread.start()
    
    # 从环境变量获取端口
    import os
    port = int(os.environ.get('MCP_SERVER_PORT', '3007'))
    
    # 运行MCP服务器
    mcp.run(transport='streamable-http', host='0.0.0.0', port=port)