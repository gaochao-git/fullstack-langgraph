# 项目测试和开发命令

.PHONY: test test-cov test-html test-xml test-fast clean-cov help

# 默认显示帮助
help:
	@echo "可用命令："
	@echo "  test         - 运行所有测试（无覆盖率）"
	@echo "  test-cov     - 运行测试并显示覆盖率"
	@echo "  test-html    - 运行测试并生成HTML覆盖率报告"
	@echo "  test-xml     - 运行测试并生成XML覆盖率报告（CI用）"
	@echo "  test-fast    - 快速测试（跳过慢速测试）"
	@echo "  test-sop     - 只测试SOP模块"
	@echo "  test-agent   - 只测试Agent模块"
	@echo "  test-mcp     - 只测试MCP模块"
	@echo "  clean-cov    - 清理覆盖率文件"
	@echo "  install      - 安装依赖"
	@echo "  format       - 格式化代码"
	@echo "  lint         - 代码检查"

# 安装依赖
install:
	pip install -r requirements.txt

# 基础测试（无覆盖率）
test:
	pytest -c test/pytest.ini -v

# 测试 + 覆盖率（主要方式）
test-cov:
	coverage run --rcfile=test/.coveragerc --branch -m pytest -c test/pytest.ini
	coverage report --rcfile=test/.coveragerc

# 测试 + HTML覆盖率报告
test-html:
	./test/scripts/coverage_report.sh

# 测试 + XML覆盖率报告（CI用）
test-xml:
	coverage run --rcfile=test/.coveragerc --branch -m pytest -c test/pytest.ini
	coverage xml --rcfile=test/.coveragerc
	coverage report --rcfile=test/.coveragerc

# 快速测试（跳过慢速和数据库测试）
test-fast:
	pytest -c test/pytest.ini -m "not slow and not db" -v

# 单模块测试（含分支覆盖率，模块隔离）
test-sop:
	coverage run --rcfile=test/.coveragerc --branch --source=src/apps/sop -m pytest -c test/pytest.ini src/apps/sop/test/ -v
	coverage report --rcfile=test/.coveragerc --include="src/apps/sop/*"
	@echo "SOP模块测试完成"

test-agent:
	coverage run --rcfile=test/.coveragerc --branch --source=src/apps/agent -m pytest -c test/pytest.ini src/apps/agent/test/ -v
	coverage report --rcfile=test/.coveragerc --include="src/apps/agent/*"
	@echo "Agent模块测试完成"

test-mcp:
	coverage run --rcfile=test/.coveragerc --branch --source=src/apps/mcp -m pytest -c test/pytest.ini src/apps/mcp/test/ -v
	coverage report --rcfile=test/.coveragerc --include="src/apps/mcp/*"
	@echo "MCP模块测试完成"

test-ai-model:
	coverage run --rcfile=test/.coveragerc --branch --source=src/apps/ai_model -m pytest -c test/pytest.ini src/apps/ai_model/test/ -v
	coverage report --rcfile=test/.coveragerc --include="src/apps/ai_model/*"
	@echo "AI模型模块测试完成"

test-scheduled-task:
	coverage run --rcfile=test/.coveragerc --branch --source=src/apps/scheduled_task -m pytest -c test/pytest.ini src/apps/scheduled_task/test/ -v
	coverage report --rcfile=test/.coveragerc --include="src/apps/scheduled_task/*"
	@echo "定时任务模块测试完成"

# 单模块HTML报告
test-sop-html:
	coverage run --rcfile=test/.coveragerc --branch --source=src/apps/sop -m pytest -c test/pytest.ini src/apps/sop/test/ -v
	coverage html --rcfile=test/.coveragerc --include="src/apps/sop/*" --directory=htmlcov/sop
	coverage report --rcfile=test/.coveragerc --include="src/apps/sop/*"
	@echo "SOP模块HTML报告: htmlcov/sop/index.html"

# 清理测试相关文件
clean-test:
	./test/scripts/clean_test.sh

# 清理覆盖率文件（保持向后兼容）
clean-cov: clean-test

# 代码格式化
format:
	black src/
	
# 代码检查
lint:
	flake8 src/
	mypy src/

# 完整检查（格式化 + 检查 + 测试）
check: format lint test-cov

# 高级测试命令示例
# 测试特定文件
test-file:
	@echo "使用方法: make test-file FILE=src/apps/sop/test/test_service.py"
	@if [ -z "$(FILE)" ]; then echo "请指定FILE参数"; exit 1; fi
	coverage run --branch --source=$(shell dirname $(shell dirname $(FILE))) -m pytest $(FILE) -v
	coverage report --include="$(shell dirname $(shell dirname $(FILE)))/*"

# 测试特定类
test-class:
	@echo "使用方法: make test-class CLASS=src/apps/sop/test/test_service.py::TestSOPService"
	@if [ -z "$(CLASS)" ]; then echo "请指定CLASS参数"; exit 1; fi
	coverage run --branch --source=$(shell dirname $(shell dirname $(shell echo $(CLASS) | cut -d: -f1))) -m pytest $(CLASS) -v

# 测试特定方法
test-method:
	@echo "使用方法: make test-method METHOD=src/apps/sop/test/test_service.py::TestSOPService::test_create_sop"
	@if [ -z "$(METHOD)" ]; then echo "请指定METHOD参数"; exit 1; fi  
	coverage run --branch --source=$(shell dirname $(shell dirname $(shell echo $(METHOD) | cut -d: -f1))) -m pytest $(METHOD) -v

# 开发环境启动
dev:
	python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000