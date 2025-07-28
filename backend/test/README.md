# 🧪 测试完整指南

本目录包含项目的所有测试相关配置、脚本和文档。

## 📁 目录结构

```
test/
├── README.md           # 本测试指南（完整版）
├── pytest.ini         # pytest配置文件
├── .coveragerc         # coverage配置文件
├── conftest.py         # 全局测试配置和fixture
├── test_module.sh      # 模块化测试脚本
├── fixtures/           # 全局共享测试fixtures
│   ├── __init__.py
│   └── common_fixtures.py # 跨模块通用测试数据
└── scripts/            # 测试辅助脚本
    ├── coverage_report.sh  # 覆盖率报告生成
    └── clean_test.sh       # 清理测试文件
```

## 🚀 快速开始

### 安装测试依赖
```bash
# 安装所有依赖（包括测试依赖）
make install

# 或者手动安装测试依赖
pip install pytest pytest-cov pytest-asyncio pytest-mock coverage
```

### 基础测试命令
```bash
# 基础测试（无覆盖率）
make test

# 测试 + 覆盖率
make test-cov

# 生成HTML覆盖率报告
make test-html

# 生成XML覆盖率报告（CI用）
make test-xml

# 快速测试（跳过慢速测试）
make test-fast

# 清理测试文件
make clean-test
```

## 📊 模块化测试（推荐）

每个业务模块可以独立测试，互相隔离：

```bash
# 使用Makefile（推荐）
make test-sop           # 测试SOP模块
make test-agent         # 测试Agent模块
make test-mcp           # 测试MCP模块
make test-ai-model      # 测试AI模型模块
make test-scheduled-task # 测试定时任务模块

# 使用专用脚本
./test/test_module.sh sop           # 终端报告
./test/test_module.sh sop html      # HTML报告
./test/test_module.sh sop xml       # XML报告

# 生成特定模块的HTML报告
make test-sop-html      # SOP模块HTML报告
```

## 🎯 精确测试控制

Coverage支持非常精确的测试控制：

```bash
# 测试特定文件
make test-file FILE=src/apps/sop/test/test_service.py

# 测试特定类
make test-class CLASS=src/apps/sop/test/test_service.py::TestSOPService

# 测试特定方法
make test-method METHOD=src/apps/sop/test/test_service.py::TestSOPService::test_create_sop

# 直接使用coverage命令
coverage run --rcfile=test/.coveragerc --branch --source=src/apps/agent -m pytest -c test/pytest.ini src/apps/agent/test/test_service.py::TestAgentService::test_get_agents
```

## 📈 覆盖率报告

### 报告类型
- **终端报告**: 实时显示覆盖率百分比
- **HTML报告**: `htmlcov/index.html` - 交互式可视化报告
- **XML报告**: `coverage.xml` - 用于CI/CD集成
- **模块报告**: `htmlcov/{module}/index.html` - 单模块报告

### 查看报告
```bash
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# 或在浏览器中直接打开
```

## ⚙️ 配置文件详解

### pytest.ini
```ini
[tool:pytest]
testpaths = src/apps test    # 测试目录
python_files = test_*.py     # 测试文件模式
asyncio_mode = auto          # 异步测试支持
```

### .coveragerc
```ini
[run]
source = src                 # 覆盖率收集范围
branch = True               # 启用分支覆盖率
omit = */test/*             # 忽略测试文件

[report]
fail_under = 80             # 最低覆盖率要求
show_missing = True         # 显示未覆盖的行
```

## 📋 测试标记

使用pytest标记来分类和筛选测试：

```python
@pytest.mark.unit           # 单元测试
@pytest.mark.integration    # 集成测试
@pytest.mark.slow           # 慢速测试
@pytest.mark.db             # 需要数据库的测试
```

```bash
# 按标记运行测试
pytest -c test/pytest.ini -m unit              # 只运行单元测试
pytest -c test/pytest.ini -m integration       # 只运行集成测试
pytest -c test/pytest.ini -m "not slow"        # 跳过慢速测试
pytest -c test/pytest.ini -m "not db"          # 跳过数据库测试
```

## 🧪 编写测试

### 服务层测试示例
```python
import pytest
from unittest.mock import AsyncMock
from ..service.sop_service import SOPService

class TestSOPService:
    @pytest.fixture
    def sop_service(self):
        return SOPService()
    
    @pytest.fixture  
    def mock_db_session(self):
        return AsyncMock()
    
    async def test_create_sop(self, sop_service, mock_db_session, sample_sop_data):
        # 测试逻辑
        result = await sop_service.create_sop_template(mock_db_session, sample_sop_data)
        assert result is not None
```

### 路由层测试示例
```python
from fastapi.testclient import TestClient
from ....main import create_app

class TestSOPRouter:
    @pytest.fixture
    def client(self):
        app = create_app()
        return TestClient(app)
    
    def test_create_sop_endpoint(self, client, sample_sop_create_data):
        response = client.post("/api/sops", json=sample_sop_create_data)
        assert response.status_code == 200
```

## 🔧 测试Fixture

项目采用分层的fixture管理：

### 全局Fixtures
- **test/conftest.py**: 全局测试配置（数据库会话、应用实例等）
- **test/fixtures/common_fixtures.py**: 跨模块通用测试数据

### 模块Fixtures  
每个业务模块管理自己的测试数据：
- **src/apps/sop/test/fixtures/sop_fixtures.py**: SOP专用测试数据
- **src/apps/agent/test/fixtures/agent_fixtures.py**: Agent专用测试数据
- **src/apps/mcp/test/fixtures/mcp_fixtures.py**: MCP专用测试数据
- **src/apps/ai_model/test/fixtures/**: AI模型专用测试数据
- **src/apps/scheduled_task/test/fixtures/**: 定时任务专用测试数据

### 使用方式
```python
# 在测试文件中导入模块专用fixtures
from .fixtures import *  # 导入当前模块的所有fixtures

# 全局fixtures会自动可用（通过conftest.py）
def test_example(sample_sop_data, mock_db_session, common_user_data):
    # sample_sop_data: 来自模块fixtures
    # mock_db_session: 来自全局conftest.py  
    # common_user_data: 来自全局common_fixtures.py
    pass
```

## 🚀 持续集成

测试配置已优化用于CI/CD流水线：

```yaml
# GitHub Actions示例
- name: Run tests with coverage
  run: |
    make test-xml
    
- name: Upload coverage reports
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## 🎯 最佳实践

1. **模块隔离**: 每个业务模块独立测试，避免相互影响
2. **分支覆盖**: 使用`--branch`获得更精确的覆盖率统计
3. **Mock使用**: 使用pytest-mock进行外部依赖隔离
4. **异步测试**: 使用pytest-asyncio支持异步函数测试
5. **数据隔离**: 每个测试使用独立的数据库会话或Mock
6. **测试命名**: 使用描述性的测试方法名，如`test_create_sop_with_valid_data`
7. **覆盖率目标**: 保持80%以上的测试覆盖率

## 🐛 调试测试

```bash
# 详细输出模式
pytest -c test/pytest.ini -v -s

# 只运行失败的测试
pytest -c test/pytest.ini --lf

# 遇到第一个失败就停止
pytest -c test/pytest.ini -x

# 显示本地变量
pytest -c test/pytest.ini --tb=long -v
```