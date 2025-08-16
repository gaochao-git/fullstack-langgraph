# UV 使用指南

UV 是一个极快的 Python 包和项目管理器，用 Rust 编写。

## 快速开始

### 安装uv
```bash
# 安装uv
pip install uv
pip3.12 install uv-0.8.11-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl 

# 验证安装
uv --version
```

### 初始化项目
```bash
# 在项目目录初始化
uv init

# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

### 安装依赖
```bash
# 从 pyproject.toml 和 uv.lock 安装依赖
uv sync

# 安装单个包
uv pip install requests

# 从 requirements.txt 安装
uv pip install -r requirements.txt
```

## 依赖管理

### 添加依赖
```bash
# 添加运行时依赖
uv add fastapi

# 添加开发依赖
uv add --dev pytest black

# 添加特定版本
uv add "django>=4.0,<5.0"
uv add "flask==2.3.0"
```

### 移除依赖
```bash
uv remove requests
```

### 更新依赖
```bash
# 更新所有依赖到最新兼容版本
uv sync --upgrade

# 更新特定包
uv add --upgrade fastapi
```

### 查看依赖
```bash
# 列出已安装的包
uv pip list

# 显示依赖树
uv pip tree

# 查看过时的包
uv pip list --outdated
```

## 锁文件管理

```bash
# 生成/更新锁文件
uv lock

# 从锁文件安装（确保环境一致）
uv sync

# 验证锁文件
uv lock --check
```

## 导出依赖

```bash
# 导出为 requirements.txt
uv pip freeze > requirements.txt

# 导出编译后的依赖（包含所有子依赖）
uv pip compile pyproject.toml -o requirements-lock.txt

# 导出特定平台的依赖
uv pip compile pyproject.toml --platform linux --python-version 3.12
```

## 离线部署

### 准备离线包
```bash
# 下载所有依赖到本地目录
uv pip download -r uv.lock -d ./offline_packages/

# 或从 pyproject.toml 下载
uv pip download -r pyproject.toml -d ./offline_packages/
```

### 离线安装
```bash
# 从本地目录安装
uv pip install --find-links ./offline_packages --no-index -r requirements.txt

# 或使用 sync
uv sync --find-links ./offline_packages --offline
```

## Python 版本管理

```bash
# 使用特定 Python 版本
uv venv --python 3.12

# 或指定路径
uv venv --python /usr/local/bin/python3.12
```

## 项目结构

```
project/
├── pyproject.toml      # 项目配置和依赖声明
├── uv.lock            # 锁定的依赖版本（应提交到版本控制）
├── .venv/             # 虚拟环境（不要提交）
└── src/               # 源代码
```

## 常用选项

```bash
# 静默模式
uv sync -q

# 详细输出
uv sync -v

# 不使用缓存
uv sync --no-cache

# 严格模式（依赖必须完全匹配）
uv sync --frozen
```

## 与 pip 的区别

1. **速度**：UV 比 pip 快 10-100 倍
2. **锁文件**：自动生成 `uv.lock` 确保依赖一致性
3. **解析器**：更智能的依赖冲突解决
4. **缓存**：全局缓存，避免重复下载
5. **原子操作**：安装失败时自动回滚

## 最佳实践

1. **始终提交 `uv.lock`** - 确保所有环境依赖一致
2. **使用 `uv sync`** - 而不是 `uv pip install`
3. **定期更新** - `uv self update` 保持 UV 最新
4. **开发依赖分离** - 使用 `--dev` 标记开发工具