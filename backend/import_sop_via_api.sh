#!/bin/bash

# SOP数据通过API导入脚本
# 使用curl调用API接口导入knowledge base中的SOP数据

set -e  # 出错时退出

API_BASE_URL="http://localhost:8000/api/sops"
KNOWLEDGE_BASE_DIR="src/knowledge_base/diagnostic_sop"

echo "🚀 开始通过API导入SOP数据..."

# 检查API是否可用
echo "🔍 检查API服务状态..."
if ! curl -s --connect-timeout 5 "${API_BASE_URL}/list" > /dev/null; then
    echo "❌ API服务不可用，请确保后端服务已启动 (python -m uvicorn src.api.app:app --reload)"
    exit 1
fi
echo "✅ API服务可用"

# 导入MySQL SOP数据
echo ""
echo "📁 导入MySQL诊断SOP..."

# SOP-DB-001: MySQL响应耗时升高诊断
echo "  📝 导入 SOP-DB-001..."
curl -X POST "${API_BASE_URL}/" \
  -H "Content-Type: application/json" \
  -d '{
    "sop_id": "SOP-DB-001",
    "sop_title": "MySQL数据库响应耗时升高诊断",
    "sop_category": "database",
    "sop_description": "诊断MySQL数据库响应时间过长的标准操作程序",
    "sop_severity": "high",
    "steps": [
      {
        "step": 1,
        "description": "获取慢查询日志配置和阈值设置",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SHOW VARIABLES WHERE Variable_name IN ('long_query_time', 'slow_query_log');",
        "requires_approval": false
      },
      {
        "step": 2,
        "description": "确定分析范围",
        "ai_generated": true,
        "tool": "llm",
        "args": "根据用户描述的响应耗时和慢查询阈值，确定分析范围，如果用户告诉了范围用用户的，否则用报警时间前后5分钟",
        "requires_approval": false
      },
      {
        "step": 3,
        "description": "大模型判断是否需要分析慢查询日志",
        "ai_generated": true,
        "tool": "llm",
        "args": "如果响应耗时小于慢查询阈值则跳过慢日志分析直接执行第5步，如果大于阈值则继续第4步",
        "requires_approval": false
      },
      {
        "step": 4,
        "description": "从ES中查询指定时间范围的慢查询日志，分析是写慢查询还是读慢查询，查看扫描行数和锁等待情况",
        "ai_generated": true,
        "tool": "get_es_data",
        "args": "index: mysql-slow-*, start_time: 动态生成, end_time: 动态生成, query: 动态生成,获取一条数据看看有哪些字段然后生成",
        "requires_approval": false
      },
      {
        "step": 5,
        "description": "获取指定时间范围内的磁盘IO使用率和CPU使用率，检查是否存在瓶颈或异常波动",
        "ai_generated": true,
        "tool": "get_zabbix_metric_data",
        "args": "metric: [system.cpu.util[,user], disk.io.util[vda]], start_time: 动态生成, end_time: 动态生成",
        "requires_approval": false
      },
      {
        "step": 6,
        "description": "如果CPU或者磁盘IO有瓶颈且当前仍然存在瓶颈，则排查CPU和IO占用前5名进程",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "top -b -n1 | head -12; iotop -b -n1 | head -10",
        "requires_approval": false
      }
    ],
    "tools_required": ["execute_mysql_query", "get_es_data", "get_zabbix_metric_data", "execute_system_command", "llm"],
    "sop_recommendations": "建议优化识别到的慢查询SQL，为高频查询字段添加索引，重构复杂查询，联系DBA进行查询优化",
    "team_name": "ops-team"
  }' \
  -w "\nHTTP Status: %{http_code}\n" || echo "❌ SOP-DB-001 导入失败"

