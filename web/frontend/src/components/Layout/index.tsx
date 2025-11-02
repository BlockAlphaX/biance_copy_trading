import { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { Layout as AntLayout, Menu, theme, Badge, Button, Space } from 'antd';
import {
  DashboardOutlined,
  SwapOutlined,
  UserOutlined,
  LineChartOutlined,
  WarningOutlined,
  FileTextOutlined,
  SettingOutlined,
  PoweroffOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useSystemStore } from '../../stores/useSystemStore';
import { systemApi } from '../../services/api';
import { wsManager } from '../../services/websocket';
import './index.css';

const { Header, Sider, Content } = AntLayout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '总览' },
  { key: '/trades', icon: <SwapOutlined />, label: '交易监控' },
  { key: '/accounts', icon: <UserOutlined />, label: '账户管理' },
  { key: '/metrics', icon: <LineChartOutlined />, label: '性能监控' },
  { key: '/risk', icon: <WarningOutlined />, label: '风险管理' },
  { key: '/logs', icon: <FileTextOutlined />, label: '日志查看' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
];

function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { status, setStatus } = useSystemStore();
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  useEffect(() => {
    // 连接 WebSocket
    wsManager.connect();

    // 获取系统状态
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 5000);

    return () => {
      clearInterval(interval);
      wsManager.disconnect();
    };
  }, []);

  const fetchSystemStatus = async () => {
    try {
      const data = await systemApi.getStatus();
      setStatus(data.status);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      setStatus('error');
    }
  };

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleSystemControl = async (action: 'start' | 'stop' | 'restart') => {
    try {
      if (action === 'start') {
        await systemApi.start();
      } else if (action === 'stop') {
        await systemApi.stop();
      } else {
        await systemApi.restart();
      }
      fetchSystemStatus();
    } catch (error) {
      console.error(`Failed to ${action} system:`, error);
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return 'success';
      case 'stopped':
        return 'default';
      case 'error':
        return 'error';
      default:
        return 'processing';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'running':
        return '运行中';
      case 'stopped':
        return '已停止';
      case 'error':
        return '错误';
      default:
        return '未知';
    }
  };

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div className="logo">
          {collapsed ? 'BCT' : 'Binance Copy Trading'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <AntLayout style={{ marginLeft: collapsed ? 80 : 200, transition: 'all 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <Badge status={getStatusColor()} text={`系统状态: ${getStatusText()}`} />
          </div>
          <Space>
            <Button
              type="primary"
              icon={<PoweroffOutlined />}
              onClick={() => handleSystemControl(status === 'running' ? 'stop' : 'start')}
              danger={status === 'running'}
            >
              {status === 'running' ? '停止' : '启动'}
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => handleSystemControl('restart')}
            >
              重启
            </Button>
          </Space>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: colorBgContainer,
            overflow: 'auto',
          }}
        >
          <Outlet />
        </Content>
      </AntLayout>
    </AntLayout>
  );
}

export default Layout;
