# Python环境配置说明

## 概述
OMind智能运维平台支持多Python环境配置，用户可以根据本地和远程环境设置不同的Python路径。

## 支持配置的脚本

所有脚本都使用统一的 `VALID_PYTHON_PATH` 数组配置：

### 1. `scripts/start_mcp.sh` - MCP服务器启动脚本
### 2. `scripts/start_backend.sh` - 后端服务启动脚本  
### 3. `scripts/pre_env.sh` - 环境预配置脚本

**配置位置**: 脚本开头配置区域
```bash
# ====== 配置区域 ======
# 用户可根据环境修改以下Python路径
VALID_PYTHON_PATH=("/Users/gaochao/miniconda3/envs/py312" "/data/omind/venv")
# ====================
```

## 配置格式

数组中可以包含：
- **虚拟环境目录路径**: 如 `/data/omind/venv`（脚本会自动找到bin/python）
- **直接Python可执行文件路径**: 如 `/usr/bin/python3`

## 配置示例

### 场景1: 本地开发 + 远程生产
```bash
VALID_PYTHON_PATH=("/Users/username/miniconda3/envs/py312" "/data/omind/venv")
```

### 场景2: 多个远程环境
```bash
VALID_PYTHON_PATH=("/opt/python312/venv" "/data/omind/venv")
```

### 场景3: 混合虚拟环境和系统Python
```bash
VALID_PYTHON_PATH=("/data/omind/venv" "/usr/bin/python3.12")
```

## 工作原理

1. **优先级**: 脚本按数组顺序依次检测，使用第一个有效的Python环境
2. **智能检测**: 
   - 对于目录路径，检测是否存在 `bin/python` 文件
   - 对于可执行文件路径，直接验证是否可用
3. **版本验证**: 确保Python版本为3.6+
4. **环境激活**: 自动激活虚拟环境（如果是虚拟环境目录）

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