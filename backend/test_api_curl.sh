#!/bin/bash

# Scheduled Task API 接口测试脚本
# 使用curl命令测试所有API端点

echo "========================================"
echo "Scheduled Task API 接口测试"
echo "========================================"

# 设置API基础URL
BASE_URL="http://localhost:8000/api/v1"
API_PREFIX="/scheduled-tasks"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "\n${YELLOW}测试: ${description}${NC}"
    echo "请求: $method $BASE_URL$endpoint"
    
    if [ -n "$data" ]; then
        echo "数据: $data"
        response=$(curl -s -X $method \
            -H "Content-Type: application/json" \
            -d "$data" \
            -w "HTTP_STATUS:%{http_code}" \
            "$BASE_URL$endpoint")
    else
        response=$(curl -s -X $method \
            -w "HTTP_STATUS:%{http_code}" \
            "$BASE_URL$endpoint")
    fi
    
    # 提取HTTP状态码
    http_status=$(echo "$response" | grep -o "HTTP_STATUS:[0-9]*" | cut -d: -f2)
    response_body=$(echo "$response" | sed 's/HTTP_STATUS:[0-9]*$//')
    
    # 根据状态码显示结果
    if [ "$http_status" -ge 200 ] && [ "$http_status" -lt 300 ]; then
        echo -e "${GREEN}✅ 成功 (状态码: $http_status)${NC}"
    elif [ "$http_status" -ge 400 ] && [ "$http_status" -lt 500 ]; then
        echo -e "${YELLOW}⚠️  客户端错误 (状态码: $http_status)${NC}"
    elif [ "$http_status" -ge 500 ]; then
        echo -e "${RED}❌ 服务器错误 (状态码: $http_status)${NC}"
    else
        echo -e "${RED}❌ 连接失败或未知错误${NC}"
    fi
    
    # 显示响应内容（格式化JSON，如果是JSON的话）
    if echo "$response_body" | python3 -m json.tool >/dev/null 2>&1; then
        echo "响应:"
        echo "$response_body" | python3 -m json.tool | head -20
    else
        echo "响应: $response_body"
    fi
    
    echo "----------------------------------------"
}

# 检查服务器是否运行
echo "检查服务器连接..."
if curl -s "$BASE_URL/health" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ 服务器连接正常${NC}"
else
    echo -e "${RED}❌ 无法连接到服务器 ($BASE_URL)${NC}"
    echo "请确保FastAPI服务器正在运行在 http://localhost:8000"
    echo "启动命令: uvicorn src.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi

# 1. 获取任务列表
test_api "GET" "$API_PREFIX" "" "获取定时任务列表"

# 2. 获取任务列表（带参数）
test_api "GET" "$API_PREFIX?skip=0&limit=5&enabled_only=true" "" "获取启用的任务列表（分页）"

# 3. 获取单个任务详情
test_api "GET" "$API_PREFIX/1" "" "获取ID为1的任务详情"

# 4. 获取不存在的任务
test_api "GET" "$API_PREFIX/999" "" "获取不存在的任务（测试404）"

# 5. 创建新任务
create_task_data='{
    "task_name": "api_test_task",
    "task_path": "app.tasks.api_test_task",
    "task_description": "通过API创建的测试任务",
    "task_interval": 300,
    "task_args": "[]",
    "task_kwargs": "{}",
    "task_enabled": true
}'
test_api "POST" "$API_PREFIX" "$create_task_data" "创建新的定时任务"

# 6. 创建任务（无效数据）
invalid_task_data='{
    "task_name": "invalid_task",
    "task_path": "",
    "task_args": "invalid json"
}'
test_api "POST" "$API_PREFIX" "$invalid_task_data" "创建任务（无效数据，测试验证）"

# 7. 更新任务
update_task_data='{
    "task_description": "更新后的任务描述",
    "task_enabled": false
}'
test_api "PUT" "$API_PREFIX/1" "$update_task_data" "更新ID为1的任务"

# 8. 更新不存在的任务
test_api "PUT" "$API_PREFIX/999" "$update_task_data" "更新不存在的任务（测试404）"

# 9. 启用任务
test_api "POST" "$API_PREFIX/1/enable" "" "启用ID为1的任务"

# 10. 禁用任务
test_api "POST" "$API_PREFIX/1/disable" "" "禁用ID为1的任务"

# 11. 启用不存在的任务
test_api "POST" "$API_PREFIX/999/enable" "" "启用不存在的任务（测试404）"

# 12. 手动触发任务
test_api "POST" "$API_PREFIX/1/trigger" "" "手动触发ID为1的任务"

# 13. 获取任务执行日志
test_api "GET" "$API_PREFIX/1/logs" "" "获取ID为1任务的执行日志"

# 14. 获取任务执行日志（带分页）
test_api "GET" "$API_PREFIX/1/logs?skip=0&limit=10" "" "获取任务执行日志（分页）"

# 15. 删除任务
test_api "DELETE" "$API_PREFIX/1" "" "删除ID为1的任务"

# 16. 删除不存在的任务
test_api "DELETE" "$API_PREFIX/999" "" "删除不存在的任务（测试404）"

# 17. 获取调度器状态
test_api "GET" "/task-scheduler/status" "" "获取任务调度器状态"

# 18. 刷新调度器
test_api "POST" "/task-scheduler/refresh" "" "刷新任务调度器配置"

echo -e "\n========================================"
echo -e "${GREEN}API 接口测试完成！${NC}"
echo "========================================"

echo -e "\n📊 测试覆盖情况:"
echo "✅ CRUD操作: 创建、读取、更新、删除"
echo "✅ 任务管理: 启用、禁用、手动触发"
echo "✅ 日志查询: 执行历史记录"
echo "✅ 调度器: 状态查询、配置刷新"
echo "✅ 错误处理: 404、400等状态码"
echo "✅ 参数验证: 分页、过滤、数据格式"

echo -e "\n💡 使用说明:"
echo "1. 如果看到连接错误，请先启动FastAPI服务器"
echo "2. 2xx状态码表示成功，4xx表示客户端错误，5xx表示服务器错误"
echo "3. 实际生产环境中需要添加认证和权限控制"
echo "4. 建议配置数据库连接后再进行完整测试"