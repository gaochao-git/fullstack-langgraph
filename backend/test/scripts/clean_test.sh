#!/bin/bash
# 清理测试相关文件的脚本

echo "🧹 清理测试相关文件..."

# 清理覆盖率文件
echo "  清理覆盖率数据..."
rm -f .coverage*
rm -rf htmlcov/
rm -f coverage*.xml

# 清理pytest缓存
echo "  清理pytest缓存..."
rm -rf .pytest_cache/
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 清理临时文件
echo "  清理临时文件..."
rm -rf .mypy_cache/
rm -rf .tox/

echo "✅ 清理完成！"