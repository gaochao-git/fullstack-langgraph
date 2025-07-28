#!/bin/bash
# 覆盖率报告生成脚本

set -e

echo "📊 生成项目覆盖率报告..."

# 清理旧的覆盖率数据
echo "🧹 清理旧数据..."
rm -f .coverage*
rm -rf htmlcov/

# 运行所有测试
echo "🏃 运行测试..."
coverage run --rcfile=test/.coveragerc --branch -m pytest -c test/pytest.ini src/apps/

# 生成报告
echo "📈 生成报告..."
coverage report --rcfile=test/.coveragerc
coverage html --rcfile=test/.coveragerc

# 显示总结
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 覆盖率报告生成完成！"
echo ""
echo "📊 终端报告: 见上方输出"
echo "🌐 HTML报告: htmlcov/index.html"
echo ""
echo "快速查看HTML报告:"
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "  open htmlcov/index.html"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "  xdg-open htmlcov/index.html"
else
    echo "  在浏览器中打开 htmlcov/index.html"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"