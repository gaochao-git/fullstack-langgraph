"""
Elasticsearch工具 - 使用requests直接调用ES REST API
"""

import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from langchain.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ES服务器配置
ES_BASE_URL = "http://82.156.146.51:9200"
ES_TIMEOUT = 30

def _es_request(method: str, endpoint: str, data: Dict = None, params: Dict = None) -> Dict:
    """执行ES REST API请求"""
    url = f"{ES_BASE_URL}/{endpoint.lstrip('/')}"
    headers = {"Content-Type": "application/json"}
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, headers=headers, timeout=ES_TIMEOUT)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, params=params, headers=headers, timeout=ES_TIMEOUT)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"ES请求失败: {e}")
        raise Exception(f"ES请求失败: {str(e)}")

def _test_es_connection() -> bool:
    """测试ES连接"""
    try:
        info = _es_request("GET", "/")
        logger.info(f"Elasticsearch连接成功，版本: {info['version']['number']}")
        return True
    except Exception as e:
        logger.error(f"ES连接测试失败: {e}")
        return False

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
        # 智能时区处理
        def convert_time_with_fallback(time_str):
            """智能时区转换，支持多种格式并提供回退方案"""
            if "+" not in time_str and "Z" not in time_str and "T" in time_str:
                # 没有时区信息，添加中国时区
                return time_str + "+08:00"
            elif time_str.endswith("Z"):
                # UTC时间，先尝试直接使用，后续如果无结果会尝试转换
                return time_str
            else:
                # 已有时区信息，直接使用
                return time_str
        
        start_time_with_tz = convert_time_with_fallback(start_time)
        end_time_with_tz = convert_time_with_fallback(end_time)
        
        # 如果没有提供查询体，使用默认查询（直接使用处理后的时间）
        if not query_body:
            query_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "range": {
                                    "@timestamp": {
                                        "gte": start_time_with_tz,
                                        "lte": end_time_with_tz
                                    }
                                }
                            }
                        ]
                    }
                },
                "sort": [{"@timestamp": {"order": "desc"}}],
                "size": 100
            }
        else:
            # 确保查询体包含时间范围
            if "query" not in query_body:
                query_body["query"] = {"bool": {"must": []}}
            
            if "bool" not in query_body["query"]:
                query_body["query"]["bool"] = {"must": []}
            
            if "must" not in query_body["query"]["bool"]:
                query_body["query"]["bool"]["must"] = []
            
            # 检查是否已存在@timestamp的range查询，如果存在则更新，否则添加
            timestamp_filter_found = False
            for i, condition in enumerate(query_body["query"]["bool"]["must"]):
                if isinstance(condition, dict) and "range" in condition and "@timestamp" in condition["range"]:
                    # 更新现有的时间过滤器
                    query_body["query"]["bool"]["must"][i] = {
                        "range": {
                            "@timestamp": {
                                "gte": start_time_with_tz,
                                "lte": end_time_with_tz
                            }
                        }
                    }
                    timestamp_filter_found = True
                    break
            
            # 如果没有找到时间过滤器，则添加新的
            if not timestamp_filter_found:
                time_filter = {
                    "range": {
                        "@timestamp": {
                            "gte": start_time_with_tz,
                            "lte": end_time_with_tz
                        }
                    }
                }
                query_body["query"]["bool"]["must"].append(time_filter)
        
        # 打印查询体用于调试
        logger.info(f"ES查询体: {json.dumps(query_body, indent=2)}")
        print(f"ES查询体: {json.dumps(query_body, indent=2)}")
        
        # 执行查询
        response = _es_request("POST", f"/{index_name}/_search", data=query_body)
        
        # 检查结果，如果是UTC时间且没有结果，尝试转换时区
        total_hits = response.get("hits", {}).get("total", {}).get("value", 0)
        
        if total_hits == 0 and (start_time.endswith("Z") or end_time.endswith("Z")):
            logger.info("UTC查询无结果，尝试转换为中国时区查询")
            print("UTC查询无结果，尝试转换为中国时区查询")
            
            # 将UTC时间转换为中国时区（减8小时，因为UTC+8小时=中国时间）
            from datetime import datetime, timedelta
            try:
                if start_time.endswith("Z"):
                    start_dt = datetime.fromisoformat(start_time[:-1])  # 移除Z
                    start_dt_china = start_dt - timedelta(hours=8)  # UTC转中国时间需要减8小时
                    start_time_china = start_dt_china.isoformat() + "+08:00"
                else:
                    start_time_china = start_time_with_tz
                    
                if end_time.endswith("Z"):
                    end_dt = datetime.fromisoformat(end_time[:-1])  # 移除Z
                    end_dt_china = end_dt - timedelta(hours=8)  # UTC转中国时间需要减8小时
                    end_time_china = end_dt_china.isoformat() + "+08:00"
                else:
                    end_time_china = end_time_with_tz
                
                # 更新查询体中的时间
                if not query_body:
                    query_body = {
                        "query": {
                            "bool": {
                                "must": [
                                    {
                                        "range": {
                                            "@timestamp": {
                                                "gte": start_time_china,
                                                "lte": end_time_china
                                            }
                                        }
                                    }
                                ]
                            }
                        },
                        "sort": [{"@timestamp": {"order": "desc"}}],
                        "size": 100
                    }
                else:
                    # 更新现有查询体中的时间过滤器
                    for condition in query_body["query"]["bool"]["must"]:
                        if isinstance(condition, dict) and "range" in condition and "@timestamp" in condition["range"]:
                            condition["range"]["@timestamp"]["gte"] = start_time_china
                            condition["range"]["@timestamp"]["lte"] = end_time_china
                            break
                
                # 重新执行查询
                logger.info(f"转换后的查询体: {json.dumps(query_body, indent=2)}")
                print(f"转换后的查询体: {json.dumps(query_body, indent=2)}")
                response = _es_request("POST", f"/{index_name}/_search", data=query_body)
                
                # 更新显示的时间范围
                start_time_with_tz = start_time_china
                end_time_with_tz = end_time_china
                
            except Exception as conv_error:
                logger.error(f"时区转换失败: {conv_error}")
        
        # 处理结果
        hits = response.get("hits", {}).get("hits", [])
        results = []
        
        for hit in hits:
            results.append({
                "timestamp": hit["_source"].get("@timestamp"),
                "source": hit["_source"]
            })
        
        final_total = response.get("hits", {}).get("total", {}).get("value", 0)
        return json.dumps({
            "total": final_total,
            "time_range": f"{start_time_with_tz} to {end_time_with_tz}",
            "original_time_range": f"{start_time} to {end_time}",
            "timezone_converted": total_hits == 0 and final_total > 0,
            "results": results
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error executing custom query: {e}")
        return json.dumps({"error": f"Failed to execute custom query: {str(e)}"})

# 重命名工具以匹配SOP配置
get_es_data = custom_elasticsearch_query

class TrendsDataInput(BaseModel):
    """获取趋势数据输入参数"""
    index_name: str = Field(description="索引名称")
    start_time: str = Field(description="开始时间 (ISO格式)")
    end_time: str = Field(description="结束时间 (ISO格式)")
    field: str = Field(description="用于统计趋势的字段")
    interval: str = Field(default="1h", description="时间间隔，如: 1m, 5m, 1h, 1d")

@tool("get_es_trends_data", args_schema=TrendsDataInput)
def get_es_trends_data(
    index_name: str,
    start_time: str,
    end_time: str,
    field: str,
    interval: str = "1h"
) -> str:
    """获取ES趋势数据。用于分析指定时间范围内数据的趋势变化。
    
    Args:
        index_name: 索引名称
        start_time: 开始时间 (ISO格式)
        end_time: 结束时间 (ISO格式)
        field: 用于统计趋势的字段
        interval: 时间间隔，如: 1m, 5m, 1h, 1d
    
    Returns:
        包含趋势数据的JSON字符串
    """
    try:
        # 测试连接
        _test_es_connection()
        
        # 构建趋势聚合查询
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
            "aggs": {
                "trends": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "interval": interval,
                        "format": "yyyy-MM-dd HH:mm:ss"
                    },
                    "aggs": {
                        "value_stats": {
                            "stats": {
                                "field": field
                            }
                        },
                        "doc_count": {
                            "value_count": {
                                "field": field
                            }
                        }
                    }
                }
            },
            "size": 0
        }
        
        # 执行查询
        response = _es_request("POST", f"/{index_name}/_search", data=query_body)
        
        # 处理聚合结果
        buckets = response.get("aggregations", {}).get("trends", {}).get("buckets", [])
        trends_data = []
        
        for bucket in buckets:
            stats = bucket.get("value_stats", {})
            trends_data.append({
                "timestamp": bucket["key_as_string"],
                "doc_count": bucket["doc_count"],
                "value_count": bucket.get("doc_count", {}).get("value", 0),
                "avg": stats.get("avg"),
                "min": stats.get("min"),
                "max": stats.get("max"),
                "sum": stats.get("sum")
            })
        
        return json.dumps({
            "index": index_name,
            "time_range": f"{start_time} to {end_time}",
            "field": field,
            "interval": interval,
            "total_buckets": len(trends_data),
            "trends": trends_data
        }, indent=2)
        
    except Exception as e:
        logger.error(f"Error getting ES trends data: {e}")
        return json.dumps({"error": f"Failed to get ES trends data: {str(e)}"})

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
        # 获取所有索引
        indices = _es_request("GET", "/_cat/indices", params={"format": "json"})
        
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

# 导出所有工具
elasticsearch_tools = [
    get_es_data,
    get_es_indices,
    get_es_trends_data
]