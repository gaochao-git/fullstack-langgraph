#!/usr/bin/env python3
"""
MCP Servers 管理脚本
支持标准命令: init, start, stop, restart, status, cleanup
"""

import os
import sys
import yaml
import subprocess
import signal
import time
import psutil
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 脚本目录
SCRIPT_DIR = Path(__file__).parent.absolute()
CONFIG_FILE = SCRIPT_DIR / "config.yaml"
PID_DIR = SCRIPT_DIR / "pids"
LOG_DIR = SCRIPT_DIR / "logs"

# 默认配置（如果配置文件不存在）
DEFAULT_CONFIG = {
    "servers": {
        "db_query": {
            "enabled": True,
            "port": 3001,
            "script": "servers/db_mcp_server.py",
            "display_name": "MySQL数据库服务"
        },
        "ssh_exec": {
            "enabled": True,
            "port": 3002,
            "script": "servers/ssh_mcp_server.py",
            "display_name": "SSH远程连接服务"
        },
        "es_search": {
            "enabled": True,
            "port": 3003,
            "script": "servers/es_mcp_server.py",
            "display_name": "Elasticsearch搜索服务"
        },
        "zabbix_monitor": {
            "enabled": True,
            "port": 3004,
            "script": "servers/zabbix_mcp_server.py",
            "display_name": "Zabbix监控服务"
        },
        "sop_server": {
            "enabled": True,
            "port": 3005,
            "script": "servers/sop_mcp_server.py",
            "display_name": "SOP标准操作程序服务"
        }
    }
}


class MCPServerManager:
    def __init__(self):
        self.config = self.load_config()
        self.ensure_directories()
    
    def load_config(self) -> Dict:
        """加载配置文件"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    # 确保有 servers 配置
                    if 'servers' not in config:
                        logger.warning("配置文件缺少 servers 部分，使用默认配置")
                        return DEFAULT_CONFIG
                    return config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return DEFAULT_CONFIG
        else:
            logger.info("配置文件不存在，使用默认配置")
            return DEFAULT_CONFIG
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        PID_DIR.mkdir(exist_ok=True)
        LOG_DIR.mkdir(exist_ok=True)
    
    def get_pid_file(self, server_name: str) -> Path:
        """获取PID文件路径"""
        return PID_DIR / f"{server_name}.pid"
    
    def get_log_file(self, server_name: str) -> Path:
        """获取日志文件路径"""
        return LOG_DIR / f"{server_name}.log"
    
    def read_pid(self, server_name: str) -> Optional[int]:
        """读取PID文件"""
        pid_file = self.get_pid_file(server_name)
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    return int(f.read().strip())
            except:
                pass
        return None
    
    def write_pid(self, server_name: str, pid: int):
        """写入PID文件"""
        pid_file = self.get_pid_file(server_name)
        with open(pid_file, 'w') as f:
            f.write(str(pid))
    
    def remove_pid(self, server_name: str):
        """删除PID文件"""
        pid_file = self.get_pid_file(server_name)
        if pid_file.exists():
            pid_file.unlink()
    
    def is_process_running(self, pid: int) -> bool:
        """检查进程是否运行"""
        try:
            process = psutil.Process(pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
    
    def is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return False
            except socket.error:
                return True
    
    def start_server(self, server_name: str, server_config: Dict) -> bool:
        """启动单个服务器"""
        if not server_config.get('enabled', True):
            logger.info(f"跳过未启用的服务: {server_name}")
            return True
        
        # 检查是否已经运行
        pid = self.read_pid(server_name)
        if pid and self.is_process_running(pid):
            logger.warning(f"{server_name} 已经在运行 (PID: {pid})")
            return True
        
        # 检查端口占用
        port = server_config['port']
        if self.is_port_in_use(port):
            logger.error(f"{server_name} 端口 {port} 已被占用")
            return False
        
        # 启动服务器
        script_path = SCRIPT_DIR / server_config['script']
        log_file = self.get_log_file(server_name)
        
        logger.info(f"启动 {server_config.get('display_name', server_name)} (端口: {port})...")
        
        try:
            # 设置环境变量
            env = os.environ.copy()
            env['PYTHONPATH'] = str(SCRIPT_DIR)
            env['MCP_SERVER_NAME'] = server_name
            env['MCP_SERVER_PORT'] = str(port)
            
            # 启动进程
            with open(log_file, 'a') as log:
                process = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    env=env,
                    stdout=log,
                    stderr=log,
                    start_new_session=True
                )
            
            # 等待服务启动
            time.sleep(2)
            
            # 检查进程是否还在运行
            if process.poll() is None:
                self.write_pid(server_name, process.pid)
                logger.info(f"✅ {server_name} 启动成功 (PID: {process.pid})")
                return True
            else:
                logger.error(f"❌ {server_name} 启动失败")
                return False
                
        except Exception as e:
            logger.error(f"启动 {server_name} 时出错: {e}")
            return False
    
    def stop_server(self, server_name: str) -> bool:
        """停止单个服务器"""
        pid = self.read_pid(server_name)
        if not pid:
            logger.info(f"{server_name} 未运行")
            return True
        
        if not self.is_process_running(pid):
            logger.warning(f"{server_name} 进程不存在")
            self.remove_pid(server_name)
            return True
        
        logger.info(f"停止 {server_name} (PID: {pid})...")
        
        try:
            process = psutil.Process(pid)
            # 优雅停止
            process.terminate()
            
            # 等待进程退出（最多10秒）
            try:
                process.wait(timeout=10)
            except psutil.TimeoutExpired:
                logger.warning(f"进程未响应SIGTERM，强制终止...")
                process.kill()
                process.wait(timeout=5)
            
            self.remove_pid(server_name)
            logger.info(f"✅ {server_name} 已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止 {server_name} 时出错: {e}")
            return False
    
    def init(self):
        """初始化组件"""
        logger.info("初始化 MCP Servers...")
        
        # 确保目录存在
        self.ensure_directories()
        
        # 检查Python环境
        logger.info(f"Python版本: {sys.version}")
        
        # 创建示例配置文件
        if not CONFIG_FILE.exists():
            logger.info("创建示例配置文件...")
            example_config = """# MCP服务器配置文件
