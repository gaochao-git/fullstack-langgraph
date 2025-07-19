"""
简化的工具函数 - 只保留编译图所需的基本功能
"""

import os
import logging

logger = logging.getLogger(__name__)


def save_graph_image(graph, mode_name, filename="graph.png"):
    """保存图结构图像到文件"""
    try:
        graph_image = graph.get_graph().draw_mermaid_png()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        graph_image_path = os.path.join(current_dir, filename)
        with open(graph_image_path, "wb") as f:
            f.write(graph_image)
        print(f"📝 {mode_name}：图已保存到 {graph_image_path}")
    except Exception as e:
        logger.warning(f"保存图结构图像失败: {e}")


def compile_graph_with_checkpointer(builder, checkpointer_type="memory"):
    """
    根据checkpointer类型编译图
    
    Args:
        builder: StateGraph构建器
        checkpointer_type: checkpointer类型 ("memory" 或 "postgres")
        
    Returns:
        编译后的graph
    """
    if checkpointer_type == "postgres":
        # PostgreSQL模式：不在这里编译，在API请求时用async with编译
        graph = builder.compile(name="diagnostic-agent")
        save_graph_image(graph, "PostgreSQL模式")
        graph = None
        print("📝 PostgreSQL模式：图将在API请求时用async with编译")
        return graph
    else:
        # 内存模式：直接使用MemorySaver
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        graph = builder.compile(checkpointer=checkpointer, name="diagnostic-agent")
        save_graph_image(graph, "内存模式")
        print(f"📝 内存模式：图已编译完成")
        return graph