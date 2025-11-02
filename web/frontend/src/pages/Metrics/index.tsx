import { useEffect, useState } from 'react';
import { Card, Row, Col, Progress, Space, Statistic } from 'antd';
import ReactECharts from 'echarts-for-react';
import { metricsApi } from '../../services/api';

function Metrics() {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const [rateLimit, performance, system] = await Promise.all([
        metricsApi.getRateLimit(),
        metricsApi.getPerformance(),
        metricsApi.getSystem(),
      ]);
      setMetrics({ rateLimit, performance, system });
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const rateLimitOption = {
    title: { text: 'API Rate Limit 使用情况', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['1分钟', '5分钟', '15分钟', '1小时'] },
    yAxis: { type: 'value' },
    series: [
      {
        name: '使用量',
        type: 'bar',
        data: [65, 45, 30, 20],
        itemStyle: { color: '#1890ff' },
      },
    ],
  };

  const performanceOption = {
    title: { text: 'API 响应时间', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 20 }, (_, i) => `${i}s`),
    },
    yAxis: { type: 'value', name: 'ms' },
    series: [
      {
        name: '响应时间',
        type: 'line',
        data: Array.from({ length: 20 }, () => Math.floor(Math.random() * 100 + 50)),
        smooth: true,
      },
    ],
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="CPU 使用率"
              value={metrics?.system?.cpu || 0}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
            />
            <Progress
              percent={metrics?.system?.cpu || 0}
              status="active"
              showInfo={false}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="内存使用率"
              value={metrics?.system?.memory || 0}
              suffix="%"
              valueStyle={{ color: '#1890ff' }}
            />
            <Progress
              percent={metrics?.system?.memory || 0}
              status="active"
              showInfo={false}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={metrics?.performance?.avg_response_time || 0}
              suffix="ms"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="请求成功率"
              value={metrics?.performance?.success_rate || 0}
              suffix="%"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card>
            <ReactECharts option={rateLimitOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card>
            <ReactECharts option={performanceOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>
    </Space>
  );
}

export default Metrics;
