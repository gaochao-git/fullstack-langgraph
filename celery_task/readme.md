# Celery 任务队列系统

## 项目结构
celery_task_system/
├── celery_app/
│   ├── __init__.py
│   ├── celery.py      # Celery 应用实例
│   ├── config.py      # 配置文件
│   ├── models.py      # 数据库模型
│   ├── scheduler.py   # 自定义调度器
│   └── tasks.py       # 任务定义
├── scripts/
│   ├── task_manager.py        # 异步任务管理工具
│   ├── periodic_task_manager.py # 定时任务管理工具
│   └── test_task.py           # 测试任务提交脚本
│   └── schema.sql             # 数据库表结构
├── run_worker.py        # Worker 启动脚本
├── run_beat.py          # Beat 启动脚本
└── requirements.txt   # 项目依赖


## 启动步骤
1. 初始化库表schema.sql
2. 启动任务执行器
python run_worker.py
3. 启动定时任务调度
python run_beat.py
4. 测试任务提交
python scripts/test_task.py
5. 查看任务状态
python scripts/task_manager.py details <task_id> --show-result