# SOP-DB-002: MySQL连接数过多诊断
echo "  📝 导入 SOP-DB-002..."
curl -X POST "${API_BASE_URL}/" \
  -H "Content-Type: application/json" \
  -d '{
    "sop_id": "SOP-DB-002",
    "sop_title": "MySQL连接数过多诊断",
    "sop_category": "database",
    "sop_description": "诊断MySQL连接数过多等问题",
    "sop_severity": "high",
    "steps": [
      {
        "step": 1,
        "description": "查看当前活跃连接数量",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SHOW STATUS LIKE 'Threads_connected';",
        "requires_approval": false
      },
      {
        "step": 2,
        "description": "确认最大连接数限制",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SHOW VARIABLES LIKE 'max_connections';",
        "requires_approval": false
      },
      {
        "step": 3,
        "description": "分析连接来源分布",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SELECT USER, HOST, COUNT(*) FROM information_schema.PROCESSLIST GROUP BY USER, HOST;",
        "requires_approval": false
      },
      {
        "step": 4,
        "description": "分析连接状态分布",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SELECT COMMAND, COUNT(*) FROM information_schema.PROCESSLIST GROUP BY COMMAND;",
        "requires_approval": false
      },
      {
        "step": 5,
        "description": "查找长时间等待的连接",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SELECT ID, USER, HOST, TIME, STATE FROM information_schema.PROCESSLIST WHERE TIME > 300;",
        "requires_approval": false
      }
    ],
    "tools_required": ["execute_mysql_query"],
    "sop_recommendations": "建议优化应用连接池配置，增加最大连接数限制，优化长时间运行的查询，实施连接超时策略",
    "team_name": "ops-team"
  }' \
  -w "\nHTTP Status: %{http_code}\n" || echo "❌ SOP-DB-002 导入失败"

# SOP-DB-003: MySQL活跃会话数过多诊断
echo "  📝 导入 SOP-DB-003..."
curl -X POST "${API_BASE_URL}/" \
  -H "Content-Type: application/json" \
  -d '{
    "sop_id": "SOP-DB-003",
    "sop_title": "MySQL活跃会话数过多诊断",
    "sop_category": "database",
    "sop_description": "诊断MySQL活跃会话数过多导致的性能问题",
    "sop_severity": "high",
    "steps": [
      {
        "step": 1,
        "description": "统计当前活跃会话数量",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SELECT COUNT(*) as active_sessions FROM information_schema.PROCESSLIST WHERE COMMAND != 'Sleep';",
        "requires_approval": false
      },
      {
        "step": 2,
        "description": "查看所有活跃会话的详细状态",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO FROM information_schema.PROCESSLIST WHERE COMMAND != 'Sleep' ORDER BY TIME DESC;",
        "requires_approval": false
      },
      {
        "step": 3,
        "description": "识别运行时间超过60秒的会话",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SELECT ID, USER, HOST, TIME, STATE, INFO FROM information_schema.PROCESSLIST WHERE TIME > 60 AND COMMAND != 'Sleep';",
        "requires_approval": false
      },
      {
        "step": 4,
        "description": "分析会话状态分布情况",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SELECT STATE, COUNT(*) as session_count FROM information_schema.PROCESSLIST GROUP BY STATE ORDER BY session_count DESC;",
        "requires_approval": false
      },
      {
        "step": 5,
        "description": "按用户统计会话数量",
        "ai_generated": false,
        "tool": "execute_mysql_query",
        "args": "SELECT USER, COUNT(*) as session_count FROM information_schema.PROCESSLIST GROUP BY USER ORDER BY session_count DESC;",
        "requires_approval": false
      }
    ],
    "tools_required": ["execute_mysql_query"],
    "sop_recommendations": "建议优化长时间运行的查询，调整应用连接池配置，终止异常的长时间会话，优化数据库连接管理策略",
    "team_name": "ops-team"
  }' \
  -w "\nHTTP Status: %{http_code}\n" || echo "❌ SOP-DB-003 导入失败"

# 导入系统SOP数据  
echo ""
echo "📁 导入系统诊断SOP..."

# SOP-SYS-101: 磁盘空间不足诊断
echo "  📝 导入 SOP-SYS-101..."
curl -X POST "${API_BASE_URL}/" \
  -H "Content-Type: application/json" \
  -d '{
    "sop_id": "SOP-SYS-101",
    "sop_title": "磁盘空间不足诊断",
    "sop_category": "system",
    "sop_description": "诊断服务器磁盘空间不足的标准操作程序",
    "sop_severity": "critical",
    "steps": [
      {
        "step": 1,
        "description": "检查磁盘使用情况",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "df -h",
        "requires_approval": true
      },
      {
        "step": 2,
        "description": "找出大文件和目录",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "du -sh --exclude='/proc' --exclude='/sys' /* | sort -rh | head -10",
        "requires_approval": true
      },
      {
        "step": 3,
        "description": "检查日志文件大小",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "find /var/log -size +100M -exec ls -lh {} \\;",
        "requires_approval": false
      },
      {
        "step": 4,
        "description": "分析临时文件占用",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "du -sh /tmp /var/tmp",
        "requires_approval": false
      },
      {
        "step": 5,
        "description": "检查可清理的日志文件",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "find /var/log -name '*.log.*' -mtime +7 -ls",
        "requires_approval": false
      },
      {
        "step": 6,
        "description": "生成排查报告",
        "ai_generated": false,
        "tool": "llm",
        "args": "报告必须包含以下几部分信息：基本信息(时间、对象、问题描述、sop编号)、根因分析(是否确定根因、确定依据)、修复建议、预防措施",
        "requires_approval": false
      }
    ],
    "tools_required": ["execute_system_command", "get_current_time"],
    "sop_recommendations": "建议清理/tmp和/var/tmp中的临时文件，归档或删除旧的日志文件，联系系统管理员扩展磁盘空间，实施日志轮转策略",
    "team_name": "ops-team"
  }' \
  -w "\nHTTP Status: %{http_code}\n" || echo "❌ SOP-SYS-101 导入失败"

