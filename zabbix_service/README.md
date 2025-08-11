# Zabbix Service

独立的 Zabbix 监控数据服务，提供统一的告警数据接口。

## 功能特性

- 独立运行的 FastAPI 服务
- 从 Zabbix API 获取监控数据
- 转换为统一的告警格式
- 支持环境变量配置

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录的 `.env` 文件中配置：

```env
# Zabbix服务运行配置
ZABBIX_SERVICE_HOST=0.0.0.0
ZABBIX_SERVICE_PORT=8001

# Zabbix API连接配置
ZABBIX_API_URL=http://your-zabbix-server/api_jsonrpc.php
ZABBIX_USERNAME=Admin
ZABBIX_PASSWORD=your-password
```

### 3. 启动服务

```bash
# 使用启动脚本
./scripts/start_service.sh

# 或直接运行
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

## API 接口

### 获取告警数据（统一格式）

```http
GET /api/alarms
```

支持的查询参数：
- `alarm_level`: 严重级别过滤，支持多选，如 `?alarm_level=P1&alarm_level=P2`
- `alarm_time`: 时间过滤，返回大于等于此时间的告警
- `team_tag`: 团队标签过滤，支持多选，如 `?team_tag=数据库&team_tag=应用`
- `idc_tag`: 机房标签过滤，支持多选，如 `?idc_tag=北京&idc_tag=上海`
- `alarm_ip`: 主机IP过滤
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认50）

返回格式：
```json
{
  "total": 100,
  "page": 1,
  "page_size": 50,
  "data": [
    {
      "alarm_id": "事件ID",
      "alarm_source": "Zabbix",
      "alarm_key": "监控指标key",
      "alarm_name": "告警名称",
      "alarm_desc": "告警描述",
      "alarm_level": "严重级别",
      "alarm_time": "时间",
      "alarm_ip": "主机IP",
      "team_tag": "团队tag",
      "idc_tag": "机房tag"
    }
  ]
}
```

示例请求：
```bash
# 获取P1和P2级别的告警
curl "http://localhost:8001/api/alarms?alarm_level=P1&alarm_level=P2"

# 获取数据库团队在北京机房的告警
curl "http://localhost:8001/api/alarms?team_tag=数据库&idc_tag=北京"

# 获取特定时间之后的告警（分页）
curl "http://localhost:8001/api/alarms?alarm_time=2024-01-01T00:00:00&page=2&page_size=20"
```

### 获取原始 Zabbix 数据

- `GET /api/zabbix/problems` - 获取问题列表
- `GET /api/zabbix/hosts` - 获取主机列表
- `GET /api/zabbix/items` - 获取监控项列表

### 健康检查

```http
GET /health
```

## 与主系统集成

在主系统的 `.env` 中配置：

```env
# 使用 Zabbix 服务作为告警数据源
ALARM_API_URL=http://localhost:8001/api/alarms
```

## 开发说明

- `src/zabbix_service.py` - Zabbix API 客户端
- `src/zabbix_adapter.py` - 数据格式转换适配器
- `src/main.py` - FastAPI 应用入口

## 部署建议

1. 可以与主系统部署在同一服务器
2. 也可以独立部署，通过网络访问
3. 建议使用进程管理工具（如 systemd 或 supervisor）管理服务