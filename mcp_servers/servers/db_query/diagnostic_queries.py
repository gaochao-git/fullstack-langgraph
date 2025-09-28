"""
数据库故障诊断常用SQL模板
仅包含只读查询，用于故障排查
"""

# MySQL 诊断查询模板
MYSQL_DIAGNOSTIC_QUERIES = {
    "connection_status": {
        "name": "连接状态检查",
        "sql": """
        SELECT 
            @@max_connections as max_connections,
            COUNT(*) as current_connections,
            COUNT(*) / @@max_connections * 100 as usage_percent
        FROM information_schema.processlist
        """,
        "description": "检查当前连接数和最大连接数配置"
    },
    
    "active_processes": {
        "name": "活跃进程列表",
        "sql": """
        SELECT 
            id, user, host, db, command, time, state,
            LEFT(info, 200) as query_preview
        FROM information_schema.processlist 
        WHERE command != 'Sleep'
        ORDER BY time DESC
        LIMIT 50
        """,
        "description": "查看当前活跃的数据库进程"
    },
    
    "slow_queries": {
        "name": "慢查询检查",
        "sql": """
        SELECT 
            id, user, db, time, state,
            LEFT(info, 500) as query
        FROM information_schema.processlist 
        WHERE command = 'Query' AND time > 5
        ORDER BY time DESC
        """,
        "description": "查找执行时间超过5秒的查询"
    },
    
    "table_locks": {
        "name": "表锁情况",
        "sql": """
        SELECT 
            l.*, p.user, p.host, p.db, p.command, p.time, p.state
        FROM information_schema.innodb_locks l
        JOIN information_schema.processlist p ON l.lock_trx_id = p.id
        ORDER BY l.lock_id
        """,
        "description": "查看当前的表锁情况"
    },
    
    "innodb_status_summary": {
        "name": "InnoDB状态摘要",
        "sql": """
        SELECT 
            variable_name, variable_value
        FROM information_schema.global_status
        WHERE variable_name IN (
            'Innodb_buffer_pool_hit_rate',
            'Innodb_buffer_pool_pages_total',
            'Innodb_buffer_pool_pages_free',
            'Innodb_buffer_pool_pages_dirty',
            'Innodb_row_lock_current_waits',
            'Innodb_row_lock_time_avg'
        )
        """,
        "description": "InnoDB关键性能指标"
    },
    
    "deadlock_info": {
        "name": "死锁信息",
        "sql": """
        SHOW ENGINE INNODB STATUS
        """,
        "description": "查看最近的死锁信息（需要解析输出）"
    },
    
    "table_sizes": {
        "name": "表大小统计",
        "sql": """
        SELECT 
            table_schema,
            table_name,
            ROUND(data_length/1024/1024, 2) as data_size_mb,
            ROUND(index_length/1024/1024, 2) as index_size_mb,
            ROUND((data_length+index_length)/1024/1024, 2) as total_size_mb,
            table_rows
        FROM information_schema.tables
        WHERE table_schema = ?
        ORDER BY total_size_mb DESC
        LIMIT 20
        """,
        "description": "查看数据库中最大的表"
    },
    
    "index_usage": {
        "name": "索引使用情况",
        "sql": """
        SELECT 
            object_schema,
            object_name,
            index_name,
            count_read,
            count_write,
            count_fetch,
            count_insert,
            count_update,
            count_delete
        FROM performance_schema.table_io_waits_summary_by_index_usage
        WHERE object_schema = ? AND object_name = ?
        ORDER BY count_read DESC
        """,
        "description": "查看表的索引使用情况"
    },
    
    "recent_errors": {
        "name": "最近的错误",
        "sql": """
        SELECT 
            logged,
            prio,
            subsystem,
            data
        FROM performance_schema.error_log
        WHERE prio IN ('Error', 'Warning')
        ORDER BY logged DESC
        LIMIT 50
        """,
        "description": "查看最近的数据库错误日志"
    },
    
    "connection_errors": {
        "name": "连接错误统计",
        "sql": """
        SELECT 
            variable_name, variable_value
        FROM information_schema.global_status
        WHERE variable_name LIKE '%connect%error%'
           OR variable_name LIKE 'Aborted_%'
        """,
        "description": "查看连接相关的错误统计"
    },
    
    "buffer_pool_stats": {
        "name": "缓冲池统计",
        "sql": """
        SELECT 
            page_type,
            pool_id,
            lru_position,
            fix_count,
            is_hashed,
            oldest_modification,
            newest_modification
        FROM information_schema.innodb_buffer_page
        WHERE pool_id = 0
        LIMIT 100
        """,
        "description": "查看InnoDB缓冲池页面信息"
    },
    
    "thread_statistics": {
        "name": "线程统计",
        "sql": """
        SELECT 
            variable_name, variable_value
        FROM information_schema.global_status
        WHERE variable_name LIKE 'Threads_%'
        """,
        "description": "查看线程相关统计信息"
    }
}

# PostgreSQL 诊断查询模板
POSTGRESQL_DIAGNOSTIC_QUERIES = {
    "connection_status": {
        "name": "连接状态检查",
        "sql": """
        SELECT 
            max_conn,
            used,
            res_for_super,
            max_conn - used - res_for_super AS available
        FROM 
            (SELECT count(*) AS used FROM pg_stat_activity) t1,
            (SELECT setting::int AS max_conn FROM pg_settings WHERE name='max_connections') t2,
            (SELECT setting::int AS res_for_super FROM pg_settings WHERE name='superuser_reserved_connections') t3
        """,
        "description": "检查当前连接数和可用连接数"
    },
    
    "active_queries": {
        "name": "活跃查询",
        "sql": """
        SELECT 
            pid,
            usename,
            application_name,
            client_addr,
            backend_start,
            state,
            state_change,
            query_start,
            now() - query_start AS duration,
            LEFT(query, 500) as query
        FROM pg_stat_activity
        WHERE state != 'idle'
        ORDER BY query_start
        """,
        "description": "查看当前活跃的查询"
    },
    
    "blocking_queries": {
        "name": "阻塞查询",
        "sql": """
        SELECT 
            blocked_locks.pid AS blocked_pid,
            blocked_activity.usename AS blocked_user,
            blocking_locks.pid AS blocking_pid,
            blocking_activity.usename AS blocking_user,
            blocked_activity.query AS blocked_statement,
            blocking_activity.query AS blocking_statement
        FROM pg_catalog.pg_locks blocked_locks
        JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
        JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
            AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
            AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
            AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
            AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
            AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
            AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
            AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
            AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
            AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
            AND blocking_locks.pid != blocked_locks.pid
        JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
        WHERE NOT blocked_locks.granted
        """,
        "description": "查找阻塞和被阻塞的查询"
    }
}

# 只读查询白名单（支持的安全查询类型）
ALLOWED_QUERY_PATTERNS = [
    r"^\s*SELECT\s+",
    r"^\s*SHOW\s+",
    r"^\s*DESC(RIBE)?\s+",
    r"^\s*EXPLAIN\s+",
    r"^\s*WITH\s+.*\s+SELECT\s+"
]

# 危险关键词黑名单
DANGEROUS_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE",
    "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL", "MERGE", "REPLACE"
]