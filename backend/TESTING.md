# 🧪 测试说明

## 快速开始

```bash
# 基础测试
make test

# 测试 + 覆盖率
make test-cov

# HTML覆盖率报告
make test-html

# 清理测试文件
make clean-test
```

## 模块化测试

```bash
make test-sop           # SOP模块
make test-agent         # Agent模块
make test-mcp           # MCP模块
```

## 📁 详细文档

所有测试配置、脚本、文档都在 [`test/`](./test/) 目录中：

- 📖 **[test/README.md](./test/README.md)** - 完整测试指南（包含所有用法和最佳实践）
- ⚙️ **[test/pytest.ini](./test/pytest.ini)** - pytest配置
- 📊 **[test/.coveragerc](./test/.coveragerc)** - coverage配置  
- 🧪 **[test/conftest.py](./test/conftest.py)** - 测试fixture
- 🔧 **[test/scripts/](./test/scripts/)** - 测试辅助脚本