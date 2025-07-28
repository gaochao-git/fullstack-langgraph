#!/bin/bash
# 模块化测试脚本 - 支持单个模块的独立测试和覆盖率

set -e

# 获取参数
MODULE=$1
REPORT_TYPE=${2:-"terminal"}  # terminal, html, xml

# 检查参数
if [ -z "$MODULE" ]; then
    echo "使用方法: $0 <模块名> [报告类型]"
    echo "模块名: sop, agent, mcp, ai_model, scheduled_task"
    echo "报告类型: terminal, html, xml"
    echo ""
    echo "示例:"
    echo "  $0 sop                  # SOP模块测试，终端报告"
    echo "  $0 sop html            # SOP模块测试，HTML报告"  
    echo "  $0 agent xml           # Agent模块测试，XML报告"
    exit 1
fi

# 验证模块名
VALID_MODULES="sop agent mcp ai_model scheduled_task"
if [[ ! " $VALID_MODULES " =~ " $MODULE " ]]; then
    echo "错误: 无效的模块名 '$MODULE'"
    echo "有效模块: $VALID_MODULES"
    exit 1
fi

echo "🧪 开始测试模块: $MODULE"
echo "📊 报告类型: $REPORT_TYPE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 设置路径
MODULE_SOURCE="src/apps/$MODULE"
MODULE_TEST="src/apps/$MODULE/test"
COVERAGE_FILE=".coverage.$MODULE"

# 检查模块目录是否存在
if [ ! -d "$MODULE_SOURCE" ]; then
    echo "错误: 模块源码目录不存在: $MODULE_SOURCE"
    exit 1
fi

if [ ! -d "$MODULE_TEST" ]; then
    echo "错误: 模块测试目录不存在: $MODULE_TEST"
    exit 1
fi

# 清理之前的覆盖率数据
rm -f "$COVERAGE_FILE"

# 运行测试并收集覆盖率
echo "🏃 运行测试..."
coverage run \
    --rcfile=test/.coveragerc \
    --data-file="$COVERAGE_FILE" \
    --source="$MODULE_SOURCE" \
    -m pytest -c test/pytest.ini "$MODULE_TEST" -v

# 生成报告
case $REPORT_TYPE in
    "html")
        echo "📈 生成HTML报告..."
        coverage html \
            --rcfile=test/.coveragerc \
            --data-file="$COVERAGE_FILE" \
            --include="$MODULE_SOURCE/*" \
            --directory="htmlcov/$MODULE"
        coverage report \
            --rcfile=test/.coveragerc \
            --data-file="$COVERAGE_FILE" \
            --include="$MODULE_SOURCE/*"
        echo "✅ HTML报告已生成: htmlcov/$MODULE/index.html"
        ;;
    "xml")
        echo "📈 生成XML报告..."
        coverage xml \
            --rcfile=test/.coveragerc \
            --data-file="$COVERAGE_FILE" \
            --include="$MODULE_SOURCE/*" \
            -o "coverage.$MODULE.xml"
        coverage report \
            --rcfile=test/.coveragerc \
            --data-file="$COVERAGE_FILE" \
            --include="$MODULE_SOURCE/*"
        echo "✅ XML报告已生成: coverage.$MODULE.xml"
        ;;
    *)
        echo "📈 生成终端报告..."
        coverage report \
            --rcfile=test/.coveragerc \
            --data-file="$COVERAGE_FILE" \
            --include="$MODULE_SOURCE/*"
        ;;
esac

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 模块 $MODULE 测试完成！"

# 清理临时文件
rm -f "$COVERAGE_FILE"