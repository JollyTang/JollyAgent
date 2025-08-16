"""
OpenTelemetry 集成模块测试

测试 OpenTelemetry 集成功能
"""

import unittest
from unittest.mock import patch, MagicMock
import time
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.monitoring.opentelemetry_integration import OpenTelemetryIntegration, initialize_global_integration


class TestOpenTelemetryIntegration(unittest.TestCase):
    """测试 OpenTelemetry 集成"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            "otlp_endpoint": "http://localhost:4317"
        }
        
    def test_initialization_without_opentelemetry(self):
        """测试在没有 OpenTelemetry 的情况下初始化"""
        with patch('src.monitoring.opentelemetry_integration.OPENTELEMETRY_AVAILABLE', False):
            integration = OpenTelemetryIntegration(self.config)
            self.assertFalse(integration.is_available())
            
    def test_initialization_with_opentelemetry(self):
        """测试在有 OpenTelemetry 的情况下初始化"""
        with patch('src.monitoring.opentelemetry_integration.OPENTELEMETRY_AVAILABLE', True):
            with patch('src.monitoring.opentelemetry_integration.trace') as mock_trace:
                with patch('src.monitoring.opentelemetry_integration.metrics') as mock_metrics:
                    with patch('src.monitoring.opentelemetry_integration.TracerProvider') as mock_tracer_provider:
                        with patch('src.monitoring.opentelemetry_integration.MeterProvider') as mock_meter_provider:
                            # 模拟 TracerProvider
                            mock_tracer_provider_instance = MagicMock()
                            mock_tracer_provider.return_value = mock_tracer_provider_instance
                            
                            # 模拟 MeterProvider
                            mock_meter_provider_instance = MagicMock()
                            mock_meter_provider.return_value = mock_meter_provider_instance
                            
                            # 模拟 tracer 和 meter
                            mock_tracer = MagicMock()
                            mock_trace.get_tracer.return_value = mock_tracer
                            
                            mock_meter = MagicMock()
                            mock_metrics.get_meter.return_value = mock_meter
                            
                            integration = OpenTelemetryIntegration(self.config)
                            
                            # 验证初始化
                            self.assertTrue(integration.is_available())
                            self.assertEqual(integration.tracer, mock_tracer)
                            self.assertEqual(integration.meter, mock_meter)
                            
    def test_trace_execution_context_manager(self):
        """测试执行追踪上下文管理器"""
        with patch('src.monitoring.opentelemetry_integration.OPENTELEMETRY_AVAILABLE', True):
            with patch('src.monitoring.opentelemetry_integration.trace') as mock_trace:
                with patch('src.monitoring.opentelemetry_integration.metrics') as mock_metrics:
                    with patch('src.monitoring.opentelemetry_integration.TracerProvider') as mock_tracer_provider:
                        with patch('src.monitoring.opentelemetry_integration.MeterProvider') as mock_meter_provider:
                            # 模拟 span
                            mock_span = MagicMock()
                            mock_span_context = MagicMock()
                            mock_span_context.__enter__ = MagicMock(return_value=mock_span)
                            mock_span_context.__exit__ = MagicMock(return_value=None)
                            
                            mock_tracer = MagicMock()
                            mock_tracer.start_as_current_span.return_value = mock_span_context
                            mock_trace.get_tracer.return_value = mock_tracer
                            
                            mock_meter = MagicMock()
                            mock_metrics.get_meter.return_value = mock_meter
                            
                            integration = OpenTelemetryIntegration(self.config)
                            
                            # 测试正常执行
                            with integration.trace_execution("test.operation", {"key": "value"}) as span:
                                self.assertEqual(span, mock_span)
                                
                            # 测试异常处理
                            with self.assertRaises(ValueError):
                                with integration.trace_execution("test.error", {"key": "value"}):
                                    raise ValueError("Test error")
                                    
    def test_record_execution(self):
        """测试记录执行指标"""
        with patch('src.monitoring.opentelemetry_integration.OPENTELEMETRY_AVAILABLE', True):
            with patch('src.monitoring.opentelemetry_integration.trace') as mock_trace:
                with patch('src.monitoring.opentelemetry_integration.metrics') as mock_metrics:
                    with patch('src.monitoring.opentelemetry_integration.TracerProvider') as mock_tracer_provider:
                        with patch('src.monitoring.opentelemetry_integration.MeterProvider') as mock_meter_provider:
                            # 模拟 meter 和计数器
                            mock_counter = MagicMock()
                            mock_histogram = MagicMock()
                            mock_meter = MagicMock()
                            mock_meter.create_counter.return_value = mock_counter
                            mock_meter.create_histogram.return_value = mock_histogram
                            mock_metrics.get_meter.return_value = mock_meter
                            
                            mock_tracer = MagicMock()
                            mock_trace.get_tracer.return_value = mock_tracer
                            
                            integration = OpenTelemetryIntegration(self.config)
                            
                            # 测试记录成功执行
                            integration.record_execution("test.operation", 1.5, True, {"key": "value"})
                            mock_counter.add.assert_called()
                            mock_histogram.record.assert_called()
                            
                            # 测试记录失败执行
                            integration.record_execution("test.error", 0.5, False, {"key": "value"})
                            # 验证错误计数器被调用
                            self.assertTrue(mock_counter.add.call_count >= 2)
                            
    def test_global_integration(self):
        """测试全局集成实例"""
        # 测试初始化
        integration1 = initialize_global_integration(self.config)
        integration2 = initialize_global_integration(self.config)
        
        # 应该返回同一个实例
        self.assertIs(integration1, integration2)
        
        # 测试获取全局实例
        from src.monitoring.opentelemetry_integration import get_global_integration
        global_integration = get_global_integration()
        self.assertIs(global_integration, integration1)


if __name__ == '__main__':
    unittest.main() 