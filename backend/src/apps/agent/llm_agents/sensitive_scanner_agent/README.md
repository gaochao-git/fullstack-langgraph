# 敏感数据扫描智能体

## 概述

敏感数据扫描智能体是一个基于LangGraph MapReduce模式的智能体，专门用于扫描文档中的敏感信息。它支持大文档的分片并行处理，可以识别身份证、手机号、银行卡号、密码、API密钥等多种敏感数据类型。

## 技术特点

### MapReduce架构 + LLM识别

该智能体采用了LangGraph的MapReduce模式，结合大语言模型的智能识别能力：

1. **Map阶段**：将大文档分成多个小片段，每个片段独立发送给LLM进行敏感数据识别
2. **Reduce阶段**：聚合所有片段的扫描结果，生成统一的报告
3. **LLM识别**：利用大模型的上下文理解能力，智能识别各类敏感信息，不依赖固定的正则规则

### 核心节点

- `initialize_scan`：初始化扫描任务，从请求中获取file_ids并加载文件内容
- `create_chunks`：根据配置的chunk_size创建文档分片，按行分割避免断词
- `parallel_scan`：并行调用LLM扫描所有分片（Map阶段）
- `aggregate_results`：聚合扫描结果（Reduce阶段）
- `generate_report`：生成最终的扫描报告

### 工具集

1. **get_file_content**：根据文件ID获取已上传的文档内容
2. **analyze_sensitive_data_prompt**：生成用于LLM分析的专业提示词
3. **merge_scan_results**：合并多个分片的扫描结果
4. **generate_scan_report**：生成格式化的扫描报告

## 使用方法

### 1. 上传文件

首先通过文件上传API上传需要扫描的文档：

```bash
curl -X POST "http://localhost:8000/api/v1/chat/files" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf"
```

响应会返回文件ID：
```json
{
  "file_id": "file_xxxxx",
  "file_name": "document.pdf"
}
```

### 2. 发起扫描

通过对话接口向智能体发起扫描请求：

```bash
curl -X POST "http://localhost:8000/api/v1/chat/threads/{thread_id}/runs/stream" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "sensitive_scanner_agent",
    "file_ids": ["file_xxxxx", "file_yyyyy"],
    "input": "请扫描这些文件中的敏感数据"
  }'
```

### 3. 批量扫描

支持同时扫描多个文件，通过file_ids数组传递：

```json
{
  "file_ids": ["file_xxxxx", "file_yyyyy", "file_zzzzz"],
  "input": "请帮我扫描这些文件中的敏感信息"
}
```

## 支持的敏感数据类型

- **身份证号**：18位身份证号码
- **手机号**：中国大陆手机号
- **银行卡号**：16-19位银行卡号
- **邮箱地址**：标准邮箱格式
- **IP地址**：IPv4地址
- **密码**：包含password、pwd等关键词的配置
- **API密钥**：api_key、access_key、secret_key等
- **私钥**：RSA等私钥格式
- **访问令牌**：token、bearer等

## 配置参数

在 `configuration.py` 中可以调整以下参数：

- `chunk_size`：每个分片的大小（默认4000字符）
- `max_parallel_chunks`：最大并行处理分片数（默认5）
- `temperature`：LLM温度参数（默认0.1，确保准确性）
- `max_tokens`：最大输出token数（默认8000）

## 性能优化

1. **分片策略**：按行分割，避免在单词中间切断
2. **并行控制**：通过max_parallel_chunks控制并发数，避免LLM调用过载
3. **结果聚合**：智能合并分片结果，避免重复计数
4. **LLM优化**：使用低温度（temperature=0.1）确保识别准确性

## 安全考虑

1. **隐私保护**：不记录具体的敏感信息内容，只记录类型和位置
2. **访问控制**：遵循文件的访问权限控制
3. **日志脱敏**：日志中不包含敏感数据的实际内容

## 扩展性

1. **敏感数据类型**：LLM可以自动识别新类型的敏感数据，无需修改代码
2. **提示词优化**：可以通过更新`analyze_sensitive_data_prompt`来改进识别效果
3. **模型选择**：支持选择不同的LLM模型进行识别

## 初始化

首次部署时，运行初始化脚本将智能体配置同步到数据库：

```bash
cd backend/src/apps/agent/llm_agents/sensitive_scanner_agent
python init_db.py
```

## 注意事项

1. 大文件会自动分片处理，但仍建议控制单个文件大小在合理范围内
2. LLM识别的准确性取决于模型能力和提示词质量
3. 并行调用LLM可能产生较高的API费用，请根据实际情况调整max_parallel_chunks
4. 文件内容会被发送给LLM，请确保文档本身不包含高度敏感信息