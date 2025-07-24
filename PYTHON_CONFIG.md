# Python环境配置说明

## 概述
OMind智能运维平台支持多Python环境配置，用户可以根据本地和远程环境设置不同的Python路径。

## 支持配置的脚本

所有脚本都使用统一的 `VALID_PYTHON_PATH` 数组配置：

### 1. `scripts/start_mcp.sh` - MCP服务器启动脚本
### 2. `scripts/start_backend.sh` - 后端服务启动脚本  
### 3. `scripts/pre_env.sh` - 环境预配置脚本 (支持命令行参数)
### 4. `scripts/upgrade.sh` - 升级脚本

**配置位置**: 脚本开头配置区域
```bash
# ====== 配置区域 ======
# 用户可根据环境修改以下Python路径
VALID_PYTHON_PATH=("/Users/gaochao/miniconda3/envs/py312" "/data/omind/venv")
# ====================
```

## 特殊功能：pre_env.sh命令行参数

`scripts/pre_env.sh` 脚本支持通过命令行参数指定Python路径，无需修改脚本文件：

```bash
# 使用命令行参数指定Python路径
scripts/pre_env.sh --init --python-path=/usr/bin/python3.12
scripts/pre_env.sh --init --path=/opt --python-path=/opt/conda/bin/python
```

**优先级**：命令行参数 > 脚本配置数组 > 自动检测

## 配置格式

数组中可以包含：
- **虚拟环境目录路径**: 如 `/data/omind/venv`（脚本会自动找到bin/python）
- **直接Python可执行文件路径**: 如 `/usr/bin/python3`

## 配置示例

### 场景1: 脚本配置方式 - 本地开发 + 远程生产
```bash
VALID_PYTHON_PATH=("/Users/username/miniconda3/envs/py312" "/data/omind/venv")
```

### 场景2: 脚本配置方式 - 多个远程环境
```bash
VALID_PYTHON_PATH=("/opt/python312/venv" "/data/omind/venv")
```

### 场景3: 脚本配置方式 - 混合虚拟环境和系统Python
```bash
VALID_PYTHON_PATH=("/data/omind/venv" "/usr/bin/python3.12")
```

### 场景4: 命令行参数方式 - 环境初始化
```bash
# 使用特定Python版本初始化环境
scripts/pre_env.sh --init --python-path=/usr/bin/python3.12

# 指定自定义部署路径和Python版本
scripts/pre_env.sh --init --deploy-path=/opt --python-path=/opt/conda/bin/python3

# 清理指定路径的环境
scripts/pre_env.sh --cleanup --deploy-path=/opt
```

## 工作原理

### pre_env.sh脚本优先级：
1. **命令行参数**: `--python-path` 指定的Python路径（最高优先级）
2. **脚本配置数组**: `VALID_PYTHON_PATH` 数组中的路径（按顺序检测）
3. **自动检测**: 如果以上都失败，提示用户检查配置

### 其他脚本优先级：
1. **脚本配置数组**: 按 `VALID_PYTHON_PATH` 数组顺序依次检测，使用第一个有效的Python环境

### 智能检测机制：
- **虚拟环境目录**: 检测是否存在 `bin/python` 文件并自动激活
- **可执行文件路径**: 直接验证是否可用和版本兼容性
- **版本验证**: 确保Python版本为3.6+
- **环境激活**: 自动激活虚拟环境（如果是虚拟环境目录）

## 测试验证

修改配置后，可以通过以下方式验证：

```bash
# 测试MCP服务器启动
cd scripts && ./start_mcp.sh

# 测试后端服务启动  
cd scripts && ./start_backend.sh

# 查看检测到的Python环境
# 脚本会输出类似：
# 🔍 检测Python环境...
#    发现虚拟环境: /data/omind/venv
# ✅ 使用虚拟环境: /data/omind/venv (Python 3.12.11)
```

## 注意事项

- 修改配置后无需重新打包，直接运行脚本即可生效
- 建议将最常用的环境放在数组前面以提高检测效率
- 确保配置的路径存在且Python版本为3.6+