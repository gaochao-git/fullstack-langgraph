"""
IDC运行分析/监控相关API（供前端 idc_research 页面使用）
注意：当前均为后端Mock数据，后续可替换为真实数据源。
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.config import get_async_db
from src.shared.schemas.response import success_response, UnifiedResponse
from src.apps.auth.dependencies import get_current_user

router = APIRouter()


# =============== 基础Mock生成器 ===============

def _gen_perf_history(hours: int = 24) -> List[Dict[str, Any]]:
    now = datetime.now()
    out = []
    for i in range(hours - 1, -1, -1):
        ts = now - timedelta(hours=i)
        out.append({
            "timestamp": ts.isoformat(),
            "cpu": int(30 + (i * 7 % 40)),
            "memory": int(50 + (i * 5 % 30)),
            "network": int(20 + (i * 3 % 60)),
            "temperature": int(45 + (i % 10)),
        })
    return out


# =============== IDC 概览数据 ===============

_IDCS: List[Dict[str, Any]] = [
    {
        "id": "idc-beijing-001",
        "name": "北京数据中心",
        "location": "北京市海淀区",
        "serverCount": 1250,
        "cpuUsage": 65,
        "memoryUsage": 72,
        "networkLoad": 45,
        "stabilityScore": 98.5,
        "powerUsage": 850,
        "temperature": 22,
        "uptime": 99.9,
        "status": "healthy",
        "lastUpdated": datetime.now().isoformat(),
        "performanceHistory": _gen_perf_history(),
    },
    {
        "id": "idc-shanghai-001",
        "name": "上海数据中心",
        "location": "上海市浦东新区",
        "serverCount": 980,
        "cpuUsage": 58,
        "memoryUsage": 68,
        "networkLoad": 52,
        "stabilityScore": 97.8,
        "powerUsage": 720,
        "temperature": 24,
        "uptime": 99.7,
        "status": "healthy",
        "lastUpdated": datetime.now().isoformat(),
        "performanceHistory": _gen_perf_history(),
    },
    {
        "id": "idc-guangzhou-001",
        "name": "广州数据中心",
        "location": "广州市天河区",
        "serverCount": 760,
        "cpuUsage": 78,
        "memoryUsage": 85,
        "networkLoad": 71,
        "stabilityScore": 95.2,
        "powerUsage": 640,
        "temperature": 26,
        "uptime": 99.2,
        "status": "warning",
        "lastUpdated": datetime.now().isoformat(),
        "performanceHistory": _gen_perf_history(),
    },
    {
        "id": "idc-shenzhen-001",
        "name": "深圳数据中心",
        "location": "深圳市南山区",
        "serverCount": 1120,
        "cpuUsage": 42,
        "memoryUsage": 55,
        "networkLoad": 38,
        "stabilityScore": 99.1,
        "powerUsage": 780,
        "temperature": 21,
        "uptime": 99.8,
        "status": "healthy",
        "lastUpdated": datetime.now().isoformat(),
        "performanceHistory": _gen_perf_history(),
    },
    {
        "id": "idc-chengdu-001",
        "name": "成都数据中心",
        "location": "成都市高新区",
        "serverCount": 650,
        "cpuUsage": 88,
        "memoryUsage": 92,
        "networkLoad": 89,
        "stabilityScore": 89.5,
        "powerUsage": 580,
        "temperature": 28,
        "uptime": 98.1,
        "status": "critical",
        "lastUpdated": datetime.now().isoformat(),
        "performanceHistory": _gen_perf_history(),
    },
]


@router.get("/idcs", response_model=UnifiedResponse)
async def list_idcs(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    return success_response(_IDCS, msg="获取IDC列表成功")


@router.get("/overview/stats", response_model=UnifiedResponse)
async def overview_stats(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    total_servers = sum(i["serverCount"] for i in _IDCS)
    avg_cpu = round(sum(i["cpuUsage"] for i in _IDCS) / len(_IDCS))
    avg_stability = round(sum(i["stabilityScore"] for i in _IDCS) / len(_IDCS), 1)
    healthy = len([i for i in _IDCS if i["status"] == "healthy"])
    return success_response({
        "totalServers": total_servers,
        "avgCpuUsage": avg_cpu,
        "avgStability": avg_stability,
        "healthyCount": healthy,
    }, msg="获取概览统计成功")


# =============== 应用与业务监控 ===============

_APPLICATIONS: List[Dict[str, Any]] = [
    {
        "id": "app-payment",
        "name": "支付系统",
        "businessType": "支付业务",
        "version": "2.3.1",
        "deployedIDCs": [i["id"] for i in _IDCS[:4]],
        "isShared": True,
        "status": "healthy",
        "services": [
            {
                "id": "payment-app-bj",
                "name": "支付应用服务器",
                "type": "app",
                "idcId": "idc-beijing-001",
                "instances": 8,
                "metrics": {
                    "cpuUsage": 45,
                    "memoryUsage": 55,
                    "diskUsage": 40,
                    "networkIO": 60,
                    "responseTime": 120,
                    "throughput": 1200,
                    "errorRate": 0.8,
                    "availability": 99.6,
                    "connections": 600,
                },
                "dependencies": ["payment-db-bj", "payment-cache-bj"],
            },
            {
                "id": "payment-db-bj",
                "name": "支付数据库",
                "type": "database",
                "idcId": "idc-beijing-001",
                "instances": 3,
                "metrics": {
                    "cpuUsage": 58,
                    "memoryUsage": 70,
                    "diskUsage": 60,
                    "networkIO": 40,
                    "responseTime": 80,
                    "throughput": 600,
                    "errorRate": 0.4,
                    "availability": 99.7,
                    "connections": 300,
                },
                "dependencies": [],
            },
            {
                "id": "payment-gw-sh",
                "name": "API网关",
                "type": "gateway",
                "idcId": "idc-shanghai-001",
                "instances": 4,
                "metrics": {"cpuUsage": 35, "memoryUsage": 40, "diskUsage": 30, "networkIO": 75, "responseTime": 60, "throughput": 2000, "errorRate": 0.5, "availability": 99.8, "connections": 800},
                "dependencies": [],
            },
        ],
    },
    {
        "id": "app-risk",
        "name": "风控引擎",
        "businessType": "风险控制",
        "version": "1.8.0",
        "deployedIDCs": ["idc-beijing-001", "idc-shenzhen-001"],
        "isShared": False,
        "status": "warning",
        "services": [
            {
                "id": "risk-app-sz",
                "name": "风控服务",
                "type": "app",
                "idcId": "idc-shenzhen-001",
                "instances": 5,
                "metrics": {
                    "cpuUsage": 60,
                    "memoryUsage": 68,
                    "diskUsage": 50,
                    "networkIO": 45,
                    "responseTime": 150,
                    "throughput": 800,
                    "errorRate": 1.2,
                    "availability": 99.2,
                    "connections": 420,
                },
                "dependencies": ["risk-db-sz"],
            },
            {
                "id": "risk-db-sz",
                "name": "风控数据库",
                "type": "database",
                "idcId": "idc-shenzhen-001",
                "instances": 2,
                "metrics": {"cpuUsage": 55, "memoryUsage": 62, "diskUsage": 60, "networkIO": 30, "responseTime": 110, "throughput": 500, "errorRate": 0.6, "availability": 99.5, "connections": 260},
                "dependencies": [],
            },
        ],
    },
    {
        "id": "app-data-analytics",
        "name": "数据分析平台",
        "businessType": "数据分析",
        "version": "3.1.0",
        "deployedIDCs": ["idc-shanghai-001", "idc-guangzhou-001"],
        "isShared": True,
        "status": "healthy",
        "services": [
            {"id": "da-app-sh", "name": "分析计算", "type": "app", "idcId": "idc-shanghai-001", "instances": 6, "metrics": {"cpuUsage": 50, "memoryUsage": 65, "diskUsage": 70, "networkIO": 40, "responseTime": 140, "throughput": 900, "errorRate": 0.7, "availability": 99.6, "connections": 350}, "dependencies": []},
            {"id": "da-db-gz", "name": "数据仓库", "type": "database", "idcId": "idc-guangzhou-001", "instances": 3, "metrics": {"cpuUsage": 48, "memoryUsage": 60, "diskUsage": 80, "networkIO": 35, "responseTime": 100, "throughput": 700, "errorRate": 0.5, "availability": 99.7, "connections": 220}, "dependencies": []},
        ],
    },
]


@router.get("/applications", response_model=UnifiedResponse)
async def list_applications(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    return success_response(_APPLICATIONS, msg="获取应用列表成功")


@router.get("/applications/business-types", response_model=UnifiedResponse)
async def list_business_types(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    types = sorted(list({app["businessType"] for app in _APPLICATIONS}))
    # UnifiedResponse 要求 data 为 dict 或 list[dict]
    return success_response({"items": types}, msg="获取业务类型成功")


# =============== 国产替代监控（硬件） ===============

def _gen_products() -> List[Dict[str, Any]]:
    products: List[Dict[str, Any]] = []
    idcs = ["idc-beijing-001", "idc-shanghai-001", "idc-guangzhou-001", "idc-shenzhen-001", "idc-chengdu-001"]
    categories = {
        "server": {"domestic": ["华为", "浪潮", "联想", "曙光"], "imported": ["Dell", "HPE", "IBM"]},
        "network": {"domestic": ["华为", "中兴", "锐捷"], "imported": ["Cisco", "Juniper", "Arista"]},
        "storage": {"domestic": ["华为", "海康威视", "同有科技"], "imported": ["NetApp", "Dell EMC", "HPE"]},
        "os": {"domestic": ["统信", "麒麟", "中科方德"], "imported": ["RedHat", "SUSE", "Ubuntu"]},
        "database": {"domestic": ["达梦", "人大金仓", "南大通用"], "imported": ["Oracle", "Microsoft", "IBM"]},
        "middleware": {"domestic": ["东方通", "金蝶", "宝兰德"], "imported": ["IBM", "Oracle", "Red Hat"]},
        "security": {"domestic": ["奇安信", "绿盟", "启明星辰"], "imported": ["Palo Alto", "Fortinet", "Check Point"]},
    }

    def add_product(cat: str, brand: str, is_dom: bool, idc: str, base_q: int):
        products.append({
            "id": f"{cat}-{brand}-{idc}",
            "category": cat,
            "name": f"{brand} {cat}",
            "brand": brand,
            "isDomestic": is_dom,
            "model": "V1",
            "quantity": base_q,
            "idcId": idc,
            "installDate": (datetime.now() - timedelta(days=400)).date().isoformat(),
            "warrantyEndDate": (datetime.now() + timedelta(days=400)).date().isoformat(),
            "status": "normal",
            "failureCount": 1 if is_dom else 2,
            "mtbf": 7600 if is_dom else 8200,
        })

    for idc in idcs:
        for cat, brands in categories.items():
            for b in brands["domestic"]:
                add_product(cat, b, True, idc, 10 if cat == "server" else 6)
            for b in brands["imported"]:
                add_product(cat, b, False, idc, 8 if cat == "server" else 4)
    return products

_HARDWARE_PRODUCTS: List[Dict[str, Any]] = _gen_products()


@router.get("/hardware/products", response_model=UnifiedResponse)
async def list_hardware_products(
    category: str = Query(None, description="按类别过滤，如 server/network/os 等"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    items = _HARDWARE_PRODUCTS
    if category:
        items = [p for p in items if p.get("category") == category]
    return success_response(items, msg="获取硬件产品成功")


@router.get("/hardware/metrics", response_model=UnifiedResponse)
async def substitution_metrics(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    # 简易聚合
    categories = sorted(list({p["category"] for p in _HARDWARE_PRODUCTS}))
    metrics: List[Dict[str, Any]] = []
    for c in categories:
        products = [p for p in _HARDWARE_PRODUCTS if p["category"] == c]
        total = sum(p["quantity"] for p in products)
        domestic = sum(p["quantity"] for p in products if p["isDomestic"])
        rate = round((domestic / total) * 100, 1) if total else 0
        # 品牌分布
        brand_map: Dict[str, Dict[str, Any]] = {}
        for p in products:
            bm = brand_map.setdefault(p["brand"], {
                "brand": p["brand"], "isDomestic": p["isDomestic"], "count": 0, "percentage": 0.0, "avgMtbf": 0
            })
            bm["count"] += p["quantity"]
            bm["avgMtbf"] = p["mtbf"]  # 简化：直接取该产品的mtbf
        brands = list(brand_map.values())
        for b in brands:
            b["percentage"] = (b["count"] / total) * 100 if total else 0
        # 故障率（简化）
        avg_fail = round(sum(p["failureCount"] for p in products) / len(products), 2) if products else 0
        domestic_fail = round(sum(p["failureCount"] for p in products if p["isDomestic"]) / max(1, len([p for p in products if p["isDomestic"]])), 2)
        imported_fail = round(sum(p["failureCount"] for p in products if not p["isDomestic"]) / max(1, len([p for p in products if not p["isDomestic"]])), 2)
        metrics.append({
            "category": c,
            "totalCount": total,
            "domesticCount": domestic,
            "substitutionRate": rate,
            "brands": brands,
            "avgFailureRate": avg_fail,
            "domesticFailureRate": domestic_fail,
            "importedFailureRate": imported_fail,
        })
    return success_response(metrics, msg="获取国产替代指标成功")


@router.get("/hardware/plans", response_model=UnifiedResponse)
async def substitution_plans(
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    plans = [
        {
            "category": "操作系统",
            "currentRate": 45.2,
            "targetRate": 80.0,
            "timeline": "2025年底",
            "priority": "high",
            "challenges": ["兼容性问题", "运维人员培训", "应用程序适配"],
            "recommendations": ["建立测试环境", "制定迁移计划", "加强技术培训"],
        },
        {
            "category": "数据库",
            "currentRate": 32.1,
            "targetRate": 70.0,
            "timeline": "2026年中",
            "priority": "high",
            "challenges": ["数据迁移复杂", "性能调优", "业务连续性"],
            "recommendations": ["选择合适的迁移工具", "制定回滚方案", "分阶段实施"],
        },
    ]
    return success_response(plans, msg="获取替代规划成功")


# =============== 服务器故障统计（用于概览仪表板） ===============

@router.get("/server-failures", response_model=UnifiedResponse)
async def server_failures(
    months: int = Query(12, ge=1, le=24, description="返回最近多少个月数据"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_user)
):
    # 输出结构参考前端 serverFailureData.ts 的 mock
    # 这里返回简化版：按月份，每个IDC代码给出品牌数据
    idc_codes = ["BJ1", "BJ2", "SH1", "SH2", "SZ1", "SZ2"]
    brands_domestic = ["华为", "浪潮", "联想", "中兴", "中科曙光"]
    brands_foreign = ["Dell", "HPE", "IBM", "Cisco"]

    data: List[Dict[str, Any]] = []
    now = datetime.now()
    for i in range(months - 1, -1, -1):
        dt = (now.replace(day=1) - timedelta(days=30 * i))
        entry: Dict[str, Any] = {"month": int(dt.strftime("%Y%m"))}
        for code in idc_codes:
            arr = []
            # 生成少量品牌数据
            for b in brands_domestic[:2] + brands_foreign[:2]:
                count = 60 + (hash(code + b + str(i)) % 100)
                trouble = 3 + (hash(b + code + str(i)) % 10)
                arr.append({
                    "brand": b,
                    "count": count,
                    "trouble": trouble,
                    "tb_detail": [
                        {"name": "内存故障", "number": trouble // 3 + 1},
                        {"name": "硬盘故障", "number": trouble // 3 + 1},
                        {"name": "网卡故障", "number": trouble - 2 * (trouble // 3 + 1)},
                    ],
                })
            entry[code] = arr
        data.append(entry)

    # 附带映射和品牌类别
    idc_mapping = {
        "BJ1": "北京一号机房",
        "BJ2": "北京二号机房",
        "SH1": "上海一号机房",
        "SH2": "上海二号机房",
        "SZ1": "深圳一号机房",
        "SZ2": "深圳二号机房",
    }
    brand_categories = {b: "domestic" for b in brands_domestic}
    brand_categories.update({b: "foreign" for b in brands_foreign})

    return success_response({
        "monthlyTroubles": data,
        "idcMapping": idc_mapping,
        "brandCategories": brand_categories,
    }, msg="获取服务器故障统计成功")
