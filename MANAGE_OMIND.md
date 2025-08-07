# OMind 生命周期管理脚本

## 概述

`manage_omind.sh` 是 OMind 智能运维平台的统一生命周期管理脚本，提供了从初始化到清理的完整服务管理功能。

## 主要特性

- **统一管理**：一个脚本管理所有生命周期操作
- **配置持久化**：init时保存配置，后续命令自动使用
- **灵活部署**：支持自定义部署路径和Python环境
- **智能检测**：自动检测环境状态和服务运行情况
- **安全操作**：清理前需要用户确认，避免误操作

## 使用方法

### 基本语法
```bash
./manage_omind.sh <command> [options]
```

### 支持的命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `init` | 初始化OMind环境 | `./manage_omind.sh init --deploy-path=/opt` |
| `start` | 启动OMind服务 | `./manage_omind.sh start` |
| `stop` | 停止OMind服务 | `./manage_omind.sh stop` |
| `restart` | 重启OMind服务 | `./manage_omind.sh restart` |
| `status` | 查看服务状态 | `./manage_omind.sh status` |
| `upgrade` | 升级到新版本 | `./manage_omind.sh upgrade --package=omind-xxx` |
| `cleanup` | 清理环境 | `./manage_omind.sh cleanup` |
| `help` | 显示帮助信息 | `./manage_omind.sh help` |

### 支持的选项

| 选项 | 说明 | 适用命令 |
|------|------|----------|
| `--deploy-path=PATH` | 指定部署路径 | 所有命令 |
| `--python-path=PATH` | 指定Python路径 | init |
| `--package=NAME` | 指定升级包名称 | upgrade |

## 配置管理

### 配置文件
- **位置**：`.omind_config`（脚本同目录下的隐藏文件）
- **格式**：Shell变量格式
- **自动生成**：init命令执行时自动创建

### 配置优先级
1. **命令行参数**（最高优先级）
2. **配置文件中的保存值**
3. **脚本默认值**（最低优先级）

### 配置示例
```bash
# OMind 配置文件 - 由 manage_omind.sh 自动生成
# 生成时间: Thu Jul 24 17:09:27 CST 2025
SAVED_DEPLOY_PATH="/data"
SAVED_PYTHON_PATH="/usr/bin/python3.12"
```

## 典型使用流程

### 1. 首次部署
```bash
# 初始化环境（保存配置）
./manage_omind.sh init --deploy-path=/data --python-path=/usr/local/python312/bin/python3

# 启动服务
./manage_omind.sh start

# 查看状态
./manage_omind.sh status
```

### 2. 日常管理
```bash
# 停止服务（使用保存的配置）
./manage_omind.sh stop

# 重启服务
./manage_omind.sh restart

# 查看状态
./manage_omind.sh status
```

### 3. 版本升级
```bash
# 升级到新版本
./manage_omind.sh upgrade --package=omind-20250724_164901

# 验证升级结果
./manage_omind.sh status
```

### 4. 环境清理
```bash
# 完全清理环境
./manage_omind.sh cleanup
```

## 服务架构

### 服务组件
- **MCP服务器**：数据库、SSH、Elasticsearch、Zabbix工具服务器
- **后端API**：FastAPI + LangGraph智能代理服务
- **前端界面**：React + Vite构建的Web界面
- **反向代理**：Nginx配置的前端和API代理

### 目录结构
```
<deploy-path>/omind/
├── backend/           # 后端代码
│   ├── logs/         # 后端日志
│   └── pids/         # 后端PID文件
├── mcp_servers/      # MCP服务器
│   ├── logs/         # MCP日志
│   ├── pids/         # MCP PID文件
│   └── servers/      # 服务器实现
├── frontend/         # 前端文件
│   └── dist/         # 构建产物
├── scripts/          # 管理脚本
├── venv/            # Python虚拟环境
└── nginx.conf       # Nginx配置
```

## 故障排除

### 常见问题

1. **初始化失败**
   ```bash
   # 检查Python版本
   python3 --version
   
   # 检查部署路径权限
   ls -la /data/
   ```

2. **服务启动失败**
   ```bash
   # 查看日志
   tail -f /data/omind/backend/logs/*.log
   tail -f /data/omind/mcp_servers/logs/*.log
   ```

3. **配置文件丢失**
   ```bash
   # 重新初始化
   ./manage_omind.sh init --deploy-path=/data --python-path=/usr/bin/python3.12
   ```

### 调试模式
脚本支持详细输出，可以查看每个步骤的执行情况：
```bash
# 启用详细输出
set -x
./manage_omind.sh status
set +x
```

## 最佳实践

1. **首次部署**：使用绝对路径指定deploy-path和python-path
2. **权限管理**：确保运行用户对部署路径有读写权限
3. **备份配置**：定期备份.omind_config文件
4. **版本管理**：升级前先查看当前状态
5. **清理操作**：清理前确保重要数据已备份

## 与其他脚本的关系

- **调用关系**：manage_omind.sh → scripts/pre_env.sh, scripts/start_*.sh, scripts/stop_*.sh
- **配置同步**：管理脚本的配置会自动同步到被调用的脚本中
- **独立使用**：scripts目录下的脚本仍可独立使用，但推荐使用统一管理脚本