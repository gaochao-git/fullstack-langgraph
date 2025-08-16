# UV 使用指南

## UV 环境已配置完成

你的项目现在使用 UV 管理依赖，所有依赖已从 `requirements_frozen.txt` 迁移到 `pyproject.toml`。

## 常用 UV 命令

### 1. 激活虚拟环境
```bash
source .venv/bin/activate
```

### 2. 安装项目依赖
```bash
# 从锁文件安装（推荐，确保一致性）
uv sync

# 或者安装最新兼容版本
uv pip install -r pyproject.toml
```

### 3. 添加新依赖
```bash
# 添加依赖
uv add package-name

# 添加开发依赖
uv add --dev package-name

# 添加特定版本
uv add "package-name==1.2.3"
```

### 4. 删除依赖
```bash
uv remove package-name
```

### 5. 更新依赖
```bash
# 更新所有依赖
uv sync --upgrade

# 更新特定依赖
uv add --upgrade package-name
```

### 6. 导出依赖
```bash
# 导出为 requirements.txt 格式
uv pip freeze > requirements.txt

# 导出锁定的精确版本
uv pip compile pyproject.toml -o requirements-lock.txt
```

### 7. 查看已安装的包
```bash
uv pip list
```

## 内网部署方案

### 1. 在有网络的环境准备
```bash
# 下载所有依赖包
uv pip download -r pyproject.toml -d ./offline_packages/

# 或使用锁文件（更精确）
uv pip download -r uv.lock -d ./offline_packages/
```

### 2. 在内网环境安装
```bash
# 从离线包安装
uv pip install --find-links ./offline_packages --no-index -r requirements-lock.txt
```

## 项目文件说明

- `pyproject.toml` - 项目配置和依赖声明
- `uv.lock` - 锁定的依赖版本（类似 package-lock.json）
- `.venv/` - UV 创建的虚拟环境
- `.python-version` - 指定的 Python 版本

## 迁移说明

原 `requirements_frozen.txt` 的所有依赖已迁移到 UV 管理：
- 总共 138 个包成功安装
- 使用 Python 3.12.11（继承自原 venv）
- 所有版本已锁定在 `uv.lock` 中

## UV 优势

1. **更快的依赖解析** - 比 pip 快 10-100 倍
2. **更好的依赖管理** - 自动处理版本冲突
3. **锁文件支持** - 确保所有环境一致性
4. **更好的缓存** - 减少重复下载
5. **原生支持 pyproject.toml** - 现代 Python 项目标准