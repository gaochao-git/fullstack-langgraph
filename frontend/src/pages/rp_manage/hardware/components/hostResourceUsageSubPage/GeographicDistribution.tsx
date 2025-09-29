// @ts-nocheck
import React, { useMemo } from 'react';
import { Card, Row, Col } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const GeographicDistribution = ({ data }) => {
  const regionData = useMemo(() => {
    if (!data || !Array.isArray(data)) {
      return [];
    }

    // 动态创建IDC区域，基于实际数据中的IDC信息
    const regions = {};
    
    data.forEach(item => {
      if (!item || !item.ip) return;
      
      // 获取IDC名称，优先使用idc_info，回退到IP区域计算作为兜底
      let regionName = '未知机房';
      if (item.idc_info && item.idc_info.idc_name) {
        regionName = item.idc_info.idc_name;
      } else {
        // 兜底逻辑：使用IP区域计算
        const ipSegment = item.ip.split('.')[2];
        regionName = `P${ipSegment}`;
      }
      
      // 如果该IDC区域不存在，创建它
      if (!regions[regionName]) {
        regions[regionName] = {
          name: regionName,
          totalMemory: 0,
          usedMemory: 0,
          totalDisk: 0,
          usedDisk: 0,
          totalCPU: 0,
          usedCPU: 0,
          hostCount: 0
        };
      }
      
      // 累加数据到对应的IDC区域
      regions[regionName].totalMemory += item.total_memory || 0;
      regions[regionName].usedMemory += item.used_memory || 0;
      regions[regionName].totalDisk += item.total_disk || 0;
      regions[regionName].usedDisk += item.used_disk || 0;
      regions[regionName].totalCPU += item.cpu_cores || 0; // 使用 cpu_cores 值
      regions[regionName].usedCPU += item.cpu_load || 0;
      regions[regionName].hostCount += 1; // 统计主机数量
    });

    return Object.values(regions);
  }, [data]);

  // 准备资源使用情况数据，确保所有值都是整数
  const memoryData = regionData.map(region => ({
    name: region.name,
    已用: Math.floor(region.usedMemory), // 使用 Math.floor() 确保为整数
    剩余: Math.floor(region.totalMemory - region.usedMemory),
  }));

  const diskData = regionData.map(region => ({
    name: region.name,
    已用: Math.floor(region.usedDisk), // 使用 Math.floor() 确保为整数
    剩余: Math.floor(region.totalDisk - region.usedDisk),
  }));

  const cpuData = regionData.map(region => ({
    name: region.name,
    已用: Math.floor(region.usedCPU), // 使用 Math.floor() 确保为整数
    剩余: Math.floor(100 - (region.usedCPU / region.totalCPU * 100)),
  }));

  // 准备饼图数据
  const hostCountData = regionData.map(region => ({
    name: region.name,
    value: region.hostCount,
  }));

  return (
    <Row gutter={[16, 16]}>
      <Col span={12}>
        <Card title="地域主机分布">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={hostCountData}
                cx="50%"
                cy="50%"
                labelLine={true}
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(1)}%)`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {hostCountData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      </Col>
      <Col span={12}>
        <Card title="内存使用情况">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={memoryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="已用" stackId="a" fill="#ff4d4f" />
              <Bar dataKey="剩余" stackId="a" fill="#52c41a" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>
      <Col span={12}>
        <Card title="磁盘使用情况">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={diskData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="已用" stackId="a" fill="#ff4d4f" />
              <Bar dataKey="剩余" stackId="a" fill="#52c41a" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>
      <Col span={12}>
        <Card title="CPU使用情况">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={cpuData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="已用" stackId="a" fill="#ff4d4f" />
              <Bar dataKey="剩余" stackId="a" fill="#52c41a" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>
    </Row>
  );
};

export default GeographicDistribution; 