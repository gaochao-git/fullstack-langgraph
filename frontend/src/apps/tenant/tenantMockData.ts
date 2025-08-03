// 租户模拟数据

export interface Tenant {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'inactive' | 'suspended';
  createdAt: string;
  updatedAt: string;
  domain: string;
  adminEmail: string;
  userCount: number;
}

export const tenantMockData: Tenant[] = [
  {
    id: 'tenant1',
    name: '企业云服务有限公司',
    description: '提供云计算服务的科技公司',
    status: 'active',
    createdAt: '2023-01-15T08:30:00Z',
    updatedAt: '2023-10-20T14:45:00Z',
    domain: 'cloudservice.example.com',
    adminEmail: 'admin@cloudservice.example.com',
    userCount: 50
  },
  {
    id: 'tenant2',
    name: '智慧教育平台',
    description: '专注于教育信息化的解决方案提供商',
    status: 'active',
    createdAt: '2023-03-22T10:15:00Z',
    updatedAt: '2023-09-12T16:20:00Z',
    domain: 'eduplatform.example.com',
    adminEmail: 'admin@eduplatform.example.com',
    userCount: 35
  },
  {
    id: 'tenant3',
    name: '医疗健康联盟',
    description: '医疗行业健康数据管理平台',
    status: 'suspended',
    createdAt: '2023-02-10T11:20:00Z',
    updatedAt: '2023-08-05T09:10:00Z',
    domain: 'healthalliance.example.com',
    adminEmail: 'admin@healthalliance.example.com',
    userCount: 20
  },
  {
    id: 'tenant4',
    name: '金融科技集团',
    description: '提供金融科技解决方案的集团公司',
    status: 'inactive',
    createdAt: '2023-04-30T15:45:00Z',
    updatedAt: '2023-05-15T11:30:00Z',
    domain: 'fintechgroup.example.com',
    adminEmail: 'admin@fintechgroup.example.com',
    userCount: 0
  },
  {
    id: 'tenant5',
    name: '智能制造系统',
    description: '工业4.0智能制造解决方案',
    status: 'active',
    createdAt: '2023-06-18T09:25:00Z',
    updatedAt: '2023-11-01T13:50:00Z',
    domain: 'smartmanufacturing.example.com',
    adminEmail: 'admin@smartmanufacturing.example.com',
    userCount: 42
  }
];