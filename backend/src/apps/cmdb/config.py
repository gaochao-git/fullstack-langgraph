"""
CMDB 知识图谱配置
定义所有 CI 类型和关系类型
"""

# ==================== CI 类型定义 ====================

CMDB_ENTITY_TYPES = {
    # ========== 物理基础设施层 ==========
    "CMDB_DataCenter": {
        "label": "数据中心/机房",
        "properties": [
            "ci_id",              # 唯一标识
            "name",               # 名称
            "city",               # 城市
            "region",             # 区域（华东/华北/华南）
            "address",            # 地址
            "geo_location",       # 地理坐标
            "area_sqm",           # 面积（平方米）
            "temperature_celsius", # 温度
            "humidity_percent",   # 湿度
            "cabinet_capacity",   # 机柜容量
            "cabinet_used",       # 已用机柜数
            "total_capacity_kw",  # 总电力容量（千瓦）
            "used_capacity_kw",   # 已用电力
            "cooling_type",       # 冷却类型
            "tier_level",         # 数据中心等级（Tier III/IV）
            "operator",           # 运营商
            "contact_person",     # 联系人
            "contact_phone",      # 联系电话
            "access_control",     # 门禁类型
            "fire_suppression",   # 消防系统
            "status",             # 状态（operational/maintenance/offline）
            "environment",        # 环境（production/staging/test）
        ],
        "required": ["ci_id", "name", "city", "status"],
        "indexes": ["ci_id", "name", "city"]
    },

    "CMDB_Cabinet": {
        "label": "机柜",
        "properties": [
            "ci_id",
            "name",
            "datacenter_id",      # 所属数据中心
            "row",                # 行
            "column",             # 列
            "height_u",           # 高度（U）
            "power_capacity_kw",  # 电力容量
            "power_usage_kw",     # 当前用电量
            "network_ports",      # 网络端口数
            "status",
        ],
        "required": ["ci_id", "name", "datacenter_id", "status"],
        "indexes": ["ci_id", "name", "datacenter_id"]
    },

    "CMDB_Rack": {
        "label": "机架",
        "properties": [
            "ci_id",
            "name",
            "cabinet_id",         # 所属机柜
            "position_start_u",   # 起始U位
            "position_end_u",     # 结束U位
            "used_u",             # 已使用U数
            "free_u",             # 剩余U数
            "allocated_to_team",  # 分配给哪个团队
            "status",
        ],
        "required": ["ci_id", "name", "cabinet_id", "status"],
        "indexes": ["ci_id", "name", "cabinet_id"]
    },

    "CMDB_PhysicalServer": {
        "label": "物理服务器",
        "properties": [
            "ci_id",
            "name",
            "cabinet_id",
            "rack_id",
            "asset_number",       # 资产编号
            "serial_number",      # 序列号
            "manufacturer",       # 厂商
            "model",              # 型号
            "cpu_model",          # CPU型号
            "cpu_cores",          # CPU核心数
            "cpu_threads",        # 线程数
            "ram_gb",             # 内存GB
            "disk_type",          # 磁盘类型（SSD/HDD）
            "disk_capacity_tb",   # 磁盘容量TB
            "ip_address",         # IP地址
            "public_ip",          # 公网IP
            "mac_address",        # MAC地址
            "network_bandwidth_gbps", # 网络带宽
            "purchase_date",      # 购买日期
            "warranty_end_date",  # 保修到期日期
            "lease_type",         # 租赁类型（owned/leased）
            "owner_team",         # 责任团队
            "environment",
            "importance",         # 重要性（critical/high/medium/low）
            "status",
            "hypervisor",         # 虚拟化平台（VMware ESXi/KVM）
            "hypervisor_version",
            "vm_count",           # 承载虚拟机数量
            "cpu_usage_percent",  # CPU使用率
            "ram_usage_percent",  # 内存使用率
            "disk_usage_percent", # 磁盘使用率
            "temperature_celsius",
            "last_reboot",        # 最后重启时间
        ],
        "required": ["ci_id", "name", "rack_id", "cpu_cores", "ram_gb", "ip_address", "status"],
        "indexes": ["ci_id", "name", "ip_address", "serial_number"]
    },

    # ========== 虚拟化层 ==========
    "CMDB_VirtualMachine": {
        "label": "虚拟机",
        "properties": [
            "ci_id",
            "name",
            "physical_server_id", # 所属物理服务器
            "vm_id",              # 虚拟机UUID
            "vcpu",               # 虚拟CPU核心数
            "vram_gb",            # 虚拟内存GB
            "vdisk_gb",           # 虚拟磁盘GB
            "os",                 # 操作系统
            "os_version",
            "kernel_version",
            "ip_address",
            "mac_address",
            "hostname",
            "hypervisor_type",
            "cluster_name",
            "datastore",
            "created_date",
            "owner_team",
            "environment",
            "importance",
            "status",             # running/stopped/suspended
            "cpu_usage_percent",
            "ram_usage_percent",
            "disk_usage_percent",
            "network_in_mbps",
            "network_out_mbps",
        ],
        "required": ["ci_id", "name", "physical_server_id", "vcpu", "vram_gb", "ip_address", "status"],
        "indexes": ["ci_id", "name", "ip_address", "vm_id"]
    },

    # ========== 应用服务层 ==========
    "CMDB_Application": {
        "label": "应用程序",
        "properties": [
            "ci_id",
            "name",
            "vm_id",              # 运行的虚拟机
            "app_type",           # 应用类型（FastAPI/Django/Spring Boot）
            "version",
            "git_repo",
            "git_commit",
            "deployment_method",  # 部署方式（systemd/supervisor）
            "service_port",
            "health_endpoint",
            "metrics_endpoint",
            "api_documentation",
            "owner_team",
            "owner_person",
            "on_call_person",
            "environment",
            "importance",
            "sla_target",         # SLA目标（99.9%）
            "status",
            "depends_on",         # 依赖的服务列表
            "health_status",      # healthy/degraded/unhealthy
            "response_time_ms",
            "error_rate_percent",
            "qps",                # 每秒请求数
        ],
        "required": ["ci_id", "name", "vm_id", "app_type", "service_port", "status"],
        "indexes": ["ci_id", "name", "vm_id"]
    },

    "CMDB_Database": {
        "label": "数据库",
        "properties": [
            "ci_id",
            "name",
            "vm_id",
            "db_type",            # PostgreSQL/MySQL/MongoDB
            "version",
            "port",
            "charset",
            "host",
            "connection_string",
            "max_connections",
            "current_connections",
            "data_dir",
            "total_size_gb",
            "used_size_gb",
            "ha_mode",            # standalone/master_slave/cluster
            "replication_role",   # master/slave/none
            "replication_lag_seconds",
            "backup_enabled",
            "backup_schedule",
            "last_backup_time",
            "backup_retention_days",
            "owner_team",
            "environment",
            "importance",
            "status",
            "qps",
            "tps",
            "slow_query_count",
            "cache_hit_rate_percent",
        ],
        "required": ["ci_id", "name", "vm_id", "db_type", "version", "port", "status"],
        "indexes": ["ci_id", "name", "vm_id", "host"]
    },

    "CMDB_MessageQueue": {
        "label": "消息队列",
        "properties": [
            "ci_id",
            "name",
            "mq_type",            # Kafka/RabbitMQ/RocketMQ
            "version",
            "cluster_mode",       # true/false
            "brokers",            # Broker列表
            "broker_count",
            "zookeeper_hosts",
            "topic_count",
            "total_partitions",
            "replication_factor",
            "owner_team",
            "environment",
            "importance",
            "status",
            "messages_in_per_sec",
            "messages_out_per_sec",
            "disk_usage_gb",
        ],
        "required": ["ci_id", "name", "mq_type", "version", "status"],
        "indexes": ["ci_id", "name"]
    },

    "CMDB_Cache": {
        "label": "缓存",
        "properties": [
            "ci_id",
            "name",
            "vm_id",
            "cache_type",         # Redis/Memcached
            "version",
            "port",
            "max_memory_gb",
            "used_memory_gb",
            "eviction_policy",
            "persistence_enabled",
            "persistence_mode",   # AOF/RDB/both
            "ha_mode",            # standalone/sentinel/cluster
            "sentinel_count",
            "master_node",
            "slave_nodes",
            "owner_team",
            "environment",
            "importance",
            "status",
            "ops_per_sec",
            "hit_rate_percent",
            "connected_clients",
        ],
        "required": ["ci_id", "name", "vm_id", "cache_type", "version", "port", "status"],
        "indexes": ["ci_id", "name", "vm_id"]
    },

    # ========== 网络层 ==========
    "CMDB_NetworkDevice": {
        "label": "网络设备",
        "properties": [
            "ci_id",
            "name",
            "device_type",        # core_switch/access_switch/router/firewall
            "manufacturer",
            "model",
            "serial_number",
            "firmware_version",
            "management_ip",
            "total_ports",
            "used_ports",
            "port_speed_gbps",
            "cabinet_id",
            "datacenter_id",
            "vlan_count",
            "vlan_list",
            "owner_team",
            "environment",
            "importance",
            "status",
            "traffic_in_mbps",
            "traffic_out_mbps",
            "packet_loss_percent",
            "error_count",
        ],
        "required": ["ci_id", "name", "device_type", "manufacturer", "model", "status"],
        "indexes": ["ci_id", "name", "management_ip", "serial_number"]
    },

    "CMDB_LoadBalancer": {
        "label": "负载均衡",
        "properties": [
            "ci_id",
            "name",
            "vm_id",
            "lb_type",            # Nginx/HAProxy/F5/ALB
            "version",
            "algorithm",          # round_robin/least_conn/ip_hash
            "listen_port",
            "ssl_enabled",
            "ssl_certificate_expiry",
            "backend_servers",    # 后端服务器列表
            "backend_server_count",
            "healthy_backend_count",
            "owner_team",
            "environment",
            "importance",
            "status",
            "requests_per_sec",
            "active_connections",
            "response_time_ms",
        ],
        "required": ["ci_id", "name", "lb_type", "algorithm", "status"],
        "indexes": ["ci_id", "name", "vm_id"]
    },

    # ========== 监控层 ==========
    "CMDB_MonitoringAgent": {
        "label": "监控代理",
        "properties": [
            "ci_id",
            "name",
            "vm_id",
            "agent_type",         # Prometheus/Zabbix/Datadog
            "version",
            "scrape_interval_seconds",
            "retention_days",
            "storage_size_gb",
            "target_count",
            "active_targets",
            "failed_targets",
            "alertmanager_url",
            "alert_rules_count",
            "active_alerts",
            "owner_team",
            "environment",
            "importance",
            "status",
        ],
        "required": ["ci_id", "name", "agent_type", "version", "status"],
        "indexes": ["ci_id", "name", "vm_id"]
    },
}

