# IDC 运维报告模块

这个模块用于管理IDC(数据中心)的运维报告。

## 功能特性

- IDC运行报告生成
- 报告查看和下载
- 电力使用情况统计
- PUE(电源使用效率)监控
- 设备可用性统计
- 告警信息汇总

## API 接口

### 报告管理
- `GET /api/v1/idc-reports` - 获取报告列表
- `POST /api/v1/idc-reports` - 创建新报告
- `GET /api/v1/idc-reports/{id}` - 获取报告详情
- `DELETE /api/v1/idc-reports/{id}` - 删除报告
- `GET /api/v1/idc-reports/{id}/download` - 下载报告文件

### 统计信息
- `GET /api/v1/idc-reports/stats` - 获取统计信息
- `GET /api/v1/idc-reports/locations` - 获取IDC位置列表