# SOP-SYS-102: 系统负载过高诊断
echo "  📝 导入 SOP-SYS-102..."
curl -X POST "${API_BASE_URL}/" \
  -H "Content-Type: application/json" \
  -d '{
    "sop_id": "SOP-SYS-102",
    "sop_title": "系统负载过高诊断",
    "sop_category": "system",
    "sop_description": "诊断Linux系统负载平均值过高的标准操作程序",
    "sop_severity": "high",
    "steps": [
      {
        "step": 1,
        "description": "检查当前负载",
        "ai_generated": false,
        "tool": "get_system_info",
        "args": "uptime && cat /proc/loadavg",
        "requires_approval": false
      },
      {
        "step": 2,
        "description": "查看CPU使用率",
        "ai_generated": false,
        "tool": "analyze_processes",
        "args": "top -bn1 | head -20",
        "requires_approval": false
      },
      {
        "step": 3,
        "description": "检查IO等待",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "iostat -x 1 5",
        "requires_approval": false
      },
      {
        "step": 4,
        "description": "查找高CPU进程",
        "ai_generated": false,
        "tool": "analyze_processes",
        "args": "ps aux --sort=-%cpu | head -10",
        "requires_approval": false
      },
      {
        "step": 5,
        "description": "查找高内存进程",
        "ai_generated": false,
        "tool": "analyze_processes",
        "args": "ps aux --sort=-%mem | head -10",
        "requires_approval": false
      }
    ],
    "tools_required": ["get_system_info", "analyze_processes", "execute_system_command"],
    "sop_recommendations": "建议优化高CPU使用率的进程，优化高内存使用的进程，检查IO瓶颈并优化磁盘性能，联系系统管理员进行资源调优",
    "team_name": "ops-team"
  }' \
  -w "\nHTTP Status: %{http_code}\n" || echo "❌ SOP-SYS-102 导入失败"

# SOP-SYS-103: 内存不足诊断
echo "  📝 导入 SOP-SYS-103..."
curl -X POST "${API_BASE_URL}/" \
  -H "Content-Type: application/json" \
  -d '{
    "sop_id": "SOP-SYS-103",
    "sop_title": "内存不足诊断",
    "sop_category": "system", 
    "sop_description": "诊断系统内存不足和内存泄漏问题",
    "sop_severity": "high",
    "steps": [
      {
        "step": 1,
        "description": "检查内存使用情况",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "free -h && cat /proc/meminfo",
        "requires_approval": false
      },
      {
        "step": 2,
        "description": "查看内存使用排行",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "ps aux --sort=-%mem | head -10",
        "requires_approval": false
      },
      {
        "step": 3,
        "description": "检查OOM日志",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "dmesg | grep -i 'killed process'",
        "requires_approval": false
      },
      {
        "step": 4,
        "description": "分析进程内存详情",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "cat /proc/meminfo | grep -E '(MemTotal|MemFree|MemAvailable|Buffers|Cached)'",
        "requires_approval": false
      },
      {
        "step": 5,
        "description": "检查swap使用情况",
        "ai_generated": false,
        "tool": "execute_system_command",
        "args": "swapon -s && cat /proc/swaps",
        "requires_approval": false
      }
    ],
    "tools_required": ["execute_system_command", "get_current_time"],
    "sop_recommendations": "建议优化高内存使用的进程，增加系统内存，配置或增大swap空间，联系系统管理员分析内存泄漏",
    "team_name": "ops-team"
  }' \
  -w "\nHTTP Status: %{http_code}\n" || echo "❌ SOP-SYS-103 导入失败"

echo ""
echo "🎉 SOP数据导入完成！"
echo ""
echo "📊 查看导入结果："
curl -s "${API_BASE_URL}/list?limit=10" | python3 -m json.tool || echo "获取导入结果失败"