"""
子图可视化工具 - 生成各个子图的详细流程图

注意：程序启动时会自动生成所有子图的图片，通常无需手动运行此脚本。

使用方法（仅用于手动调试）：
1. 直接运行此脚本：python visualize_subgraphs.py
2. 或从项目根目录运行：
   cd /Users/gaochao/gaochao-git/gaochao_repo/fullstack-langgraph/backend
   python -c "
   import sys, os
   sys.path.append(os.getcwd())
   from src.agents.diagnostic_agent.visualize_subgraphs import visualize_all_subgraphs
   visualize_all_subgraphs()
   "

自动生成的文件：
- graph.png - 主图流程图（程序启动时自动生成）
- sop_diagnosis_subgraph.png - SOP诊断子图流程图（程序启动时自动生成）
- general_qa_subgraph.png - 普通问答子图流程图（程序启动时自动生成）
"""

import os
import sys

def save_subgraph_image(graph, filename):
    """保存子图流程图到独立文件"""
    try:
        graph_image = graph.get_graph().draw_mermaid_png()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        graph_image_path = os.path.join(current_dir, f"{filename}.png")
        with open(graph_image_path, "wb") as f:
            f.write(graph_image)
        print(f"✅ {filename}流程图已保存到: {graph_image_path}")
        return graph_image_path
    except Exception as e:
        print(f"❌ {filename}流程图生成失败: {e}")
        return None


def visualize_all_subgraphs():
    """为所有子图生成可视化图片"""
    
    # 确保项目路径在sys.path中
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    # 导入必要的模块
    try:
        from src.agents.diagnostic_agent.sop_diagnosis_subgraph import create_sop_diagnosis_subgraph
        from src.agents.diagnostic_agent.general_qa_subgraph import create_general_qa_subgraph
        from src.agents.diagnostic_agent.main_graph import create_main_graph
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        print("请确保从项目根目录运行此脚本")
        return
    
    print("🎨 开始生成子图流程图...")
    
    # 生成SOP诊断子图
    try:
        sop_subgraph = create_sop_diagnosis_subgraph()
        save_subgraph_image(sop_subgraph, "sop_diagnosis_subgraph")
    except Exception as e:
        print(f"❌ SOP诊断子图生成失败: {e}")
    
    # 生成普通问答子图
    try:
        qa_subgraph = create_general_qa_subgraph()
        save_subgraph_image(qa_subgraph, "general_qa_subgraph")
    except Exception as e:
        print(f"❌ 普通问答子图生成失败: {e}")
    
    # 生成主图（用于对比）
    try:
        main_graph_builder = create_main_graph()
        main_graph = main_graph_builder.compile()
        save_subgraph_image(main_graph, "main_graph_with_subgraphs")
    except Exception as e:
        print(f"❌ 主图生成失败: {e}")
    
    print("🎉 所有流程图生成完成！")
    print("\n📊 生成的流程图文件:")
    print("- sop_diagnosis_subgraph.png - SOP诊断子图流程图")
    print("- general_qa_subgraph.png - 普通问答子图流程图")
    print("- main_graph_with_subgraphs.png - 包含子图的完整主图流程图")


if __name__ == "__main__":
    visualize_all_subgraphs()