servers:
  db_query:
    enabled: true
    port: 3001
    script: "servers/db_mcp_server.py"
    display_name: "MySQL数据库服务"
    config:
      host: localhost
      port: 3306
      username: root
      password: ""
      
  ssh_exec:
    enabled: true
    port: 3002
    script: "servers/ssh_mcp_server.py"
    display_name: "SSH远程连接服务"
    config:
      host: localhost
      port: 22
      username: root
      password: ""
      
  es_search:
    enabled: true
    port: 3003
    script: "servers/es_mcp_server.py"
    display_name: "Elasticsearch搜索服务"
    config:
      base_url: "http://localhost:9200"
      
  zabbix_monitor:
    enabled: true
    port: 3004
    script: "servers/zabbix_mcp_server.py"
    display_name: "Zabbix监控服务"
    config:
      url: "http://localhost/zabbix"
      username: "Admin"
      password: "zabbix"
      
  sop_server:
    enabled: true
    port: 3005
    script: "servers/sop_mcp_server.py"
    display_name: "SOP标准操作程序服务"
    config:
      api_url: "http://localhost:8000"
"""
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                f.write(example_config)
            logger.info(f"✅ 已创建配置文件: {CONFIG_FILE}")
        
        logger.info("✅ 初始化完成")
    
    def start(self):
        """启动所有服务"""
        logger.info("启动 MCP Servers...")
        
        servers = self.config.get('servers', {})
        if not servers:
            logger.error("没有配置任何服务器")
            return
        
        success = 0
        failed = 0
        
        for server_name, server_config in servers.items():
            if self.start_server(server_name, server_config):
                success += 1
            else:
                failed += 1
        
        logger.info(f"\n{'='*80}")
        if success > 0:
            logger.info(f"✅ 成功启动 {success} 个服务")
        if failed > 0:
            logger.error(f"❌ {failed} 个服务启动失败")
    
    def stop(self):
        """停止所有服务"""
        logger.info("停止 MCP Servers...")
        
        servers = self.config.get('servers', {})
        success = 0
        failed = 0
        
        for server_name in servers:
            if self.stop_server(server_name):
                success += 1
            else:
                failed += 1
        
        if failed == 0:
            logger.info("✅ 所有MCP服务器已停止")
        else:
            logger.error(f"❌ {failed} 个服务器停止失败")
    
    def restart(self):
        """重启所有服务"""
        logger.info("重启 MCP Servers...")
        self.stop()
        time.sleep(2)
        self.start()
    
    def status(self):
        """查看服务状态"""
        logger.info("MCP Servers 状态")
        logger.info("="*80)
        
        servers = self.config.get('servers', {})
        running = 0
        stopped = 0
        
        for server_name, server_config in servers.items():
            if not server_config.get('enabled', True):
                logger.info(f"○ {server_name} 未启用")
                continue
            
            pid = self.read_pid(server_name)
            port = server_config['port']
            display_name = server_config.get('display_name', server_name)
            
            if pid and self.is_process_running(pid):
                logger.info(f"● {display_name} 运行中")
                logger.info(f"    PID: {pid}, 端口: {port}")
                running += 1
            else:
                logger.error(f"● {display_name} 未运行")
                if pid:
                    logger.warning(f"    PID文件存在但进程不存在")
                stopped += 1
        
        logger.info("="*80)
        logger.info(f"总计: {running} 个运行中, {stopped} 个已停止")
    
    def cleanup(self):
        """清理临时文件"""
        logger.info("清理临时文件...")
        
        # 清理PID文件
        for pid_file in PID_DIR.glob("*.pid"):
            pid_file.unlink()
            logger.info(f"删除 {pid_file}")
        
        # 清理日志文件（可选）
        # for log_file in LOG_DIR.glob("*.log"):
        #     log_file.unlink()
        #     logger.info(f"删除 {log_file}")
        
        logger.info("✅ 清理完成")


def main():
    parser = argparse.ArgumentParser(description='MCP Servers 管理工具')
    parser.add_argument(
        'command',
        choices=['init', 'start', 'stop', 'restart', 'status', 'cleanup'],
        help='要执行的命令'
    )
    
    args = parser.parse_args()
    
    manager = MCPServerManager()
    
    # 执行对应的命令
    command_map = {
        'init': manager.init,
        'start': manager.start,
        'stop': manager.stop,
        'restart': manager.restart,
        'status': manager.status,
        'cleanup': manager.cleanup
    }
    
    try:
        command_map[args.command]()
    except KeyboardInterrupt:
        logger.info("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        import traceback
        logger.error(f"执行命令时出错: {e}")
        logger.error(f"详细错误信息：\n{traceback.format_exc()}")
        sys.exit(1)


if __name__ == '__main__':
    main()