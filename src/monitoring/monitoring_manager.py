"""
监控管理器

统一管理监控功能，根据配置决定是否启用监控。
实现任务 1.4: 实现执行步骤追踪（Think-Act-Observe-Response）
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path
import time

from .custom_instrumentation import CustomInstrumentation, InstrumentationConfig
from .opentelemetry_integration import initialize_global_integration
from .step_tracker import initialize_global_step_tracker
from ..config import get_config

logger = logging.getLogger(__name__)


class MonitoringManager:
    """监控管理器"""
    
    def __init__(self):
        self.config = get_config()
        self.instrumentation: Optional[CustomInstrumentation] = None
        self.is_initialized = False
        
    def initialize(self) -> bool:
        """初始化监控系统"""
        if self.is_initialized:
            return True
            
        if not self.config.monitoring.enable_monitoring:
            logger.info("监控功能已禁用，跳过初始化")
            return False
            
        try:
            # 初始化 OpenTelemetry 集成
            if self.config.monitoring.enable_opentelemetry:
                initialize_global_integration({
                    "service_name": self.config.monitoring.service_name,
                    "service_version": self.config.monitoring.service_version
                })
                logger.info("OpenTelemetry 集成已初始化")
            
            # 初始化执行步骤追踪器
            if self.config.monitoring.enable_step_tracking:
                initialize_global_step_tracker({
                    "enable_step_tracking": self.config.monitoring.enable_step_tracking,
                    "enable_metadata_collection": self.config.monitoring.enable_metadata_collection
                })
                logger.info("执行步骤追踪器已初始化")
            
            # 创建自定义 instrumentation 配置
            instrumentation_config = InstrumentationConfig(
                enable_agent_tracing=self.config.monitoring.enable_agent_tracing,
                enable_tool_tracing=self.config.monitoring.enable_tool_tracing,
                enable_memory_tracing=self.config.monitoring.enable_memory_tracing,
                enable_llm_tracing=self.config.monitoring.enable_llm_tracing,
                enable_performance_metrics=self.config.monitoring.enable_performance_metrics,
                enable_error_tracking=self.config.monitoring.enable_error_tracking
            )
            
            # 初始化自定义 instrumentation
            self.instrumentation = CustomInstrumentation(instrumentation_config)
            
            # 确保监控数据目录存在
            if self.config.monitoring.enable_local_backup:
                backup_dir = Path(self.config.monitoring.backup_directory)
                backup_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"监控数据备份目录已创建: {backup_dir}")
            
            self.is_initialized = True
            logger.info("监控系统初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"监控系统初始化失败: {e}")
            return False
    
    def instrument_agent(self, agent_instance) -> bool:
        """为 Agent 实例添加监控"""
        if not self.is_initialized or not self.instrumentation:
            logger.warning("监控系统未初始化，跳过 Agent instrumentation")
            return False
            
        try:
            self.instrumentation.instrument_agent_methods(agent_instance)
            logger.info("Agent 监控已启用")
            return True
        except Exception as e:
            logger.error(f"Agent 监控启用失败: {e}")
            return False
    
    def instrument_executor(self, executor_instance) -> bool:
        """为执行器实例添加监控"""
        if not self.is_initialized or not self.instrumentation:
            logger.warning("监控系统未初始化，跳过执行器 instrumentation")
            return False
            
        try:
            self.instrumentation.instrument_tool_executor(executor_instance)
            logger.info("执行器监控已启用")
            return True
        except Exception as e:
            logger.error(f"执行器监控启用失败: {e}")
            return False
    
    def instrument_memory(self, memory_instance) -> bool:
        """为记忆管理器实例添加监控"""
        if not self.is_initialized or not self.instrumentation:
            logger.warning("监控系统未初始化，跳过记忆管理器 instrumentation")
            return False
            
        try:
            self.instrumentation.instrument_memory_manager(memory_instance)
            logger.info("记忆管理器监控已启用")
            return True
        except Exception as e:
            logger.error(f"记忆管理器监控启用失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        if not self.is_initialized or not self.instrumentation:
            return {"error": "监控系统未初始化"}
            
        try:
            stats = self.instrumentation.get_statistics()
            stats["monitoring_enabled"] = True
            stats["step_tracking_enabled"] = self.config.monitoring.enable_step_tracking
            stats["opentelemetry_enabled"] = self.config.monitoring.enable_opentelemetry
            return stats
        except Exception as e:
            logger.error(f"获取监控统计信息失败: {e}")
            return {"error": str(e)}
    
    def export_data(self, filepath: Optional[str] = None) -> bool:
        """导出监控数据"""
        if not self.is_initialized or not self.instrumentation:
            logger.warning("监控系统未初始化，无法导出数据")
            return False
            
        try:
            if filepath is None:
                filepath = Path(self.config.monitoring.backup_directory) / f"monitoring_data_{int(time.time())}.json"
            
            # 导出执行步骤追踪数据
            step_tracker = self.instrumentation.step_tracker
            if step_tracker:
                step_tracker.export_data(str(filepath))
            
            logger.info(f"监控数据已导出到: {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出监控数据失败: {e}")
            return False
    
    def is_monitoring_enabled(self) -> bool:
        """检查监控是否已启用"""
        return self.is_initialized and self.config.monitoring.enable_monitoring


# 全局监控管理器实例
_global_monitoring_manager: Optional[MonitoringManager] = None


def get_monitoring_manager() -> MonitoringManager:
    """获取全局监控管理器实例"""
    global _global_monitoring_manager
    if _global_monitoring_manager is None:
        _global_monitoring_manager = MonitoringManager()
    return _global_monitoring_manager


def initialize_monitoring() -> bool:
    """初始化监控系统"""
    manager = get_monitoring_manager()
    return manager.initialize()


def instrument_agent_with_monitoring(agent_instance) -> bool:
    """为 Agent 实例添加监控（便捷函数）"""
    manager = get_monitoring_manager()
    if not manager.is_initialized:
        manager.initialize()
    return manager.instrument_agent(agent_instance)


def instrument_executor_with_monitoring(executor_instance) -> bool:
    """为执行器实例添加监控（便捷函数）"""
    manager = get_monitoring_manager()
    if not manager.is_initialized:
        manager.initialize()
    return manager.instrument_executor(executor_instance)


def instrument_memory_with_monitoring(memory_instance) -> bool:
    """为记忆管理器实例添加监控（便捷函数）"""
    manager = get_monitoring_manager()
    if not manager.is_initialized:
        manager.initialize()
    return manager.instrument_memory(memory_instance) 