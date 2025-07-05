"""
MySQL工具 - 使用LangChain工具框架
"""

import pymysql
import json
from typing import Dict, Any, List, Optional
import logging
from langchain.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

def _create_mysql_connection():
    """创建新的MySQL连接，每次调用都重新连接"""
    # 默认连接参数，按优先级排序
    default_configs = [
        {"host": "82.156.146.51", "username": "gaochao", "password": "fffjjj"},
        {"host": "82.156.146.51", "username": "root", "password": "123456"},
        {"host": "82.156.146.51", "username": "mysql", "password": "mysql"}
    ]
    
    for config in default_configs:
        try:
            connection_config = {
                'host': config["host"],
                'port': 3306,
                'user': config["username"],
                'password': config["password"],
                'charset': 'utf8mb4',
                'autocommit': True,
                'database': 'information_schema'
            }
            
            connection = pymysql.connect(**connection_config)
            logger.info(f"MySQL连接成功，用户: {config['username']}")
            return connection
            
        except Exception as e:
            logger.debug(f"尝试用户 {config['username']} 失败: {e}")
            continue
    
    raise Exception("无法建立MySQL连接，请检查数据库服务状态和凭据")

class ProcessListInput(BaseModel):
    """进程列表查询输入参数"""
    connection_name: str = Field(default="default", description="连接名称")
    show_full: bool = Field(default=True, description="显示完整查询语句")

