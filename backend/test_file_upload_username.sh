#!/bin/bash

# 测试文件上传API的user_name参数

# 配置
API_BASE_URL="http://localhost:8000"
AGENT_KEY="agent_c794582e36607cbbdcf7fe16dffb51580d5c424f61f3b3e0e03d8494b4"

echo "🧪 测试文件上传API的user_name参数..."

# 创建测试文件
echo "This is a test document for user_name parameter testing." > test_username.txt

# 1. 测试带user_name参数
echo -e "\n✅ 测试1: 带user_name参数上传"
curl -X POST "${API_BASE_URL}/api/chat/files/upload?user_name=test_api_user" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -F "file=@test_username.txt" \
  -w "\nHTTP状态码: %{http_code}\n" | /Users/gaochao/miniconda3/envs/py312/bin/python -c "
import sys, json
try:
    # 读取输入直到找到JSON部分
    input_data = sys.stdin.read()
    # 找到JSON开始的位置
    json_start = input_data.find('{')
    if json_start >= 0:
        json_data = input_data[json_start:input_data.rfind('}')+1]
        data = json.loads(json_data)
        if data.get('status') == 'ok':
            print(f'✅ 上传成功!')
            print(f'   文件ID: {data[\"data\"][\"file_id\"]}')
            print(f'   文件名: {data[\"data\"][\"file_name\"]}')
            print(f'   文件大小: {data[\"data\"][\"file_size\"]} bytes')
            # 保存文件ID供后续使用
            with open('.test_file_id', 'w') as f:
                f.write(data['data']['file_id'])
        else:
            print(f'❌ 上传失败: {data.get(\"msg\", \"未知错误\")}')
    else:
        print('❌ 响应不是JSON格式')
        print(f'原始响应: {input_data}')
except Exception as e:
    print(f'❌ 解析响应失败: {e}')
"

# 2. 测试不带user_name参数（应该失败）
echo -e "\n❌ 测试2: 不带user_name参数上传（应该失败）"
curl -X POST "${API_BASE_URL}/api/chat/files/upload" \
  -H "Authorization: Bearer ${AGENT_KEY}" \
  -F "file=@test_username.txt" \
  -w "\nHTTP状态码: %{http_code}\n" 2>/dev/null | python -c "
import sys, json
try:
    input_data = sys.stdin.read()
    json_start = input_data.find('{')
    if json_start >= 0:
        json_data = input_data[json_start:input_data.rfind('}')+1]
        data = json.loads(json_data)
        if data.get('status') == 'error':
            print(f'✅ 正确拒绝: {data.get(\"msg\", \"未知错误\")}')
        else:
            print(f'❌ 错误：应该返回错误但返回了: {data}')
    else:
        print('❌ 响应不是JSON格式')
except Exception as e:
    print(f'❌ 解析响应失败: {e}')
"

# 3. 如果第一个测试成功，测试获取文档内容
if [ -f .test_file_id ]; then
    FILE_ID=$(cat .test_file_id)
    echo -e "\n🔍 测试3: 获取文档内容"
    
    # 等待文件处理完成
    sleep 2
    
    curl -X GET "${API_BASE_URL}/api/chat/files/${FILE_ID}/content" \
      -H "Authorization: Bearer ${AGENT_KEY}" \
      -w "\nHTTP状态码: %{http_code}\n" 2>/dev/null | python -c "
import sys, json
try:
    input_data = sys.stdin.read()
    json_start = input_data.find('{')
    if json_start >= 0:
        json_data = input_data[json_start:input_data.rfind('}')+1]
        data = json.loads(json_data)
        if data.get('status') == 'ok':
            print(f'✅ 获取内容成功!')
            content = data['data'].get('content', '')[:100]
            print(f'   内容预览: {content}...')
        else:
            print(f'ℹ️ 文档可能还在处理中: {data.get(\"msg\", \"\")}')
    else:
        print('❌ 响应不是JSON格式')
except Exception as e:
    print(f'❌ 解析响应失败: {e}')
"
fi

# 清理
rm -f test_username.txt .test_file_id

echo -e "\n✅ user_name参数测试完成!"
echo "说明："
echo "1. 文件上传API现在需要必须的user_name查询参数"
echo "2. user_name用于记录是谁上传的文件"
echo "3. 参数名称已统一为user_name（不是user_id）"