# ==================== 关系类型定义 ====================

CMDB_RELATIONSHIP_TYPES = {
    # 1. 物理容器关系
    "CONTAINS": {
        "label": "包含",
        "description": "物理层级的包含关系（机房→机柜→机架→服务器）",
        "allowed_pairs": [
            ("CMDB_DataCenter", "CMDB_Cabinet"),
            ("CMDB_Cabinet", "CMDB_Rack"),
            ("CMDB_Rack", "CMDB_PhysicalServer"),
        ],
        "properties": [
            "row",                # 行号（DataCenter->Cabinet）
            "u_position",         # U位（Rack->Server）
            "created_at",
            "source",             # manual | auto_discovery
        ]
    },

    # 2. 虚拟化关系
    "HOSTS": {
        "label": "宿主",
        "description": "物理服务器宿主虚拟机",
        "allowed_pairs": [
            ("CMDB_PhysicalServer", "CMDB_VirtualMachine"),
        ],
        "properties": [
            "hypervisor",
            "allocated_vcpu",
            "allocated_vram_gb",
            "created_at",
        ]
    },

    # 3. 应用运行关系
    "RUNS_ON": {
        "label": "运行于",
        "description": "应用/数据库运行在虚拟机上",
        "allowed_pairs": [
            ("CMDB_Application", "CMDB_VirtualMachine"),
            ("CMDB_Database", "CMDB_VirtualMachine"),
            ("CMDB_MessageQueue", "CMDB_VirtualMachine"),
            ("CMDB_Cache", "CMDB_VirtualMachine"),
            ("CMDB_LoadBalancer", "CMDB_VirtualMachine"),
            ("CMDB_MonitoringAgent", "CMDB_VirtualMachine"),
        ],
        "properties": [
            "deployment_method",  # systemd | supervisor | manual
            "service_port",
            "install_dir",
            "data_dir",
            "port",
            "created_at",
        ]
    },

    # 4. 应用依赖关系
    "DEPENDS_ON": {
        "label": "依赖于",
        "description": "应用之间的依赖关系",
        "allowed_pairs": [
            ("CMDB_Application", "CMDB_Database"),
            ("CMDB_Application", "CMDB_Cache"),
            ("CMDB_Application", "CMDB_MessageQueue"),
            ("CMDB_Application", "CMDB_Application"),
        ],
        "properties": [
            "importance",         # critical | high | medium | low
            "impact_level",       # high | medium | low
            "port",
            "protocol",           # TCP | UDP | HTTP
            "connection_pool_size",
            "timeout_seconds",
            "cache_strategy",
            "discovered_at",
            "source",
        ]
    },

    # 5. 网络连接关系
    "CONNECTS_TO": {
        "label": "连接到",
        "description": "网络连接关系",
        "allowed_pairs": [
            ("CMDB_PhysicalServer", "CMDB_NetworkDevice"),
            ("CMDB_NetworkDevice", "CMDB_NetworkDevice"),
            ("CMDB_LoadBalancer", "CMDB_Application"),
        ],
        "properties": [
            "port_number",
            "switch_port",
            "vlan",
            "bandwidth_gbps",
            "backend_port",
            "health_check_path",
            "weight",
            "discovered_at",
        ]
    },

    # 6. 数据复制关系
    "REPLICATES_TO": {
        "label": "复制到",
        "description": "主从复制关系",
        "allowed_pairs": [
            ("CMDB_Database", "CMDB_Database"),
            ("CMDB_Cache", "CMDB_Cache"),
        ],
        "properties": [
            "replication_mode",   # sync | async
            "replication_lag_seconds",
            "configured_at",
        ]
    },

    # 7. 故障切换关系
    "FAILS_OVER_TO": {
        "label": "故障切换到",
        "description": "高可用故障切换关系",
        "allowed_pairs": [
            ("CMDB_Database", "CMDB_Database"),
            ("CMDB_LoadBalancer", "CMDB_LoadBalancer"),
        ],
        "properties": [
            "failover_mode",      # automatic | manual
            "vrrp_priority",
            "configured_at",
        ]
    },

    # 8. 监控关系
    "MONITORS": {
        "label": "监控",
        "description": "监控代理监控目标资源",
        "allowed_pairs": [
            ("CMDB_MonitoringAgent", "CMDB_PhysicalServer"),
            ("CMDB_MonitoringAgent", "CMDB_VirtualMachine"),
            ("CMDB_MonitoringAgent", "CMDB_Application"),
            ("CMDB_MonitoringAgent", "CMDB_Database"),
            ("CMDB_MonitoringAgent", "CMDB_NetworkDevice"),
        ],
        "properties": [
            "scrape_interval_seconds",
            "metrics_path",
            "alert_rules",
            "configured_at",
        ]
    },

    # 9. 跨数据中心同步
    "SYNCS_WITH": {
        "label": "同步",
        "description": "数据中心间数据同步",
        "allowed_pairs": [
            ("CMDB_DataCenter", "CMDB_DataCenter"),
        ],
        "properties": [
            "sync_type",          # data_replication | network_link
            "bandwidth_mbps",
            "latency_ms",
            "configured_at",
        ]
    },

    # 10. 灾备关系
    "BACKUP_TO": {
        "label": "备份到",
        "description": "数据备份到另一个数据中心",
        "allowed_pairs": [
            ("CMDB_Application", "CMDB_DataCenter"),
            ("CMDB_Database", "CMDB_DataCenter"),
        ],
        "properties": [
            "backup_frequency",   # daily | weekly | monthly
            "backup_location",
            "retention_days",
            "last_backup_time",
            "configured_at",
        ]
    },
}

