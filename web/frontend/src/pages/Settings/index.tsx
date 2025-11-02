import { useEffect, useState } from 'react';
import { Card, Form, Input, InputNumber, Switch, Button, Space, message, Divider } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import { systemApi } from '../../services/api';

function Settings() {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const config = await systemApi.getConfig();
      form.setFieldsValue(config);
    } catch (error) {
      console.error('Failed to fetch config:', error);
      message.error('加载配置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      setSaving(true);
      await systemApi.updateConfig(values);
      message.success('配置保存成功');
    } catch (error) {
      console.error('Failed to save config:', error);
      message.error('配置保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card
      title="系统设置"
      extra={
        <Button
          type="primary"
          icon={<SaveOutlined />}
          loading={saving}
          onClick={handleSave}
        >
          保存配置
        </Button>
      }
    >
      <Form
        form={form}
        layout="vertical"
        loading={loading}
      >
        <Divider orientation="left">基础配置</Divider>
        
        <Form.Item
          label="主账户 API Key"
          name={['master', 'api_key']}
          rules={[{ required: true, message: '请输入主账户 API Key' }]}
        >
          <Input.Password placeholder="输入主账户 API Key" />
        </Form.Item>

        <Form.Item
          label="主账户 API Secret"
          name={['master', 'api_secret']}
          rules={[{ required: true, message: '请输入主账户 API Secret' }]}
        >
          <Input.Password placeholder="输入主账户 API Secret" />
        </Form.Item>

        <Divider orientation="left">交易配置</Divider>

        <Form.Item
          label="跟单模式"
          name={['trading', 'copy_mode']}
          valuePropName="checked"
        >
          <Switch checkedChildren="开启" unCheckedChildren="关闭" />
        </Form.Item>

        <Form.Item
          label="跟单比例"
          name={['trading', 'copy_ratio']}
          rules={[{ required: true, message: '请输入跟单比例' }]}
        >
          <InputNumber
            min={0.1}
            max={10}
            step={0.1}
            style={{ width: '100%' }}
            addonAfter="倍"
          />
        </Form.Item>

        <Form.Item
          label="最小订单金额"
          name={['trading', 'min_order_amount']}
        >
          <InputNumber
            min={1}
            style={{ width: '100%' }}
            addonAfter="USDT"
          />
        </Form.Item>

        <Form.Item
          label="最大订单金额"
          name={['trading', 'max_order_amount']}
        >
          <InputNumber
            min={1}
            style={{ width: '100%' }}
            addonAfter="USDT"
          />
        </Form.Item>

        <Divider orientation="left">风险管理</Divider>

        <Form.Item
          label="启用风险控制"
          name={['risk', 'enabled']}
          valuePropName="checked"
        >
          <Switch checkedChildren="开启" unCheckedChildren="关闭" />
        </Form.Item>

        <Form.Item
          label="最大持仓比例"
          name={['risk', 'max_position_ratio']}
        >
          <InputNumber
            min={0}
            max={100}
            style={{ width: '100%' }}
            addonAfter="%"
          />
        </Form.Item>

        <Form.Item
          label="止损比例"
          name={['risk', 'stop_loss_ratio']}
        >
          <InputNumber
            min={0}
            max={100}
            style={{ width: '100%' }}
            addonAfter="%"
          />
        </Form.Item>

        <Divider orientation="left">通知配置</Divider>

        <Form.Item
          label="启用 Telegram 通知"
          name={['notification', 'telegram_enabled']}
          valuePropName="checked"
        >
          <Switch checkedChildren="开启" unCheckedChildren="关闭" />
        </Form.Item>

        <Form.Item
          label="Telegram Bot Token"
          name={['notification', 'telegram_token']}
        >
          <Input.Password placeholder="输入 Telegram Bot Token" />
        </Form.Item>

        <Form.Item
          label="Telegram Chat ID"
          name={['notification', 'telegram_chat_id']}
        >
          <Input placeholder="输入 Telegram Chat ID" />
        </Form.Item>

        <Divider orientation="left">高级配置</Divider>

        <Form.Item
          label="Rate Limit (请求/分钟)"
          name={['advanced', 'rate_limit']}
        >
          <InputNumber
            min={1}
            max={1200}
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          label="熔断器阈值"
          name={['advanced', 'circuit_breaker_threshold']}
        >
          <InputNumber
            min={1}
            max={100}
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          label="日志级别"
          name={['advanced', 'log_level']}
        >
          <Input placeholder="DEBUG, INFO, WARNING, ERROR" />
        </Form.Item>
      </Form>
    </Card>
  );
}

export default Settings;
