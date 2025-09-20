#!/usr/bin/env python3
"""
ECharts Interactive Chart Server
基于PyEcharts的交互式图表生成MCP服务器
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from fastmcp import FastMCP
from pyecharts import options as opts
from pyecharts.charts import Line, Bar, Pie, Scatter, HeatMap, Tree
from pyecharts.globals import ThemeType

from ..common.base_config import MCPServerConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("ECharts Interactive Chart Server")

# 加载配置
config = MCPServerConfig('echarts_server')

# 设置生成图表的目录
CHART_DIR = os.path.join(os.path.dirname(__file__), "generated_charts")
os.makedirs(CHART_DIR, exist_ok=True)

@mcp.tool()
async def create_interactive_line_chart(
    data: Dict[str, List[Any]],
    x_field: str = "x",
    y_series: Dict[str, str] = None,
    title: str = "Interactive Line Chart",
    subtitle: str = "",
    x_name: str = "",  # X轴名称
    y_name: str = "",  # Y轴名称
    y_unit: str = "",  # Y轴单位（如 "℃", "%", "MB/s"）
    theme: str = "light",
    enable_zoom: bool = True,
    enable_toolbox: bool = True
) -> str:
    """创建交互式折线图
    
    Args:
        data: 数据字典，如 {"x": [...], "y1": [...], "y2": [...]}
        x_field: X轴字段名
        y_series: Y轴系列配置，如 {"销量": "y1", "利润": "y2"}
        title: 图表标题
        subtitle: 副标题
        x_name: X轴名称（如 "时间"、"日期"）
        y_name: Y轴名称（如 "CPU使用率"、"温度"）
        y_unit: Y轴单位（如 "%"、"℃"、"MB/s"）
        theme: 主题 (light/dark)
        enable_zoom: 是否启用缩放
        enable_toolbox: 是否显示工具箱
    
    Returns:
        HTML文件的URL
    
    示例:
        data = {"time": ["00:00", "01:00"], "cpu": [25, 30]}
        create_interactive_line_chart(
            data, "time", {"CPU": "cpu"}, 
            "CPU监控", x_name="时间", y_name="CPU使用率", y_unit="%"
        )
    """
    try:
        # 创建折线图
        line = Line(init_opts=opts.InitOpts(
            theme=ThemeType.LIGHT if theme == "light" else ThemeType.DARK,
            width="100%",
            height="400px"
        ))
        
        # 添加X轴数据
        line.add_xaxis(data[x_field])
        
        # 添加Y轴系列
        if y_series:
            for series_name, field_name in y_series.items():
                line.add_yaxis(
                    series_name=series_name,
                    y_axis=data[field_name],
                    is_smooth=True,  # 平滑曲线
                    symbol_size=8,   # 点的大小
                    itemstyle_opts=opts.ItemStyleOpts(
                        border_width=2
                    )
                )
        else:
            # 默认添加所有非X轴字段
            for key, values in data.items():
                if key != x_field:
                    line.add_yaxis(key, values)
        
        # 设置全局配置
        global_opts = {
            "title_opts": opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                pos_left="center"
            ),
            "tooltip_opts": opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="cross",
                background_color="rgba(255, 255, 255, 0.9)",
                border_width=1,
                border_color="#ccc",
                textstyle_opts=opts.TextStyleOpts(color="#000")
            ),
            "legend_opts": opts.LegendOpts(
                is_show=True,
                pos_top="10%"
            ),
            "xaxis_opts": opts.AxisOpts(
                name=x_name or x_field,  # 使用指定名称或默认字段名
                name_location="end",
                name_gap=5,
                type_="category",
                boundary_gap=False,
                axislabel_opts=opts.LabelOpts(rotate=45)
            ),
            "yaxis_opts": opts.AxisOpts(
                name=y_name or y_field,  # 使用指定名称或默认字段名
                name_location="end",
                name_gap=10,
                type_="value",
                # 如果有单位，添加到标签格式化器中
                axislabel_opts=opts.LabelOpts(
                    formatter=f"{{value}}{y_unit}" if y_unit else "{value}"
                )
            )
        }
        
        # 添加缩放功能
        if enable_zoom:
            global_opts["datazoom_opts"] = [
                opts.DataZoomOpts(type_="slider", range_start=0, range_end=100),
                opts.DataZoomOpts(type_="inside", range_start=0, range_end=100)
            ]
        
        # 添加工具箱
        if enable_toolbox:
            global_opts["toolbox_opts"] = opts.ToolboxOpts(
                is_show=True,
                feature={
                    "dataZoom": {"show": True, "title": {"zoom": "缩放", "back": "还原"}},
                    "dataView": {"show": True, "title": "数据视图", "readOnly": False},
                    "magicType": {"show": True, "type": ["line", "bar"], "title": {"line": "折线图", "bar": "柱状图"}},
                    "restore": {"show": True, "title": "还原"},
                    "saveAsImage": {"show": True, "title": "保存为图片"}
                }
            )
        
        line.set_global_opts(**global_opts)
        
        # 保存HTML文件
        filename = f"line_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.html"
        filepath = os.path.join(CHART_DIR, filename)
        line.render(filepath)
        
        # 返回可访问的URL
        port = int(os.environ.get('MCP_SERVER_PORT', '3008'))
        static_port = port + 1000  # 静态文件服务器端口
        url = f"http://localhost:{static_port}/{filename}"
        
        # 返回嵌入式iframe
        return f'<iframe src="{url}" width="100%" height="400" frameborder="0"></iframe>'
        
    except Exception as e:
        logger.error(f"创建交互式折线图失败: {str(e)}")
        return f"错误: {str(e)}"

@mcp.tool()
async def create_interactive_bar_chart(
    data: Dict[str, List[Any]],
    x_field: str = "x",
    y_series: Dict[str, str] = None,
    title: str = "Interactive Bar Chart",
    x_name: str = "",
    y_name: str = "",
    y_unit: str = "",
    stack: bool = False,
    theme: str = "light"
) -> str:
    """创建交互式柱状图
    
    Args:
        data: 数据字典
        x_field: X轴字段名
        y_series: Y轴系列配置
        title: 图表标题
        x_name: X轴名称
        y_name: Y轴名称
        y_unit: Y轴单位
        stack: 是否堆叠
        theme: 主题
    
    Returns:
        HTML文件的URL
    """
    try:
        bar = Bar(init_opts=opts.InitOpts(
            theme=ThemeType.LIGHT if theme == "light" else ThemeType.DARK,
            width="100%",
            height="400px"
        ))
        
        bar.add_xaxis(data[x_field])
        
        if y_series:
            for series_name, field_name in y_series.items():
                bar.add_yaxis(
                    series_name=series_name,
                    y_axis=data[field_name],
                    stack="stack" if stack else None,
                    category_gap="50%"
                )
        
        bar.set_global_opts(
            title_opts=opts.TitleOpts(title=title, pos_left="center"),
            tooltip_opts=opts.TooltipOpts(
                trigger="axis",
                axis_pointer_type="shadow"
            ),
            xaxis_opts=opts.AxisOpts(
                name=x_name or x_field,
                name_location="end",
                name_gap=5
            ),
            yaxis_opts=opts.AxisOpts(
                name=y_name or y_field,
                name_location="end",
                name_gap=10,
                axislabel_opts=opts.LabelOpts(
                    formatter=f"{{value}}{y_unit}" if y_unit else "{value}"
                )
            ),
            datazoom_opts=[opts.DataZoomOpts(type_="slider")],
            toolbox_opts=opts.ToolboxOpts(
                feature={
                    "dataZoom": {},
                    "dataView": {},
                    "magicType": {"type": ["line", "bar", "stack", "tiled"]},
                    "restore": {},
                    "saveAsImage": {}
                }
            )
        )
        
        # 保存并返回
        filename = f"bar_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.html"
        filepath = os.path.join(CHART_DIR, filename)
        bar.render(filepath)
        
        port = int(os.environ.get('MCP_SERVER_PORT', '3008'))
        static_port = port + 1000
        url = f"http://localhost:{static_port}/{filename}"
        
        return f'<iframe src="{url}" width="100%" height="400" frameborder="0"></iframe>'
        
    except Exception as e:
        logger.error(f"创建交互式柱状图失败: {str(e)}")
        return f"错误: {str(e)}"

@mcp.tool()
async def create_interactive_pie_chart(
    data: List[Dict[str, Any]],
    name_field: str = "name",
    value_field: str = "value",
    title: str = "Interactive Pie Chart",
    subtitle: str = "",
    theme: str = "light",
    rosetype: str = None,  # None, "radius", or "area"
    radius: List[str] = None  # e.g., ["0%", "75%"] or ["40%", "75%"] for doughnut
) -> str:
    """创建交互式饼图
    
    Args:
        data: 数据列表，如 [{"name": "A", "value": 10}, ...]
        name_field: 名称字段
        value_field: 数值字段
        title: 图表标题
        subtitle: 副标题
        theme: 主题
        rosetype: 玫瑰图类型 (None/'radius'/'area')
        radius: 半径设置，如 ["40%", "75%"] 创建环形图
    
    Returns:
        HTML文件的URL
    """
    try:
        pie = Pie(init_opts=opts.InitOpts(
            theme=ThemeType.LIGHT if theme == "light" else ThemeType.DARK,
            width="100%",
            height="400px"
        ))
        
        # 准备数据
        pie_data = [(d[name_field], d[value_field]) for d in data]
        
        # 设置半径（默认值）
        if radius is None:
            radius = ["0%", "75%"]
        
        pie.add(
            series_name="",
            data_pair=pie_data,
            radius=radius,
            rosetype=rosetype,
            label_opts=opts.LabelOpts(
                formatter="{b}: {c} ({d}%)",
                position="outside"
            ),
            itemstyle_opts=opts.ItemStyleOpts(
                border_radius=10,
                border_color="#fff",
                border_width=2
            )
        )
        
        pie.set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                pos_left="center"
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter="{a} <br/>{b}: {c} ({d}%)"
            ),
            legend_opts=opts.LegendOpts(
                orient="vertical",
                pos_top="15%",
                pos_left="2%"
            ),
            toolbox_opts=opts.ToolboxOpts(
                is_show=True,
                feature={
                    "dataView": {"show": True, "readOnly": False},
                    "restore": {"show": True},
                    "saveAsImage": {"show": True}
                }
            )
        )
        
        # 保存HTML文件
        filename = f"pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.html"
        filepath = os.path.join(CHART_DIR, filename)
        pie.render(filepath)
        
        port = int(os.environ.get('MCP_SERVER_PORT', '3008'))
        static_port = port + 1000
        url = f"http://localhost:{static_port}/{filename}"
        
        return f'<iframe src="{url}" width="100%" height="400" frameborder="0"></iframe>'
        
    except Exception as e:
        logger.error(f"创建交互式饼图失败: {str(e)}")
        return f"错误: {str(e)}"

@mcp.tool()
async def create_interactive_scatter_chart(
    data: List[Dict[str, Any]],
    x_field: str = "x",
    y_field: str = "y",
    size_field: Optional[str] = None,
    category_field: Optional[str] = None,
    title: str = "Interactive Scatter Chart",
    subtitle: str = "",
    theme: str = "light",
    enable_visual_map: bool = False
) -> str:
    """创建交互式散点图
    
    Args:
        data: 数据列表
        x_field: X轴字段名
        y_field: Y轴字段名
        size_field: 点大小字段（可选）
        category_field: 分类字段（可选）
        title: 图表标题
        subtitle: 副标题
        theme: 主题
        enable_visual_map: 是否启用视觉映射
    
    Returns:
        HTML文件的URL
    """
    try:
        scatter = Scatter(init_opts=opts.InitOpts(
            theme=ThemeType.LIGHT if theme == "light" else ThemeType.DARK,
            width="100%",
            height="400px"
        ))
        
        # 根据是否有分类字段来组织数据
        if category_field:
            # 按分类分组
            from collections import defaultdict
            grouped_data = defaultdict(list)
            for item in data:
                grouped_data[item.get(category_field, "未分类")].append(item)
            
            # 为每个分类添加系列
            for category, items in grouped_data.items():
                scatter_data = []
                for item in items:
                    point = [item[x_field], item[y_field]]
                    if size_field and size_field in item:
                        point.append(item[size_field])
                    scatter_data.append(point)
                
                scatter.add_xaxis([item[x_field] for item in items])
                scatter.add_yaxis(
                    series_name=str(category),
                    y_axis=[item[y_field] for item in items],
                    symbol_size=20 if not size_field else None,
                    label_opts=opts.LabelOpts(is_show=False)
                )
        else:
            # 单系列散点图
            scatter_data = []
            for item in data:
                point = [item[x_field], item[y_field]]
                if size_field and size_field in item:
                    point.append(item[size_field])
                scatter_data.append(point)
            
            scatter.add_xaxis([item[x_field] for item in data])
            scatter.add_yaxis(
                series_name="数据",
                y_axis=[item[y_field] for item in data],
                symbol_size=20 if not size_field else None,
                label_opts=opts.LabelOpts(is_show=False)
            )
        
        # 全局配置
        global_opts = {
            "title_opts": opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                pos_left="center"
            ),
            "tooltip_opts": opts.TooltipOpts(
                trigger="item",
                formatter="{a} <br/>{b}: ({c})",
                axis_pointer_type="cross"
            ),
            "xaxis_opts": opts.AxisOpts(
                type_="value",
                splitline_opts=opts.SplitLineOpts(is_show=True)
            ),
            "yaxis_opts": opts.AxisOpts(
                type_="value",
                splitline_opts=opts.SplitLineOpts(is_show=True)
            ),
            "datazoom_opts": [
                opts.DataZoomOpts(type_="slider", xaxis_index=0),
                opts.DataZoomOpts(type_="slider", yaxis_index=0, orient="vertical"),
                opts.DataZoomOpts(type_="inside", xaxis_index=0),
                opts.DataZoomOpts(type_="inside", yaxis_index=0)
            ],
            "toolbox_opts": opts.ToolboxOpts(
                is_show=True,
                feature={
                    "dataZoom": {"show": True},
                    "dataView": {"show": True, "readOnly": False},
                    "restore": {"show": True},
                    "saveAsImage": {"show": True}
                }
            )
        }
        
        # 添加视觉映射
        if enable_visual_map:
            global_opts["visualmap_opts"] = opts.VisualMapOpts(
                type_="continuous",
                pos_left="right",
                pos_top="center",
                min_=0,
                max_=100,
                range_text=["High", "Low"],
                dimension=2 if size_field else 1,
                range_color=["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090", "#fdae61", "#f46d43", "#d73027", "#a50026"]
            )
        
        if category_field:
            global_opts["legend_opts"] = opts.LegendOpts(
                is_show=True,
                pos_top="10%"
            )
        
        scatter.set_global_opts(**global_opts)
        
        # 保存HTML文件
        filename = f"scatter_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.html"
        filepath = os.path.join(CHART_DIR, filename)
        scatter.render(filepath)
        
        port = int(os.environ.get('MCP_SERVER_PORT', '3008'))
        static_port = port + 1000
        url = f"http://localhost:{static_port}/{filename}"
        
        return f'<iframe src="{url}" width="100%" height="400" frameborder="0"></iframe>'
        
    except Exception as e:
        logger.error(f"创建交互式散点图失败: {str(e)}")
        return f"错误: {str(e)}"

@mcp.tool()
async def create_interactive_heatmap_chart(
    data: List[List[Any]],
    x_labels: List[str],
    y_labels: List[str],
    title: str = "Interactive Heatmap",
    subtitle: str = "",
    theme: str = "light",
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    color_scheme: str = "default"
) -> str:
    """创建交互式热力图
    
    Args:
        data: 二维数据数组
        x_labels: X轴标签
        y_labels: Y轴标签
        title: 图表标题
        subtitle: 副标题
        theme: 主题
        min_value: 最小值（用于颜色映射）
        max_value: 最大值（用于颜色映射）
        color_scheme: 颜色方案
    
    Returns:
        HTML文件的URL
    """
    try:
        heatmap = HeatMap(init_opts=opts.InitOpts(
            theme=ThemeType.LIGHT if theme == "light" else ThemeType.DARK,
            width="100%",
            height="400px"
        ))
        
        # 准备热力图数据
        heatmap_data = []
        for i, y_label in enumerate(y_labels):
            for j, x_label in enumerate(x_labels):
                # [x_index, y_index, value]
                heatmap_data.append([j, i, data[i][j]])
        
        # 计算最小最大值
        if min_value is None:
            min_value = min(min(row) for row in data)
        if max_value is None:
            max_value = max(max(row) for row in data)
        
        heatmap.add_xaxis(x_labels)
        heatmap.add_yaxis(
            series_name="热力值",
            yaxis_data=y_labels,
            value=heatmap_data,
            label_opts=opts.LabelOpts(is_show=True, position="inside"),
            itemstyle_opts=opts.ItemStyleOpts(
                border_color="#fff",
                border_width=1
            )
        )
        
        # 设置颜色方案
        if color_scheme == "red_yellow_green":
            colors = ["#313695", "#4575b4", "#74add1", "#abd9e9", "#e0f3f8", "#ffffbf", "#fee090", "#fdae61", "#f46d43", "#d73027", "#a50026"]
        elif color_scheme == "blue_white_red":
            colors = ["#0000FF", "#4169E1", "#87CEEB", "#FFFFFF", "#FFB6C1", "#FF69B4", "#FF0000"]
        else:
            colors = ["#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de"]
        
        heatmap.set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                pos_left="center"
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                formatter="{a} <br/>{b}: {c}"
            ),
            xaxis_opts=opts.AxisOpts(
                type_="category",
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True,
                    areastyle_opts=opts.AreaStyleOpts(opacity=1)
                ),
                axislabel_opts=opts.LabelOpts(rotate=45)
            ),
            yaxis_opts=opts.AxisOpts(
                type_="category",
                splitarea_opts=opts.SplitAreaOpts(
                    is_show=True,
                    areastyle_opts=opts.AreaStyleOpts(opacity=1)
                )
            ),
            visualmap_opts=opts.VisualMapOpts(
                min_=min_value,
                max_=max_value,
                is_calculable=True,
                orient="horizontal",
                pos_left="center",
                pos_top="90%",
                range_color=colors
            ),
            toolbox_opts=opts.ToolboxOpts(
                is_show=True,
                feature={
                    "dataView": {"show": True, "readOnly": False},
                    "restore": {"show": True},
                    "saveAsImage": {"show": True}
                }
            )
        )
        
        # 保存HTML文件
        filename = f"heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.html"
        filepath = os.path.join(CHART_DIR, filename)
        heatmap.render(filepath)
        
        port = int(os.environ.get('MCP_SERVER_PORT', '3008'))
        static_port = port + 1000
        url = f"http://localhost:{static_port}/{filename}"
        
        return f'<iframe src="{url}" width="100%" height="400" frameborder="0"></iframe>'
        
    except Exception as e:
        logger.error(f"创建交互式热力图失败: {str(e)}")
        return f"错误: {str(e)}"

@mcp.tool()
async def create_interactive_tree_chart(
    data: Dict[str, Any],
    title: str = "Interactive Tree Chart",
    subtitle: str = "",
    orient: str = "TB",  # LR, RL, TB, BT
    theme: str = "light",
    layout: str = "orthogonal",  # orthogonal or radial
    symbol: str = "emptyCircle",
    symbol_size: int = 7,
    enable_roam: bool = True,
    initial_tree_depth: Optional[int] = None
) -> str:
    """创建交互式树图（展示层级关系）
    
    Args:
        data: 树形数据，格式如下：
            {
                "name": "根节点",
                "value": 100,  # 可选
                "itemStyle": {  # 可选，自定义节点样式
                    "color": "#ff0000",  # 节点颜色
                    "borderColor": "#000",  # 边框颜色
                    "borderWidth": 2,  # 边框宽度
                    "borderType": "solid",  # 边框类型
                    "shadowBlur": 10,  # 阴影模糊度
                    "shadowColor": "rgba(0,0,0,0.3)"  # 阴影颜色
                },
                "children": [
                    {
                        "name": "子节点1",
                        "value": 50,
                        "itemStyle": {"color": "#00ff00"},  # 子节点颜色
                        "children": [...]
                    },
                    ...
                ]
            }
        title: 图表标题
        subtitle: 副标题
        orient: 树图方向
            - "LR": 从左到右
            - "RL": 从右到左
            - "TB": 从上到下（默认）
            - "BT": 从下到上
        theme: 主题 (light/dark)
        layout: 布局方式
            - "orthogonal": 正交布局（默认）
            - "radial": 径向布局
        symbol: 节点符号
            - "emptyCircle": 空心圆（默认）
            - "circle": 实心圆
            - "rect": 矩形
            - "roundRect": 圆角矩形
            - "triangle": 三角形
            - "diamond": 菱形
        symbol_size: 节点大小
        enable_roam: 是否开启拖拽漫游
        initial_tree_depth: 初始展开层级（None表示全部展开）
    
    Returns:
        HTML文件的URL
    
    示例:
        data = {
            "name": "公司架构",
            "children": [
                {
                    "name": "技术部",
                    "children": [
                        {"name": "前端组", "value": 10},
                        {"name": "后端组", "value": 15}
                    ]
                },
                {
                    "name": "市场部",
                    "children": [
                        {"name": "销售组", "value": 20},
                        {"name": "推广组", "value": 12}
                    ]
                }
            ]
        }
    """
    try:
        # 创建树图
        tree = Tree(init_opts=opts.InitOpts(
            theme=ThemeType.LIGHT if theme == "light" else ThemeType.DARK,
            width="100%",
            height="400px"
        ))
        
        # 添加数据
        tree.add(
            series_name="",
            data=[data],  # Tree 需要列表格式
            orient=orient,
            symbol=symbol,
            symbol_size=symbol_size,
            layout=layout,
            is_roam=enable_roam,
            initial_tree_depth=initial_tree_depth,
            label_opts=opts.LabelOpts(
                position="top" if orient in ["TB", "BT"] else "right",
                vertical_align="middle",
                font_size=12
            ),
            leaves_opts=opts.TreeLeavesOpts(
                label_opts=opts.LabelOpts(
                    position="bottom" if orient in ["TB", "BT"] else "right",
                    vertical_align="middle",
                    font_size=11
                )
            ),
            itemstyle_opts=opts.ItemStyleOpts(
                border_color="#c23531",
                border_width=1
            )
        )
        
        # 设置全局选项
        tree.set_global_opts(
            title_opts=opts.TitleOpts(
                title=title,
                subtitle=subtitle,
                pos_left="center"
            ),
            tooltip_opts=opts.TooltipOpts(
                trigger="item",
                trigger_on="mousemove",
                formatter="{b}: {c}"  # 显示名称和值
            ),
            toolbox_opts=opts.ToolboxOpts(
                is_show=True,
                feature={
                    "dataView": {"show": True, "title": "数据视图", "readOnly": False},
                    "restore": {"show": True, "title": "还原"},
                    "saveAsImage": {"show": True, "title": "保存为图片"}
                }
            )
        )
        
        # 保存HTML文件
        filename = f"tree_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.html"
        filepath = os.path.join(CHART_DIR, filename)
        tree.render(filepath)
        
        # 返回可访问的URL
        port = int(os.environ.get('MCP_SERVER_PORT', '3008'))
        static_port = port + 1000
        url = f"http://localhost:{static_port}/{filename}"
        
        return f'<iframe src="{url}" width="100%" height="400" frameborder="0"></iframe>'
        
    except Exception as e:
        logger.error(f"创建交互式树图失败: {str(e)}")
        return f"错误: {str(e)}"

def start_static_server():
    """启动静态文件服务器"""
    import threading
    import http.server
    import socketserver
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=CHART_DIR, **kwargs)
        
        def end_headers(self):
            # 添加CORS头
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()
    
    port = int(os.environ.get('MCP_SERVER_PORT', '3008'))
    static_port = port + 1000
    
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
    port = int(os.environ.get('MCP_SERVER_PORT', '3008'))
    
    # 运行MCP服务器
    mcp.run(transport='streamable-http', host='0.0.0.0', port=port)