@tool("get_mysql_processlist", args_schema=ProcessListInput)
def get_mysql_processlist(
    connection_name: str = "default",
    show_full: bool = True
) -> str:
    """获取MySQL进程列表。用于查看当前运行的SQL查询和连接状态。
    
    Args:
        connection_name: MySQL连接名称（此参数保留兼容性，实际会创建新连接）
        show_full: 是否显示完整的查询语句
    
    Returns:
        包含进程列表的JSON字符串
    """
    connection = None
    try:
        connection = _create_mysql_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        if show_full:
            cursor.execute("SHOW FULL PROCESSLIST")
        else:
            cursor.execute("SHOW PROCESSLIST")
        
        processes = cursor.fetchall()
        
        # 转换时间格式并添加分析
        process_data = []
        long_running_queries = []
        
        for process in processes:
            time_seconds = process.get('Time', 0) or 0
            
            process_info = {
                "id": process.get('Id'),
                "user": process.get('User'),
                "host": process.get('Host'),
                "database": process.get('db'),
                "command": process.get('Command'),
                "time_seconds": time_seconds,
                "state": process.get('State'),
                "info": process.get('Info')
            }
            
            process_data.append(process_info)
            
            # 标记长时间运行的查询（超过30秒）
            if time_seconds > 30 and process.get('Command') not in ['Sleep', 'Binlog Dump']:
                long_running_queries.append(process_info)
        
        cursor.close()
        
        return json.dumps({
            "total_processes": len(process_data),
            "processes": process_data,
            "long_running_queries": long_running_queries,
            "analysis": {
                "sleeping_connections": len([p for p in process_data if p["command"] == "Sleep"]),
                "active_queries": len([p for p in process_data if p["command"] == "Query"]),
                "long_running_count": len(long_running_queries)
            }
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting MySQL processlist: {e}")
        return json.dumps({"error": f"Failed to get processlist: {str(e)}"})
    finally:
        if connection:
            connection.close()

class DatabaseStatusInput(BaseModel):
    """数据库状态查询输入参数"""
    connection_name: str = Field(default="default", description="连接名称")
    status_variables: Optional[List[str]] = Field(default=None, description="指定状态变量列表")

@tool("get_mysql_status", args_schema=DatabaseStatusInput)
def get_mysql_status(
    connection_name: str = "default",
    status_variables: Optional[List[str]] = None
) -> str:
    """获取MySQL数据库状态信息。用于监控数据库性能指标和运行状态。
    
    Args:
        connection_name: MySQL连接名称（此参数保留兼容性，实际会创建新连接）
        status_variables: 指定要查询的状态变量列表
    
    Returns:
        包含数据库状态的JSON字符串
    """
    connection = None
    try:
        connection = _create_mysql_connection()
        cursor = connection.cursor()
        
        # 获取状态变量
        if status_variables:
            status_data = {}
            for var in status_variables:
                cursor.execute(f"SHOW STATUS LIKE '{var}'")
                result = cursor.fetchone()
                if result:
                    status_data[result[0]] = result[1]
        else:
            cursor.execute("SHOW STATUS")
            status_results = cursor.fetchall()
            status_data = {row[0]: row[1] for row in status_results}
        
        # 重要指标分析
        key_metrics = {}
        
        # 连接相关
        if 'Connections' in status_data:
            key_metrics['connections'] = {
                'total_connections': int(status_data.get('Connections', 0)),
                'aborted_connects': int(status_data.get('Aborted_connects', 0)),
                'aborted_clients': int(status_data.get('Aborted_clients', 0)),
                'threads_connected': int(status_data.get('Threads_connected', 0)),
                'threads_running': int(status_data.get('Threads_running', 0))
            }
        
        # 查询相关
        questions = int(status_data.get('Questions', 0))
        uptime = int(status_data.get('Uptime', 1))
        
        if questions > 0 and uptime > 0:
            key_metrics['queries'] = {
                'questions_total': questions,
                'queries_per_second': round(questions / uptime, 2),
                'slow_queries': int(status_data.get('Slow_queries', 0)),
                'select_queries': int(status_data.get('Com_select', 0)),
                'insert_queries': int(status_data.get('Com_insert', 0)),
                'update_queries': int(status_data.get('Com_update', 0)),
                'delete_queries': int(status_data.get('Com_delete', 0))
            }
        
        # InnoDB相关
        if 'Innodb_buffer_pool_size' in status_data:
            key_metrics['innodb'] = {
                'buffer_pool_pages_total': int(status_data.get('Innodb_buffer_pool_pages_total', 0)),
                'buffer_pool_pages_free': int(status_data.get('Innodb_buffer_pool_pages_free', 0)),
                'buffer_pool_pages_dirty': int(status_data.get('Innodb_buffer_pool_pages_dirty', 0)),
                'buffer_pool_read_requests': int(status_data.get('Innodb_buffer_pool_read_requests', 0)),
                'buffer_pool_reads': int(status_data.get('Innodb_buffer_pool_reads', 0)),
                'data_reads': int(status_data.get('Innodb_data_reads', 0)),
                'data_writes': int(status_data.get('Innodb_data_writes', 0))
            }
        
        cursor.close()
        
        return json.dumps({
            "uptime_seconds": uptime,
            "key_metrics": key_metrics,
            "all_status_variables": status_data if not status_variables else None
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting MySQL status: {e}")
        return json.dumps({"error": f"Failed to get MySQL status: {str(e)}"})
    finally:
        if connection:
            connection.close()

class SlowQueryAnalysisInput(BaseModel):
    """慢查询分析输入参数"""
    connection_name: str = Field(default="default", description="连接名称")
    limit: int = Field(default=10, description="返回记录数量")

@tool("analyze_slow_queries", args_schema=SlowQueryAnalysisInput)
def analyze_slow_queries(
    connection_name: str = "default",
    limit: int = 10
) -> str:
    """分析慢查询日志。用于识别性能问题和优化机会。
    
    Args:
        connection_name: MySQL连接名称
        limit: 返回的慢查询记录数量
    
    Returns:
        包含慢查询分析结果的JSON字符串
    """
    try:
        connection = _get_mysql_connection(connection_name)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 检查慢查询日志是否启用
        cursor.execute("SHOW VARIABLES LIKE 'slow_query_log'")
        slow_log_status = cursor.fetchone()
        
        cursor.execute("SHOW VARIABLES LIKE 'long_query_time'")
        long_query_time = cursor.fetchone()
        
        # 获取性能模式中的慢查询信息
        slow_queries = []
        
        try:
            # 从performance_schema获取慢查询信息
            query = """
            SELECT 
                digest_text,
                count_star as exec_count,
                avg_timer_wait/1000000000000 as avg_time_seconds,
                max_timer_wait/1000000000000 as max_time_seconds,
                sum_timer_wait/1000000000000 as total_time_seconds,
                sum_rows_examined as total_rows_examined,
                sum_rows_sent as total_rows_sent,
                first_seen,
                last_seen
            FROM performance_schema.events_statements_summary_by_digest 
            WHERE avg_timer_wait > %s * 1000000000000
            ORDER BY avg_timer_wait DESC 
            LIMIT %s
            """
            
            long_query_seconds = float(long_query_time['Value']) if long_query_time else 1.0
            cursor.execute(query, (long_query_seconds, limit))
            slow_queries = cursor.fetchall()
            
        except Exception as perf_error:
            logger.warning(f"Could not query performance_schema: {perf_error}")
            
            # 回退到基本的慢查询统计
            cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
            slow_count = cursor.fetchone()
            slow_queries = [{"note": f"Slow queries count: {slow_count['Value'] if slow_count else 0}"}]
        
        # 获取当前运行的潜在慢查询
        cursor.execute("SHOW FULL PROCESSLIST")
        current_processes = cursor.fetchall()
        
        potential_slow = []
        for process in current_processes:
            if (process.get('Time', 0) or 0) > 5 and process.get('Command') == 'Query':
                potential_slow.append({
                    "id": process.get('Id'),
                    "time_seconds": process.get('Time'),
                    "user": process.get('User'),
                    "database": process.get('db'),
                    "query": process.get('Info')
                })
        
        cursor.close()
        
        return json.dumps({
            "slow_query_log_enabled": slow_log_status['Value'].lower() == 'on' if slow_log_status else False,
            "long_query_time_seconds": float(long_query_time['Value']) if long_query_time else None,
            "historical_slow_queries": slow_queries,
            "current_potential_slow_queries": potential_slow,
            "recommendations": [
                "Enable slow_query_log if not already enabled",
                "Consider lowering long_query_time if needed",
                "Review and optimize queries with high avg_time_seconds",
                "Check for missing indexes on queries with high rows_examined"
            ]
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error analyzing slow queries: {e}")
        return json.dumps({"error": f"Failed to analyze slow queries: {str(e)}"})
    finally:
        if connection:
            connection.close()

class TableAnalysisInput(BaseModel):
    """表分析输入参数"""
    connection_name: str = Field(default="default", description="连接名称")
    database_name: str = Field(description="数据库名称")
    table_name: Optional[str] = Field(default=None, description="表名称，为空则分析所有表")

@tool("analyze_table_stats", args_schema=TableAnalysisInput)
def analyze_table_stats(
    connection_name: str = "default",
    database_name: str = "",
    table_name: Optional[str] = None
) -> str:
    """分析表统计信息。用于了解表大小、索引使用情况等。
    
    Args:
        connection_name: MySQL连接名称
        database_name: 数据库名称
        table_name: 表名称，为空则分析所有表
    
    Returns:
        包含表统计信息的JSON字符串
    """
    connection = None
    try:
        connection = _create_mysql_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 构建查询条件
        where_clause = "WHERE table_schema = %s"
        params = [database_name]
        
        if table_name:
            where_clause += " AND table_name = %s"
            params.append(table_name)
        
        # 获取表统计信息
        query = f"""
        SELECT 
            table_name,
            engine,
            table_rows,
            avg_row_length,
            data_length,
            index_length,
            data_free,
            auto_increment,
            create_time,
            update_time,
            check_time,
            table_collation
        FROM information_schema.tables 
        {where_clause}
        ORDER BY data_length DESC
        """
        
        cursor.execute(query, params)
        tables = cursor.fetchall()
        
        table_stats = []
        total_data_size = 0
        total_index_size = 0
        
        for table in tables:
            data_size = table.get('data_length', 0) or 0
            index_size = table.get('index_length', 0) or 0
            total_size = data_size + index_size
            
            total_data_size += data_size
            total_index_size += index_size
            
            # 格式化大小
            def format_bytes(bytes_value):
                if bytes_value >= 1024**3:
                    return f"{bytes_value / (1024**3):.2f} GB"
                elif bytes_value >= 1024**2:
                    return f"{bytes_value / (1024**2):.2f} MB"
                elif bytes_value >= 1024:
                    return f"{bytes_value / 1024:.2f} KB"
                else:
                    return f"{bytes_value} B"
            
            table_info = {
                "table_name": table.get('table_name'),
                "engine": table.get('engine'),
                "estimated_rows": table.get('table_rows', 0),
                "avg_row_length": table.get('avg_row_length', 0),
                "data_size_bytes": data_size,
                "data_size_formatted": format_bytes(data_size),
                "index_size_bytes": index_size,
                "index_size_formatted": format_bytes(index_size),
                "total_size_bytes": total_size,
                "total_size_formatted": format_bytes(total_size),
                "free_space_bytes": table.get('data_free', 0) or 0,
                "auto_increment": table.get('auto_increment'),
                "created": table.get('create_time').isoformat() if table.get('create_time') else None,
                "updated": table.get('update_time').isoformat() if table.get('update_time') else None,
                "collation": table.get('table_collation')
            }
            
            table_stats.append(table_info)
        
        # 获取索引统计信息（如果指定了单个表）
        index_stats = []
        if table_name and tables:
            index_query = """
            SELECT 
                index_name,
                column_name,
                seq_in_index,
                non_unique,
                index_type,
                cardinality
            FROM information_schema.statistics 
            WHERE table_schema = %s AND table_name = %s
            ORDER BY index_name, seq_in_index
            """
            
            cursor.execute(index_query, [database_name, table_name])
            indexes = cursor.fetchall()
            
            current_index = None
            for idx in indexes:
                if current_index != idx['index_name']:
                    index_stats.append({
                        "index_name": idx['index_name'],
                        "columns": [idx['column_name']],
                        "unique": idx['non_unique'] == 0,
                        "type": idx['index_type'],
                        "cardinality": idx['cardinality']
                    })
                    current_index = idx['index_name']
                else:
                    # 多列索引
                    index_stats[-1]["columns"].append(idx['column_name'])
        
        cursor.close()
        
        def format_bytes(bytes_value):
            if bytes_value >= 1024**3:
                return f"{bytes_value / (1024**3):.2f} GB"
            elif bytes_value >= 1024**2:
                return f"{bytes_value / (1024**2):.2f} MB"
            elif bytes_value >= 1024:
                return f"{bytes_value / 1024:.2f} KB"
            else:
                return f"{bytes_value} B"
        
        result = {
            "database": database_name,
            "table_count": len(table_stats),
            "total_data_size": format_bytes(total_data_size),
            "total_index_size": format_bytes(total_index_size),
            "total_size": format_bytes(total_data_size + total_index_size),
            "tables": table_stats
        }
        
        if index_stats:
            result["indexes"] = index_stats
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        logger.error(f"Error analyzing table stats: {e}")
        return json.dumps({"error": f"Failed to analyze table stats: {str(e)}"})
    finally:
        if connection:
            connection.close()

class CustomQueryInput(BaseModel):
    """自定义查询输入参数"""
    connection_name: str = Field(default="default", description="连接名称")
    query: str = Field(description="SQL查询语句")
    limit: int = Field(default=100, description="结果限制数量")

@tool("execute_diagnostic_query", args_schema=CustomQueryInput)
def execute_diagnostic_query(
    connection_name: str = "default",
    query: str = "",
    limit: int = 100
) -> str:
    """执行诊断SQL查询。用于执行自定义的数据库诊断查询。
    
    Args:
        connection_name: MySQL连接名称
        query: SQL查询语句
        limit: 结果限制数量
    
    Returns:
        包含查询结果的JSON字符串
    """
    # 安全检查：只允许SELECT查询和特定的SHOW语句
    query_upper = query.strip().upper()
    allowed_commands = ['SELECT', 'SHOW', 'EXPLAIN', 'DESCRIBE', 'DESC']
    
    if not any(query_upper.startswith(cmd) for cmd in allowed_commands):
        return json.dumps({
            "error": "Only SELECT, SHOW, EXPLAIN, and DESCRIBE statements are allowed for diagnostic queries"
        })
    
    try:
        connection = _get_mysql_connection(connection_name)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 添加LIMIT子句以防止返回过多数据
        if query_upper.startswith('SELECT') and 'LIMIT' not in query_upper:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # 获取列信息
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        cursor.close()
        
        return json.dumps({
            "query": query,
            "columns": columns,
            "row_count": len(results),
            "results": results
        }, indent=2, default=str)  # default=str 处理datetime等类型
        
    except Exception as e:
        logger.error(f"Error executing diagnostic query: {e}")
        return json.dumps({"error": f"Failed to execute query: {str(e)}"})
    finally:
        if connection:
            connection.close()

# 导出所有工具
mysql_tools = [
    get_mysql_processlist,
    get_mysql_status,
    analyze_slow_queries,
    analyze_table_stats,
    execute_diagnostic_query
]
