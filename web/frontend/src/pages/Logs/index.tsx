import { useEffect, useState } from 'react';
import { Card, Table, Tabs, Button, Space, Input, Select, Tag } from 'antd';
import { ReloadOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import { logsApi } from '../../services/api';
import dayjs from 'dayjs';

const { TabPane } = Tabs;

function Logs() {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('system');
  const [logs, setLogs] = useState<any[]>([]);
  const [filters, setFilters] = useState<any>({});

  useEffect(() => {
    fetchLogs();
  }, [activeTab, filters]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      let data;
      if (activeTab === 'system') {
        data = await logsApi.getSystem(filters);
      } else if (activeTab === 'trades') {
        data = await logsApi.getTrades(filters);
      } else {
        data = await logsApi.getErrors(filters);
      }
      setLogs(data || []);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleClearLogs = async () => {
    try {
      await logsApi.clear(activeTab);
      fetchLogs();
    } catch (error) {
      console.error('Failed to clear logs:', error);
    }
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (level: string) => {
        const colorMap: any = {
          ERROR: 'red',
          WARNING: 'orange',
          INFO: 'blue',
          DEBUG: 'default',
        };
        return <Tag color={colorMap[level]}>{level}</Tag>;
      },
    },
    {
      title: '来源',
      dataIndex: 'source',
      key: 'source',
      width: 150,
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
  ];

  return (
    <Card>
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="系统日志" key="system">
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Space wrap>
              <Select
                placeholder="选择级别"
                style={{ width: 120 }}
                allowClear
                onChange={(value) => setFilters({ ...filters, level: value })}
              >
                <Select.Option value="ERROR">ERROR</Select.Option>
                <Select.Option value="WARNING">WARNING</Select.Option>
                <Select.Option value="INFO">INFO</Select.Option>
                <Select.Option value="DEBUG">DEBUG</Select.Option>
              </Select>
              <Input
                placeholder="搜索关键词"
                prefix={<SearchOutlined />}
                style={{ width: 200 }}
                onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              />
              <Button icon={<ReloadOutlined />} onClick={fetchLogs}>
                刷新
              </Button>
              <Button icon={<DeleteOutlined />} danger onClick={handleClearLogs}>
                清空日志
              </Button>
            </Space>
            <Table
              columns={columns}
              dataSource={logs}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 20 }}
              size="small"
            />
          </Space>
        </TabPane>
        <TabPane tab="交易日志" key="trades">
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Space wrap>
              <Input
                placeholder="搜索关键词"
                prefix={<SearchOutlined />}
                style={{ width: 200 }}
                onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              />
              <Button icon={<ReloadOutlined />} onClick={fetchLogs}>
                刷新
              </Button>
              <Button icon={<DeleteOutlined />} danger onClick={handleClearLogs}>
                清空日志
              </Button>
            </Space>
            <Table
              columns={columns}
              dataSource={logs}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 20 }}
              size="small"
            />
          </Space>
        </TabPane>
        <TabPane tab="错误日志" key="errors">
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Space wrap>
              <Input
                placeholder="搜索关键词"
                prefix={<SearchOutlined />}
                style={{ width: 200 }}
                onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
              />
              <Button icon={<ReloadOutlined />} onClick={fetchLogs}>
                刷新
              </Button>
              <Button icon={<DeleteOutlined />} danger onClick={handleClearLogs}>
                清空日志
              </Button>
            </Space>
            <Table
              columns={columns}
              dataSource={logs}
              rowKey="id"
              loading={loading}
              pagination={{ pageSize: 20 }}
              size="small"
            />
          </Space>
        </TabPane>
      </Tabs>
    </Card>
  );
}

export default Logs;