# ==================== 枚举值定义 ====================

CMDB_ENUMS = {
    "status": ["operational", "maintenance", "offline", "decommissioned"],
    "environment": ["production", "staging", "test", "development"],
    "importance": ["critical", "high", "medium", "low"],
    "vm_status": ["running", "stopped", "suspended"],
    "app_status": ["running", "stopped", "failed", "deploying"],
    "health_status": ["healthy", "degraded", "unhealthy"],
    "deployment_method": ["systemd", "supervisor", "manual"],
    "hypervisor": ["VMware ESXi", "KVM", "Hyper-V"],
    "db_type": ["PostgreSQL", "MySQL", "MongoDB", "Oracle", "SQL Server"],
    "cache_type": ["Redis", "Memcached"],
    "mq_type": ["Kafka", "RabbitMQ", "RocketMQ", "ActiveMQ"],
    "network_device_type": ["core_switch", "access_switch", "router", "firewall"],
    "lb_type": ["Nginx", "HAProxy", "F5", "ALB"],
    "lb_algorithm": ["round_robin", "least_conn", "ip_hash", "url_hash"],
    "monitoring_agent_type": ["Prometheus", "Zabbix", "Datadog", "Grafana Agent"],
    "replication_mode": ["sync", "async"],
    "failover_mode": ["automatic", "manual"],
    "ha_mode": ["standalone", "master_slave", "cluster", "sentinel"],
}
