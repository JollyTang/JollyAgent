"""
OpenTelemetry 集成模块

提供 OpenTelemetry 的配置、初始化和基础功能。
实现任务 1.1: 集成 OpenTelemetry Python SDK 到 Agent 核心代码
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry import metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import ConsoleMetricExporter, PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    metrics = None
    TracerProvider = None
    BatchSpanProcessor = None
    ConsoleSpanExporter = None
    MeterProvider = None
    ConsoleMetricExporter = None
    PeriodicExportingMetricReader = None
    Resource = None

logger = logging.getLogger(__name__)


class OpenTelemetryIntegration:
    """OpenTelemetry 集成类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.tracer_provider = None
        self.meter_provider = None
        self.tracer = None
        self.meter = None
        self._initialized = False
        
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry 未安装，监控功能将被禁用")
            return
            
        self._setup_providers()
        self._setup_exporters()
        self._setup_instrumentation()
        
    def _setup_providers(self):
        """设置 Tracer 和 Meter 提供者"""
        try:
            resource = Resource.create({
                "service.name": "jollyagent",
                "service.version": "1.0.0",
                "service.instance.id": os.getenv("HOSTNAME", "unknown")
            })
            
            self.tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self.tracer_provider)
            
            metric_reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(),
                export_interval_millis=5000
            )
            self.meter_provider = MeterProvider(
                metric_readers=[metric_reader],
                resource=resource
            )
            metrics.set_meter_provider(self.meter_provider)
            
            logger.info("OpenTelemetry 提供者设置完成")
            
        except Exception as e:
            logger.error(f"设置 OpenTelemetry 提供者失败: {e}")
            
    def _setup_exporters(self):
        """设置导出器"""
        try:
            console_exporter = ConsoleSpanExporter()
            self.tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
            logger.info("控制台导出器已配置")
                
        except Exception as e:
            logger.error(f"设置导出器失败: {e}")
            
    def _setup_instrumentation(self):
        """设置基础工具"""
        try:
            self.tracer = trace.get_tracer(__name__)
            self.meter = metrics.get_meter(__name__)
            
            self.execution_counter = self.meter.create_counter(
                name="jollyagent.executions.total",
                description="Total number of executions"
            )
            
            self.execution_duration = self.meter.create_histogram(
                name="jollyagent.executions.duration",
                description="Execution duration in seconds"
            )
            
            self.error_counter = self.meter.create_counter(
                name="jollyagent.errors.total", 
                description="Total number of errors"
            )
            
            self._initialized = True
            logger.info("OpenTelemetry 工具设置完成")
            
        except Exception as e:
            logger.error(f"设置工具失败: {e}")
            
    def is_available(self) -> bool:
        """检查 OpenTelemetry 是否可用"""
        return OPENTELEMETRY_AVAILABLE and self._initialized
        
    def get_tracer(self):
        """获取 tracer 实例"""
        return self.tracer if self.is_available() else None
        
    def get_meter(self):
        """获取 meter 实例"""
        return self.meter if self.is_available() else None
        
    @contextmanager
    def trace_execution(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """追踪执行过程的上下文管理器"""
        if not self.is_available():
            yield None
            return
            
        attributes = attributes or {}
        with self.tracer.start_as_current_span(name, attributes=attributes) as span:
            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
                
    def record_execution(self, name: str, duration: float, success: bool = True, 
                        attributes: Optional[Dict[str, Any]] = None):
        """记录执行指标"""
        if not self.is_available():
            return
            
        try:
            self.execution_counter.add(1, {
                "name": name,
                "success": str(success).lower()
            })
            
            self.execution_duration.record(duration, {
                "name": name,
                "success": str(success).lower()
            })
            
            if not success:
                self.error_counter.add(1, {"name": name})
                
        except Exception as e:
            logger.error(f"记录执行指标失败: {e}")
            
    def shutdown(self):
        """关闭 OpenTelemetry 集成"""
        try:
            if self.tracer_provider:
                self.tracer_provider.shutdown()
            if self.meter_provider:
                self.meter_provider.shutdown()
            logger.info("OpenTelemetry 集成已关闭")
        except Exception as e:
            logger.error(f"关闭 OpenTelemetry 集成失败: {e}")


# 全局实例
_global_integration: Optional[OpenTelemetryIntegration] = None


def get_global_integration() -> Optional[OpenTelemetryIntegration]:
    """获取全局 OpenTelemetry 集成实例"""
    return _global_integration


def initialize_global_integration(config: Optional[Dict[str, Any]] = None) -> OpenTelemetryIntegration:
    """初始化全局 OpenTelemetry 集成"""
    global _global_integration
    if _global_integration is None:
        _global_integration = OpenTelemetryIntegration(config)
    return _global_integration


def shutdown_global_integration():
    """关闭全局 OpenTelemetry 集成"""
    global _global_integration
    if _global_integration:
        _global_integration.shutdown()
        _global_integration = None 