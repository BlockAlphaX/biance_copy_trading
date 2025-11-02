import { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Table, Switch, Button, InputNumber, Space, Tag } from 'antd';
import { DollarOutlined, UserOutlined } from '@ant-design/icons';
import { accountsApi } from '../../services/api';

function Accounts() {
  const [loading, setLoading] = useState(false);
  const [accounts, setAccounts] = useState<any[]>([]);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const data = await accountsApi.getAll();
      setAccounts(data);
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleEnable = async (name: string, enabled: boolean) => {
    try {
      await accountsApi.toggleEnable(name, enabled);
      fetchAccounts();
    } catch (error) {
      console.error('Failed to toggle account:', error);
    }
  };

  const handleSetLeverage = async (name: string, leverage: number) => {
    try {
      await accountsApi.setLeverage(name, leverage);
      fetchAccounts();
    } catch (error) {
      console.error('Failed to set leverage:', error);
    }
  };

  const columns = [
    {
      title: '账户名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'master' ? 'blue' : 'green'}>
          {type === 'master' ? '主账户' : '跟随账户'}
        </Tag>
      ),
    },
    {
      title: '余额',
      dataIndex: 'balance',
      key: 'balance',
      render: (balance: number) => `$${balance?.toFixed(2) || 0}`,
    },
    {
      title: '杠杆',
      dataIndex: 'leverage',
      key: 'leverage',
      render: (leverage: number, record: any) => (
        <InputNumber
          min={1}
          max={125}
          value={leverage}
          onChange={(value) => handleSetLeverage(record.name, value || 1)}
          style={{ width: 80 }}
        />
      ),
    },
    {
      title: '状态',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean, record: any) => (
        <Switch
          checked={enabled}
          onChange={(checked) => handleToggleEnable(record.name, checked)}
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space>
          <Button type="link" size="small">
            查看持仓
          </Button>
          <Button type="link" size="small">
            详情
          </Button>
        </Space>
      ),
    },
  ];

  const totalBalance = accounts.reduce((sum, acc) => sum + (acc.balance || 0), 0);
  const masterAccount = accounts.find((acc) => acc.type === 'master');
  const followerAccounts = accounts.filter((acc) => acc.type === 'follower');

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="总余额"
              value={totalBalance}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="USDT"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="账户数量"
              value={accounts.length}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="活跃账户"
              value={accounts.filter((acc) => acc.enabled).length}
              suffix={`/ ${accounts.length}`}
            />
          </Card>
        </Col>
      </Row>

      {masterAccount && (
        <Card title="主账户" extra={<Tag color="blue">Master</Tag>}>
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <Statistic title="账户名" value={masterAccount.name} />
            </Col>
            <Col span={8}>
              <Statistic
                title="余额"
                value={masterAccount.balance}
                precision={2}
                suffix="USDT"
              />
            </Col>
            <Col span={8}>
              <Statistic title="杠杆" value={`${masterAccount.leverage}x`} />
            </Col>
          </Row>
        </Card>
      )}

      <Card title="跟随账户">
        <Table
          columns={columns}
          dataSource={followerAccounts}
          rowKey="name"
          loading={loading}
          pagination={false}
        />
      </Card>
    </Space>
  );
}

export default Accounts;
