"""
Elasticsearch工具 - 使用LangChain工具框架
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch
import logging
from langchain.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

def _create_es_client():
    """创建新的Elasticsearch客户端，每次调用都重新连接"""
    # 默认配置，按优先级排序
    default_configs = [
        {"hosts": ["82.156.146.51:9200"]},
        {"hosts": ["http://82.156.146.51:9200"]},
        {"hosts": ["82.156.146.51:9200"], "username": "elastic", "password": "changeme"}
    ]
    
    for config in default_configs:
        try:
            if "username" in config and "password" in config:
                es_client = Elasticsearch(
                    hosts=config["hosts"],
                    basic_auth=(config["username"], config["password"]),
                    verify_certs=False
                )
            else:
                es_client = Elasticsearch(hosts=config["hosts"])
            
            # 测试连接
            info = es_client.info()
            logger.info(f"Elasticsearch连接成功，版本: {info['version']['number']}")
            return es_client
            
        except Exception as e:
            logger.debug(f"尝试配置 {config['hosts']} 失败: {e}")
            continue
    
    raise Exception("无法建立Elasticsearch连接，请检查ES服务状态和配置")

class ErrorLogSearchInput(BaseModel):
    """错误日志搜索输入参数"""
    index_pattern: str = Field(default="logstash-*", description="索引模式")
    error_keywords: Optional[List[str]] = Field(default=None, description="错误关键词列表")
    time_range_hours: int = Field(default=24, description="时间范围(小时)")
    size: int = Field(default=100, description="返回结果数量")

@tool("search_error_logs", args_schema=ErrorLogSearchInput)
def search_error_logs(
    index_pattern: str = "logstash-*",
    error_keywords: Optional[List[str]] = None,
    time_range_hours: int = 24,
    size: int = 100
) -> str:
    """搜索错误日志。用于查找系统中的错误和异常信息。
    
    Args:
        index_pattern: Elasticsearch索引模式，默认为logstash-*
        error_keywords: 要搜索的错误关键词列表
        time_range_hours: 搜索时间范围(小时)，默认24小时
        size: 返回结果数量，默认100条
    
    Returns:
        包含错误日志的JSON字符串
    """
    if not _ensure_es_connection():
        return json.dumps({"error": "无法连接到Elasticsearch，请检查服务状态"})
    
    try:
        # 构建时间范围查询
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        # 构建查询条件
        query = {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat()
                            }
                        }
                    }
                ],
                "should": []
            }
        }
        
        # 添加错误关键词查询
        if error_keywords:
            for keyword in error_keywords:
                query["bool"]["should"].extend([
                    {"match": {"message": keyword}},
                    {"match": {"level": "ERROR"}},
                    {"match": {"level": "FATAL"}},
                    {"wildcard": {"message": f"*{keyword}*"}}
                ])
        else:
            # 默认查询错误级别日志
            query["bool"]["should"].extend([
                {"match": {"level": "ERROR"}},
                {"match": {"level": "FATAL"}},
                {"match": {"level": "CRITICAL"}}
            ])
        
        # 执行搜索
        response = es_client.search(
            index=index_pattern,
            body={
                "query": query,
                "sort": [{"@timestamp": {"order": "desc"}}],
                "size": size,
                "_source": ["@timestamp", "level", "message", "host", "service", "stack_trace"]
            }
        )
        
        # 处理结果
        hits = response.get("hits", {}).get("hits", [])
        results = []
        
        for hit in hits:
            source = hit["_source"]
            results.append({
                "timestamp": source.get("@timestamp"),
                "level": source.get("level"),
                "message": source.get("message", ""),
                "host": source.get("host"),
                "service": source.get("service"),
                "stack_trace": source.get("stack_trace")
            })
        
        return json.dumps({
            "total": response.get("hits", {}).get("total", {}).get("value", 0),
            "logs": results,
            "time_range": f"{start_time.isoformat()} to {end_time.isoformat()}"
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error searching logs: {e}")
        return json.dumps({"error": f"Failed to search logs: {str(e)}"})
    finally:
        if es_client:
            es_client.close()

class LogPatternAnalysisInput(BaseModel):
    """日志模式分析输入参数"""
    index_pattern: str = Field(default="logstash-*", description="索引模式")
    time_range_hours: int = Field(default=24, description="时间范围(小时)")

@tool("analyze_log_patterns", args_schema=LogPatternAnalysisInput)
def analyze_log_patterns(
    index_pattern: str = "logstash-*",
    time_range_hours: int = 24
) -> str:
    """分析日志模式和频率。用于识别系统中的错误趋势和热点问题。
    
    Args:
        index_pattern: Elasticsearch索引模式
        time_range_hours: 分析时间范围(小时)
    
    Returns:
        包含日志分析结果的JSON字符串
    """
    if not _ensure_es_connection():
        return json.dumps({"error": "无法连接到Elasticsearch，请检查服务状态"})
    
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        # 聚合查询：按错误类型分组
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": end_time.isoformat()
                                }
                            }
                        },
                        {
                            "terms": {
                                "level": ["ERROR", "FATAL", "CRITICAL"]
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "error_by_service": {
                    "terms": {
                        "field": "service.keyword",
                        "size": 10
                    }
                },
                "error_by_host": {
                    "terms": {
                        "field": "host.keyword",
                        "size": 10
                    }
                },
                "errors_over_time": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "interval": "1h"
                    }
                }
            }
        }
        
        response = _es_client.search(
            index=index_pattern,
            body=query,
            size=0
        )
        
        aggregations = response.get("aggregations", {})
        
        return json.dumps({
            "total_errors": response.get("hits", {}).get("total", {}).get("value", 0),
            "errors_by_service": [
                {"service": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggregations.get("error_by_service", {}).get("buckets", [])
            ],
            "errors_by_host": [
                {"host": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggregations.get("error_by_host", {}).get("buckets", [])
            ],
            "errors_timeline": [
                {
                    "timestamp": bucket["key_as_string"],
                    "count": bucket["doc_count"]
                }
                for bucket in aggregations.get("errors_over_time", {}).get("buckets", [])
            ]
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error analyzing log patterns: {e}")
        return json.dumps({"error": f"Failed to analyze log patterns: {str(e)}"})

class CorrelationSearchInput(BaseModel):
    """关联搜索输入参数"""
    correlation_id: str = Field(description="关联ID，如trace_id、request_id等")
    index_pattern: str = Field(default="logstash-*", description="索引模式")
    time_range_hours: int = Field(default=24, description="时间范围(小时)")

@tool("search_by_correlation_id", args_schema=CorrelationSearchInput)
def search_by_correlation_id(
    correlation_id: str,
    index_pattern: str = "logstash-*",
    time_range_hours: int = 24
) -> str:
    """根据关联ID搜索相关日志。用于追踪特定请求或事务的完整调用链。
    
    Args:
        correlation_id: 关联ID，如trace_id、request_id等
        index_pattern: Elasticsearch索引模式
        time_range_hours: 搜索时间范围(小时)
    
    Returns:
        包含相关日志的JSON字符串
    """
    if not _ensure_es_connection():
        return json.dumps({"error": "无法连接到Elasticsearch，请检查服务状态"})
    
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        query = {
            "bool": {
                "must": [
                    {
                        "range": {
                            "@timestamp": {
                                "gte": start_time.isoformat(),
                                "lte": end_time.isoformat()
                            }
                        }
                    },
                    {
                        "multi_match": {
                            "query": correlation_id,
                            "fields": ["correlation_id", "trace_id", "request_id", "session_id", "message"]
                        }
                    }
                ]
            }
        }
        
        response = _es_client.search(
            index=index_pattern,
            body={
                "query": query,
                "sort": [{"@timestamp": {"order": "asc"}}],
                "size": 1000
            }
        )
        
        hits = response.get("hits", {}).get("hits", [])
        logs = []
        
        for hit in hits:
            source = hit["_source"]
            logs.append({
                "timestamp": source.get("@timestamp"),
                "level": source.get("level"),
                "service": source.get("service"),
                "host": source.get("host"),
                "message": source.get("message", "")
            })
        
        return json.dumps({
            "correlation_id": correlation_id,
            "total": len(logs),
            "logs": logs
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error searching by correlation ID: {e}")
        return json.dumps({"error": f"Failed to search by correlation ID: {str(e)}"})

class ServiceHealthInput(BaseModel):
    """服务健康检查输入参数"""
    services: Optional[List[str]] = Field(default=None, description="服务名称列表")
    time_range_hours: int = Field(default=1, description="时间范围(小时)")

@tool("get_service_health_summary", args_schema=ServiceHealthInput)
def get_service_health_summary(
    services: Optional[List[str]] = None,
    time_range_hours: int = 1
) -> str:
    """获取服务健康状况摘要。用于快速了解各服务的运行状态。
    
    Args:
        services: 要检查的服务名称列表，None表示检查所有服务
        time_range_hours: 检查时间范围(小时)
    
    Returns:
        包含服务健康状况的JSON字符串
    """
    if not _ensure_es_connection():
        return json.dumps({"error": "无法连接到Elasticsearch，请检查服务状态"})
    
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        query_filter = [
            {
                "range": {
                    "@timestamp": {
                        "gte": start_time.isoformat(),
                        "lte": end_time.isoformat()
                    }
                }
            }
        ]
        
        if services:
            query_filter.append({
                "terms": {
                    "service.keyword": services
                }
            })
        
        query = {
            "query": {
                "bool": {
                    "must": query_filter
                }
            },
            "aggs": {
                "services": {
                    "terms": {
                        "field": "service.keyword",
                        "size": 20
                    },
                    "aggs": {
                        "levels": {
                            "terms": {
                                "field": "level.keyword"
                            }
                        }
                    }
                }
            }
        }
        
        response = _es_client.search(
            index="logstash-*",
            body=query,
            size=0
        )
        
        services_data = []
        for bucket in response.get("aggregations", {}).get("services", {}).get("buckets", []):
            service_name = bucket["key"]
            total_logs = bucket["doc_count"]
            
            level_counts = {}
            for level_bucket in bucket.get("levels", {}).get("buckets", []):
                level_counts[level_bucket["key"]] = level_bucket["doc_count"]
            
            error_count = sum(level_counts.get(level, 0) for level in ["ERROR", "FATAL", "CRITICAL"])
            warning_count = level_counts.get("WARN", 0) + level_counts.get("WARNING", 0)
            info_count = level_counts.get("INFO", 0)
            
            health_score = max(0, 100 - (error_count * 10 + warning_count * 2))
            
            services_data.append({
                "service": service_name,
                "total_logs": total_logs,
                "error_count": error_count,
                "warning_count": warning_count,
                "info_count": info_count,
                "health_score": health_score,
                "status": "healthy" if health_score > 80 else "warning" if health_score > 50 else "critical"
            })
        
        return json.dumps({
            "time_range": f"Last {time_range_hours} hour(s)",
            "services": services_data
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting service health summary: {e}")
        return json.dumps({"error": f"Failed to get service health summary: {str(e)}"})

class CustomQueryInput(BaseModel):
    """自定义查询输入参数"""
    index_name: str = Field(description="索引名称")
    start_time: str = Field(description="开始时间 (ISO格式)")
    end_time: str = Field(description="结束时间 (ISO格式)")
    query_body: Optional[Dict[str, Any]] = Field(default=None, description="查询体，如果为空则由AI生成")

@tool("custom_elasticsearch_query", args_schema=CustomQueryInput)
def custom_elasticsearch_query(
    index_name: str,
    start_time: str,
    end_time: str,
    query_body: Optional[Dict[str, Any]] = None
) -> str:
    """执行自定义Elasticsearch查询。支持指定索引名、时间范围和查询体。
    
    Args:
        index_name: 索引名称
        start_time: 开始时间 (ISO格式)
        end_time: 结束时间 (ISO格式)
        query_body: 自定义查询体，如果为空则生成默认查询
    
    Returns:
        包含查询结果的JSON字符串
    """
    try:
        es_client = _create_es_client()
        
        # 如果没有提供查询体，使用默认查询
        if not query_body:
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": start_time,
                                        "lte": end_time
                                    }
                                }
                            }
                        ]
                    }
                },
                "sort": [{"@timestamp": {"order": "desc"}}],
                "size": 100
            }
        
        # 确保查询体包含时间范围
        if "query" not in query_body:
            query_body["query"] = {"bool": {"must": []}}
        
        if "bool" not in query_body["query"]:
            query_body["query"]["bool"] = {"must": []}
        
        if "must" not in query_body["query"]["bool"]:
            query_body["query"]["bool"]["must"] = []
        
        # 添加时间范围过滤
        time_filter = {
            "range": {
                "@timestamp": {
                    "gte": start_time,
                    "lte": end_time
                }
            }
        }
        
        query_body["query"]["bool"]["must"].append(time_filter)
        
        # 执行查询
        response = es_client.search(
            index=index_name,
            body=query_body
        )
        
        # 处理结果
        hits = response.get("hits", {}).get("hits", [])
        results = []
        
        for hit in hits:
            results.append({
                "timestamp": hit["_source"].get("@timestamp"),
                "source": hit["_source"]
            })
        
        return json.dumps({
            "total": response.get("hits", {}).get("total", {}).get("value", 0),
            "time_range": f"{start_time} to {end_time}",
            "results": results
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error executing custom query: {e}")
        return json.dumps({"error": f"Failed to execute custom query: {str(e)}"})
    finally:
        if 'es_client' in locals():
            es_client.close()

# 重命名工具以匹配SOP配置
get_es_data = custom_elasticsearch_query

class IndicesListInput(BaseModel):
    """获取所有索引输入参数"""
    pass

@tool("get_es_indices", args_schema=IndicesListInput)
def get_es_indices() -> str:
    """获取Elasticsearch所有索引列表。用于查看可用的索引。
    
    Returns:
        包含索引列表的JSON字符串
    """
    try:
        es_client = _create_es_client()
        
        # 获取所有索引
        indices = es_client.cat.indices(format="json")
        
        # 格式化索引信息
        index_data = []
        for index in indices:
            index_data.append({
                "index": index["index"],
                "status": index["status"], 
                "health": index["health"],
                "docs_count": index.get("docs.count", "0"),
                "store_size": index.get("store.size", "0b")
            })
        
        # 按索引名称排序
        index_data.sort(key=lambda x: x["index"])
        
        return json.dumps({
            "total_indices": len(index_data),
            "indices": index_data
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting ES indices: {e}")
        return json.dumps({"error": f"Failed to get ES indices: {str(e)}"})
    finally:
        if 'es_client' in locals():
            es_client.close()

# 导出所有工具
elasticsearch_tools = [
    get_es_data,
    get_es_indices
] 