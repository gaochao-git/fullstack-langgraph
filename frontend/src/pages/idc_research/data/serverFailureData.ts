// 服务器故障数据结构
export interface ServerFailureDetail {
  name: string;
  number: number;
}

export interface ServerFailureItem {
  brand: string;
  count: number;
  trouble: number;
  tb_detail: ServerFailureDetail[];
}

export interface MonthlyFailureData {
  month: number;
  BJ1: ServerFailureItem[];
  BJ2: ServerFailureItem[];
  SH1: ServerFailureItem[];
  SH2: ServerFailureItem[];
  SZ1: ServerFailureItem[];
  SZ2: ServerFailureItem[];
}

export interface ServerFailureData {
  info: string;
  data: MonthlyFailureData[];
}

// 模拟服务器故障数据 - 12个月数据
export const mockServerFailureData: ServerFailureData = {
  "info": "服务器故障数据",
  "data": [
    {
      "month": 202412,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 12, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 4}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 1}]},
        {"brand": "华为", "count": 150, "trouble": 9, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 2}, {"name": "风扇故障", "number": 1}]},
        {"brand": "Dell", "count": 120, "trouble": 18, "tb_detail": [{"name": "硬盘故障", "number": 8}, {"name": "内存故障", "number": 5}, {"name": "电源故障", "number": 3}, {"name": "主板故障", "number": 2}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 6, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 14, "tb_detail": [{"name": "硬盘故障", "number": 6}, {"name": "内存故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 2}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 15, "tb_detail": [{"name": "内存故障", "number": 6}, {"name": "硬盘故障", "number": 5}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 2}]},
        {"brand": "中科曙光", "count": 60, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 8, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 2}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 11, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 4}, {"name": "网卡故障", "number": 2}]},
        {"brand": "IBM", "count": 75, "trouble": 10, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 3}, {"name": "主板故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 7, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}, {"name": "风扇故障", "number": 1}]}
      ]
    },
    {
      "month": 202411,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 11, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 2}]},
        {"brand": "华为", "count": 150, "trouble": 7, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}, {"name": "风扇故障", "number": 1}]},
        {"brand": "Dell", "count": 120, "trouble": 16, "tb_detail": [{"name": "硬盘故障", "number": 7}, {"name": "内存故障", "number": 4}, {"name": "电源故障", "number": 3}, {"name": "主板故障", "number": 2}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 13, "tb_detail": [{"name": "硬盘故障", "number": 5}, {"name": "内存故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 2}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 13, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 2}]},
        {"brand": "中科曙光", "count": 60, "trouble": 3, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 6, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 10, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]},
        {"brand": "IBM", "count": 75, "trouble": 9, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 2}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 6, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}]}
      ]
    },
    {
      "month": 202410,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 10, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 1}]},
        {"brand": "华为", "count": 150, "trouble": 8, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 2}, {"name": "风扇故障", "number": 1}]},
        {"brand": "Dell", "count": 120, "trouble": 15, "tb_detail": [{"name": "硬盘故障", "number": 6}, {"name": "内存故障", "number": 4}, {"name": "电源故障", "number": 3}, {"name": "主板故障", "number": 2}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 12, "tb_detail": [{"name": "硬盘故障", "number": 5}, {"name": "内存故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 12, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]},
        {"brand": "中科曙光", "count": 60, "trouble": 3, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 6, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 9, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "IBM", "count": 75, "trouble": 8, "tb_detail": [{"name": "硬盘故障", "number": 3}, {"name": "内存故障", "number": 2}, {"name": "主板故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}]}
      ]
    },
    {
      "month": 202409,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 9, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 1}]},
        {"brand": "华为", "count": 150, "trouble": 9, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 2}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]},
        {"brand": "Dell", "count": 120, "trouble": 14, "tb_detail": [{"name": "硬盘故障", "number": 6}, {"name": "内存故障", "number": 4}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 2}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 11, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 2}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 11, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]},
        {"brand": "中科曙光", "count": 60, "trouble": 3, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 8, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "IBM", "count": 75, "trouble": 7, "tb_detail": [{"name": "硬盘故障", "number": 3}, {"name": "内存故障", "number": 2}, {"name": "主板故障", "number": 1}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}, {"name": "网卡故障", "number": 1}]}
      ]
    },
    {
      "month": 202408,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 8, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 1}]},
        {"brand": "华为", "count": 150, "trouble": 9, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 2}, {"name": "网卡故障", "number": 2}, {"name": "风扇故障", "number": 1}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 3, "tb_detail": [{"name": "内存故障", "number": 1}, {"name": "硬盘故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 10, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 10, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 7, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "IBM", "count": 75, "trouble": 6, "tb_detail": [{"name": "硬盘故障", "number": 2}, {"name": "内存故障", "number": 2}, {"name": "主板故障", "number": 1}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}, {"name": "网卡故障", "number": 1}]}
      ]
    },
    {
      "month": 202407,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 14, "tb_detail": [{"name": "内存故障", "number": 6}, {"name": "硬盘故障", "number": 4}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 2}]},
        {"brand": "华为", "count": 150, "trouble": 11, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "风扇故障", "number": 2}]},
        {"brand": "Dell", "count": 120, "trouble": 21, "tb_detail": [{"name": "硬盘故障", "number": 9}, {"name": "内存故障", "number": 6}, {"name": "电源故障", "number": 4}, {"name": "主板故障", "number": 2}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 8, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 3}, {"name": "电源故障", "number": 2}]},
        {"brand": "HPE", "count": 90, "trouble": 16, "tb_detail": [{"name": "硬盘故障", "number": 7}, {"name": "内存故障", "number": 4}, {"name": "网卡故障", "number": 3}, {"name": "电源故障", "number": 2}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 16, "tb_detail": [{"name": "内存故障", "number": 6}, {"name": "硬盘故障", "number": 5}, {"name": "网卡故障", "number": 3}, {"name": "电源故障", "number": 2}]},
        {"brand": "中科曙光", "count": 60, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 10, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "电源故障", "number": 3}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 13, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 2}]},
        {"brand": "IBM", "count": 75, "trouble": 12, "tb_detail": [{"name": "硬盘故障", "number": 5}, {"name": "内存故障", "number": 3}, {"name": "主板故障", "number": 2}, {"name": "电源故障", "number": 2}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 9, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 2}, {"name": "风扇故障", "number": 1}]}
      ]
    },
    {
      "month": 202406,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 7, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 1}, {"name": "主板故障", "number": 1}]},
        {"brand": "华为", "count": 150, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}]},
        {"brand": "Dell", "count": 120, "trouble": 12, "tb_detail": [{"name": "硬盘故障", "number": 5}, {"name": "内存故障", "number": 3}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 2}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 2, "tb_detail": [{"name": "内存故障", "number": 1}, {"name": "硬盘故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 8, "tb_detail": [{"name": "硬盘故障", "number": 3}, {"name": "内存故障", "number": 2}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 10, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]},
        {"brand": "中科曙光", "count": 60, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 7, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "IBM", "count": 75, "trouble": 7, "tb_detail": [{"name": "硬盘故障", "number": 3}, {"name": "内存故障", "number": 2}, {"name": "主板故障", "number": 1}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}]}
      ]
    },
    {
      "month": 202405,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 9, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 1}]},
        {"brand": "华为", "count": 150, "trouble": 8, "tb_detail": [{"name": "硬盘故障", "number": 3}, {"name": "内存故障", "number": 3}, {"name": "网卡故障", "number": 1}, {"name": "风扇故障", "number": 1}]},
        {"brand": "Dell", "count": 120, "trouble": 13, "tb_detail": [{"name": "硬盘故障", "number": 5}, {"name": "内存故障", "number": 4}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 2}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 3, "tb_detail": [{"name": "内存故障", "number": 1}, {"name": "硬盘故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 10, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 11, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]},
        {"brand": "中科曙光", "count": 60, "trouble": 3, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 8, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "IBM", "count": 75, "trouble": 7, "tb_detail": [{"name": "硬盘故障", "number": 3}, {"name": "内存故障", "number": 2}, {"name": "主板故障", "number": 1}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}]}
      ]
    },
    {
      "month": 202404,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 11, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 3}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 1}]},
        {"brand": "华为", "count": 150, "trouble": 10, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "风扇故障", "number": 1}]},
        {"brand": "Dell", "count": 120, "trouble": 17, "tb_detail": [{"name": "硬盘故障", "number": 7}, {"name": "内存故障", "number": 5}, {"name": "电源故障", "number": 3}, {"name": "主板故障", "number": 2}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 12, "tb_detail": [{"name": "硬盘故障", "number": 5}, {"name": "内存故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 12, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]},
        {"brand": "中科曙光", "count": 60, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 6, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 9, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "IBM", "count": 75, "trouble": 8, "tb_detail": [{"name": "硬盘故障", "number": 3}, {"name": "内存故障", "number": 2}, {"name": "主板故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}]}
      ]
    },
    {
      "month": 202403,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 12, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 4}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 1}]},
        {"brand": "华为", "count": 150, "trouble": 10, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "风扇故障", "number": 1}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 12, "tb_detail": [{"name": "硬盘故障", "number": 5}, {"name": "内存故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 12, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 7, "tb_detail": [{"name": "内存故障", "number": 3}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 2}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 10, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]},
        {"brand": "IBM", "count": 75, "trouble": 9, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 2}, {"name": "主板故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}]}
      ]
    },
    {
      "month": 202402,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 13, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 4}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 2}]},
        {"brand": "华为", "count": 150, "trouble": 8, "tb_detail": [{"name": "硬盘故障", "number": 3}, {"name": "内存故障", "number": 3}, {"name": "网卡故障", "number": 1}, {"name": "风扇故障", "number": 1}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 11, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 2}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 11, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 6, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 2}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 9, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "IBM", "count": 75, "trouble": 8, "tb_detail": [{"name": "硬盘故障", "number": 3}, {"name": "内存故障", "number": 2}, {"name": "主板故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}]}
      ]
    },
    {
      "month": 202401,
      "BJ1": [
        {"brand": "中兴", "count": 100, "trouble": 12, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 4}, {"name": "电源故障", "number": 2}, {"name": "主板故障", "number": 1}]},
        {"brand": "华为", "count": 150, "trouble": 9, "tb_detail": [{"name": "硬盘故障", "number": 4}, {"name": "内存故障", "number": 2}, {"name": "网卡故障", "number": 2}, {"name": "风扇故障", "number": 1}]}
      ],
      "BJ2": [
        {"brand": "浪潮", "count": 80, "trouble": 4, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "HPE", "count": 90, "trouble": 12, "tb_detail": [{"name": "硬盘故障", "number": 5}, {"name": "内存故障", "number": 4}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH1": [
        {"brand": "华为", "count": 200, "trouble": 11, "tb_detail": [{"name": "内存故障", "number": 5}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SH2": [
        {"brand": "联想", "count": 110, "trouble": 6, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "电源故障", "number": 2}]}
      ],
      "SZ1": [
        {"brand": "华为", "count": 180, "trouble": 9, "tb_detail": [{"name": "内存故障", "number": 4}, {"name": "硬盘故障", "number": 3}, {"name": "网卡故障", "number": 1}, {"name": "电源故障", "number": 1}]},
        {"brand": "IBM", "count": 75, "trouble": 8, "tb_detail": [{"name": "硬盘故障", "number": 3}, {"name": "内存故障", "number": 2}, {"name": "主板故障", "number": 2}, {"name": "电源故障", "number": 1}]}
      ],
      "SZ2": [
        {"brand": "中兴", "count": 95, "trouble": 5, "tb_detail": [{"name": "内存故障", "number": 2}, {"name": "硬盘故障", "number": 2}, {"name": "网卡故障", "number": 1}]}
      ]
    }
  ]
};

// 机房映射
export const idcMapping: Record<string, string> = {
  'BJ1': '北京数据中心1',
  'BJ2': '北京数据中心2', 
  'SH1': '上海数据中心1',
  'SH2': '上海数据中心2',
  'SZ1': '深圳数据中心1',
  'SZ2': '深圳数据中心2'
};

// 品牌分类
export const brandCategories: Record<string, 'domestic' | 'foreign'> = {
  '华为': 'domestic',
  '中兴': 'domestic',
  '浪潮': 'domestic',
  '联想': 'domestic',
  '中科曙光': 'domestic',
  'Dell': 'foreign',
  'HPE': 'foreign',
  'IBM': 'foreign',
};

