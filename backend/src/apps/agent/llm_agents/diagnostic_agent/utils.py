"""
简化的工具函数 - 只保留编译图所需的基本功能
"""

import os
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


def save_graph_image(graph, filename="graph.png"):
    """保存图结构图像到文件"""
    try:
        graph_image = graph.get_graph().draw_mermaid_png()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        graph_image_path = os.path.join(current_dir, filename)
        with open(graph_image_path, "wb") as f:
            f.write(graph_image)
        print(f"📝图已保存到 {graph_image_path}")
    except Exception as e:
        logger.warning(f"保存图结构图像失败: {e}")


def compile_graph_with_checkpointer(builder, checkpointer_type=None):
    """
    只支持PostgreSQL模式编译图
    Args:
        builder: StateGraph构建器
        checkpointer_type: 保留参数但不再使用
    Returns:
        编译后的graph
    """
    # 只保留PostgreSQL分支
    graph = builder.compile(name="diagnostic-agent")
    # 开发环境下保存图结构图像
    # save_graph_image(graph)
    return graph