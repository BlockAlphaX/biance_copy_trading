import { useEffect, useState } from 'react';
import { Card, Table, Tag, Space, Button, DatePicker, Select, Input, Drawer } from 'antd';
import { SearchOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { tradesApi } from '../../services/api';
import dayjs from 'dayjs';

const { RangePicker } = DatePicker;

function Trades() {
  const [loading, setLoading] = useState(false);
  const [trades, setTrades] = useState<any[]>([]);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [filters, setFilters] = useState<any>({});
  const [selectedTrade, setSelectedTrade] = useState<any>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);

  useEffect(() => {
    fetchTrades();
  }, [pagination.current, pagination.pageSize, filters]);

  const fetchTrades = async () => {
    setLoading(true);
    try {
      const data = await tradesApi.getHistory({
        page: pagination.current,
        size: pagination.pageSize,
        ...filters,
      });
      setTrades(data.items || []);
      setPagination((prev) => ({ ...prev, total: data.total || 0 }));
    } catch (error) {
      console.error('Failed to fetch trades:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (newPagination: any) => {
    setPagination(newPagination);
  };

  const handleViewDetail = (trade: any) => {
    setSelectedTrade(trade);
    setDrawerVisible(true);
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
      sorter: true,
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      filters: [
        { text: 'BTCUSDT', value: 'BTCUSDT' },
        { text: 'ETHUSDT', value: 'ETHUSDT' },
      ],
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'BUY' ? 'green' : 'red'}>{side}</Tag>
      ),
      filters: [
        { text: 'BUY', value: 'BUY' },
        { text: 'SELL', value: 'SELL' },
      ],
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price.toFixed(2)}`,
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '总额',
      dataIndex: 'total',
      key: 'total',
      render: (_: any, record: any) => `$${(record.price * record.quantity).toFixed(2)}`,
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
      render: (status: string) => {
        const colorMap: any = {
          success: 'success',
          failed: 'error',
          pending: 'processing',
        };
        return <Tag color={colorMap[status] || 'default'}>{status}</Tag>;
      },
      filters: [
        { text: 'Success', value: 'success' },
        { text: 'Failed', value: 'failed' },
        { text: 'Pending', value: 'pending' },
      ],
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Button type="link" size="small" onClick={() => handleViewDetail(record)}>
          详情
        </Button>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Space wrap>
          <RangePicker
            onChange={(dates) =>
              setFilters({
                ...filters,
                start_time: dates?.[0]?.toISOString(),
                end_time: dates?.[1]?.toISOString(),
              })
            }
          />
          <Select
            placeholder="选择交易对"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => setFilters({ ...filters, symbol: value })}
          >
            <Select.Option value="BTCUSDT">BTCUSDT</Select.Option>
            <Select.Option value="ETHUSDT">ETHUSDT</Select.Option>
          </Select>
          <Input
            placeholder="搜索账户"
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
            onChange={(e) => setFilters({ ...filters, account: e.target.value })}
          />
          <Button icon={<ReloadOutlined />} onClick={fetchTrades}>
            刷新
          </Button>
          <Button icon={<DownloadOutlined />}>导出</Button>
        </Space>
      </Card>

      <Card title="交易历史">
        <Table
          columns={columns}
          dataSource={trades}
          rowKey="id"
          loading={loading}
          pagination={pagination}
          onChange={handleTableChange}
        />
      </Card>

      <Drawer
        title="交易详情"
        placement="right"
        width={500}
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
      >
        {selectedTrade && (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <div>
              <strong>交易ID:</strong> {selectedTrade.id}
            </div>
            <div>
              <strong>时间:</strong>{' '}
              {dayjs(selectedTrade.timestamp).format('YYYY-MM-DD HH:mm:ss')}
            </div>
            <div>
              <strong>交易对:</strong> {selectedTrade.symbol}
            </div>
            <div>
              <strong>方向:</strong>{' '}
              <Tag color={selectedTrade.side === 'BUY' ? 'green' : 'red'}>
                {selectedTrade.side}
              </Tag>
            </div>
            <div>
              <strong>价格:</strong> ${selectedTrade.price?.toFixed(2)}
            </div>
            <div>
              <strong>数量:</strong> {selectedTrade.quantity}
            </div>
            <div>
              <strong>账户:</strong> {selectedTrade.account}
            </div>
            <div>
              <strong>状态:</strong>{' '}
              <Tag
                color={
                  selectedTrade.status === 'success'
                    ? 'success'
                    : selectedTrade.status === 'failed'
                    ? 'error'
                    : 'processing'
                }
              >
                {selectedTrade.status}
              </Tag>
            </div>
          </Space>
        )}
      </Drawer>
    </Space>
  );
}

export default Trades;
