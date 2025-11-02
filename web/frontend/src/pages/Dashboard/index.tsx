import { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, Tag, Space } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  DollarOutlined,
  SwapOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { systemApi, tradesApi, accountsApi } from '../../services/api';
import { wsManager } from '../../services/websocket';
import { useTradeStore } from '../../stores/useTradeStore';
import dayjs from 'dayjs';

function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [accounts, setAccounts] = useState<any[]>([]);
  const { trades, addTrade } = useTradeStore();

  useEffect(() => {
    fetchData();

    // 监听实时交易
    wsManager.on('trade', (trade: any) => {
      addTrade(trade);
    });

    return () => {
      wsManager.off('trade');
    };
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsData, accountsData] = await Promise.all([
        tradesApi.getStats(),
        accountsApi.getAll(),
      ]);
      setStats(statsData);
      setAccounts(accountsData);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const tradeColumns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text: string) => dayjs(text).format('HH:mm:ss'),
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'BUY' ? 'green' : 'red'}>{side}</Tag>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => price.toFixed(2),
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '账户',
      dataIndex: 'account',
      key: 'account',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'success' ? 'success' : 'error'}>{status}</Tag>
      ),
    },
  ];

  // 账户余额饼图
  const balanceChartOption = {
    title: {
      text: '账户余额分布',
      left: 'center',
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: ${c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
    },
    series: [
      {
        name: '余额',
        type: 'pie',
        radius: '50%',
        data: accounts.map((acc) => ({
          value: acc.balance || 0,
          name: acc.name,
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  };

  // 交易量趋势图
  const volumeChartOption = {
    title: {
      text: '24小时交易量',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 24 }, (_, i) => `${i}:00`),
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: '交易量',
        type: 'line',
        data: Array.from({ length: 24 }, () => Math.floor(Math.random() * 100)),
        smooth: true,
        areaStyle: {},
      },
    ],
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总交易量"
              value={stats?.total_trades || 0}
              prefix={<SwapOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="成功率"
              value={stats?.success_rate || 0}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总盈亏"
              value={stats?.total_pnl || 0}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="USDT"
              valueStyle={{ color: (stats?.total_pnl || 0) >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日交易"
              value={stats?.today_trades || 0}
              prefix={
                (stats?.today_change || 0) >= 0 ? (
                  <ArrowUpOutlined />
                ) : (
                  <ArrowDownOutlined />
                )
              }
              valueStyle={{
                color: (stats?.today_change || 0) >= 0 ? '#3f8600' : '#cf1322',
              }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card>
            <ReactECharts option={balanceChartOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card>
            <ReactECharts option={volumeChartOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      <Card title="实时交易流" extra={<Tag color="green">实时</Tag>}>
        <Table
          columns={tradeColumns}
          dataSource={trades.slice(0, 10)}
          rowKey="id"
          loading={loading}
          pagination={false}
          size="small"
        />
      </Card>
    </Space>
  );
}

export default Dashboard;
