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

# 加载配置
config = MCPServerConfig('chart_server')

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']  # 如果需要中文，可以改为 'SimHei'
plt.rcParams['axes.unicode_minus'] = False

@mcp.tool()
async def create_line_chart(
    data: List[Dict[str, Any]],
    x_field: str,
    y_field: str,
    title: str = "Line Chart",
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    style: str = "seaborn",
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
        Base64编码的PNG图片字符串
    """
    try:
        # 设置样式
        plt.style.use(style)
        
        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(df[x_field], df[y_field], color=color, linewidth=2, marker='o')
        
        # 设置标题和标签
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_label or x_field, fontsize=12)
        ax.set_ylabel(y_label or y_field, fontsize=12)
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存为Base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
        
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
    style: str = "seaborn",
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
        Base64编码的PNG图片字符串
    """
    try:
        plt.style.use(style)
        df = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=figsize)
        
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
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
        
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
        Base64编码的PNG图片字符串
    """
    try:
        df = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # 使用seaborn调色板如果没有指定颜色
        if colors is None:
            colors = sns.color_palette("husl", len(df))
        
        ax.pie(df[value_field], labels=df[label_field], autopct=autopct,
               startangle=startangle, colors=colors)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
        
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
    style: str = "seaborn",
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
        Base64编码的PNG图片字符串
    """
    try:
        plt.style.use(style)
        df = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=figsize)
        ax.scatter(df[x_field], df[y_field], c=color, s=size, alpha=alpha)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_label or x_field, fontsize=12)
        ax.set_ylabel(y_label or y_field, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
        
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
        Base64编码的PNG图片字符串
    """
    try:
        # 转换为numpy数组
        data_array = np.array(data)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # 创建热力图
        sns.heatmap(data_array, annot=annot, fmt=fmt, cmap=cmap,
                    xticklabels=x_labels, yticklabels=y_labels,
                    cbar=True, ax=ax)
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
        
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
    style: str = "seaborn",
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
        Base64编码的PNG图片字符串
    """
    try:
        plt.style.use(style)
        fig, ax = plt.subplots(figsize=figsize)
        
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
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
        
    except Exception as e:
        logger.error(f"创建多系列图表失败: {str(e)}")
        return f"错误: {str(e)}"

if __name__ == "__main__":
    # 从环境变量获取端口
    import os
    port = int(os.environ.get('MCP_SERVER_PORT', '3007'))
    
    # 运行服务器，使用HTTP模式
    mcp.run(transport='streamable-http', host='0.0.0.0', port=port)