import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Input,
  message,
  Modal,
  Tooltip
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { ScanConfigApi } from '../services/scanConfigApi';
import type { ScanConfig } from '../types/scanConfig';
import ScanConfigFormModal from './ScanConfigFormModal';

const { Search } = Input;

const ScanConfigManagement: React.FC = () => {
  const [configs, setConfigs] = useState<ScanConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchName, setSearchName] = useState('');
  const [formModalVisible, setFormModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState<ScanConfig | undefined>();

  // 获取配置列表
  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const response = await ScanConfigApi.listConfigs({
        page: currentPage,
        size: pageSize,
        config_name: searchName || undefined
      });

      // omind_get返回的response结构: {status, msg, data, code}
      // response本身就是后端返回的数据
      if (response.status === 'ok') {
        setConfigs(response.data.items);
        setTotal(response.data.pagination.total);
      } else {
        message.error(response.msg || '获取配置列表失败');
      }
    } catch (error) {
      console.error('Fetch error:', error);
      message.error('获取配置列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, [currentPage, pageSize, searchName]);

  // 处理删除
  const handleDelete = (configId: string, isDefault: boolean) => {
    if (isDefault) {
      message.warning('默认配置不能删除');
      return;
    }

    Modal.confirm({
      title: '确认删除',
      content: '删除后将无法恢复，确定要删除此配置吗？',
      onOk: async () => {
        try {
          const response = await ScanConfigApi.deleteConfig(configId);

          if (response.status === 'ok') {
            message.success('删除成功');
            fetchConfigs();
          } else {
            message.error(response.msg || '删除失败');
          }
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  // 打开新建表单
  const handleCreate = () => {
    setEditingConfig(undefined);
    setFormModalVisible(true);
  };

  // 打开编辑表单
  const handleEdit = (config: ScanConfig) => {
    setEditingConfig(config);
    setFormModalVisible(true);
  };

  // 表单提交成功
  const handleFormSuccess = () => {
    fetchConfigs();
  };

  // 表格列定义
  const columns: ColumnsType<ScanConfig> = [
    {
      title: '配置名称',
      dataIndex: 'config_name',
      key: 'config_name',
      width: 200,
    },
    {
      title: '配置ID',
      dataIndex: 'config_id',
      key: 'config_id',
      width: 180,
      ellipsis: true,
    },
    {
      title: '配置描述',
      dataIndex: 'config_description',
      key: 'config_description',
      ellipsis: true,
      render: (desc) => desc || '-'
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => (
        <Tag color={status === 'active' ? 'success' : 'default'}>
          {status === 'active' ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '创建人',
      dataIndex: 'create_by',
      key: 'create_by',
      width: 120
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: (time) => new Date(time).toLocaleString('zh-CN', { hour12: false })
    },
    {
      title: '修改人',
      dataIndex: 'update_by',
      key: 'update_by',
      width: 120,
      render: (text) => text || '-'
    },
    {
      title: '修改时间',
      dataIndex: 'update_time',
      key: 'update_time',
      width: 180,
      render: (time) => time ? new Date(time).toLocaleString('zh-CN', { hour12: false }) : '-'
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right',
      width: 150,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.config_id, record.is_default)}
            disabled={record.is_default}
          >
            删除
          </Button>
        </Space>
      )
    }
  ];

  return (
    <div className="scan-config-management-container">
      <Card
        title="扫描配置管理"
        extra={
          <Space>
            <Search
              placeholder="搜索配置名称"
              allowClear
              style={{ width: 200 }}
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
              onSearch={(value) => {
                setCurrentPage(1);
                setSearchName(value);
              }}
            />
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchConfigs}
            >
              刷新
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              新建配置
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={configs}
          rowKey="config_id"
          loading={loading}
          scroll={{ x: 1000 }}
          pagination={{
            current: currentPage,
            pageSize: pageSize,
            total: total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (page, size) => {
              setCurrentPage(page);
              setPageSize(size || 10);
            }
          }}
        />
      </Card>

      {/* 配置表单模态框 */}
      <ScanConfigFormModal
        visible={formModalVisible}
        config={editingConfig}
        onClose={() => setFormModalVisible(false)}
        onSuccess={handleFormSuccess}
      />
    </div>
  );
};

export default ScanConfigManagement;
