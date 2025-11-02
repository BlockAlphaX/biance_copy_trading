import { useEffect, useState } from 'react';
import { Card, Row, Col, Alert, Button, Table, Tag, Space, Modal } from 'antd';
import { WarningOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { riskApi } from '../../services/api';
import dayjs from 'dayjs';

function Risk() {
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [summaryData, alertsData] = await Promise.all([
        riskApi.getSummary(),
        riskApi.getAlerts(),
      ]);
      setSummary(summaryData);
      setAlerts(alertsData);
    } catch (error) {
      console.error('Failed to fetch risk data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEmergencyStop = () => {
    Modal.confirm({
      title: '确认紧急停止',
      icon: <ExclamationCircleOutlined />,
      content: '这将立即停止所有交易活动。确定要继续吗？',
      okText: '确认',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await riskApi.emergencyStop();
          fetchData();
        } catch (error) {
          console.error('Failed to emergency stop:', error);
        }
      },
    });
  };

  const handleAckAlert = async (id: string) => {
    try {
      await riskApi.ackAlert(id);
      fetchData();
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const columns = [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      render: (level: string) => {
        const colorMap: any = {
          critical: 'red',
          warning: 'orange',
          info: 'blue',
        };
        return <Tag color={colorMap[level]}>{level.toUpperCase()}</Tag>;
      },
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: '消息',
      dataIndex: 'message',
      key: 'message',
    },
    {
      title: '状态',
      dataIndex: 'acknowledged',
      key: 'acknowledged',
      render: (ack: boolean) => (
        <Tag color={ack ? 'success' : 'warning'}>{ack ? '已确认' : '待处理'}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) =>
        !record.acknowledged && (
          <Button type="link" size="small" onClick={() => handleAckAlert(record.id)}>
            确认
          </Button>
        ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Alert
        message="风险管理系统"
        description="实时监控交易风险，及时发现并处理异常情况"
        type="info"
        showIcon
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <WarningOutlined style={{ fontSize: 48, color: '#faad14' }} />
              <h3>风险等级</h3>
              <Tag color={summary?.risk_level === 'high' ? 'red' : 'green'} style={{ fontSize: 16 }}>
                {summary?.risk_level?.toUpperCase() || 'LOW'}
              </Tag>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <h4>总持仓风险</h4>
            <p style={{ fontSize: 24, fontWeight: 'bold' }}>
              ${summary?.total_exposure?.toFixed(2) || 0}
            </p>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <h4>未确认告警</h4>
            <p style={{ fontSize: 24, fontWeight: 'bold', color: '#ff4d4f' }}>
              {alerts.filter((a) => !a.acknowledged).length}
            </p>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <h4>紧急操作</h4>
            <Button
              danger
              type="primary"
              icon={<ExclamationCircleOutlined />}
              onClick={handleEmergencyStop}
              block
            >
              紧急停止
            </Button>
          </Card>
        </Col>
      </Row>

      <Card title="风险告警" extra={<Button onClick={fetchData}>刷新</Button>}>
        <Table
          columns={columns}
          dataSource={alerts}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </Space>
  );
}

export default Risk;
