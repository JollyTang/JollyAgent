"""工具基类抽象模块."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolParameter(BaseModel):
    """工具参数定义."""
    
    name: str = Field(..., description="参数名称")
    type: str = Field(..., description="参数类型：string, integer, boolean, object, array")
    description: str = Field(..., description="参数描述")
    required: bool = Field(default=True, description="是否必需")
    default: Optional[Any] = Field(default=None, description="默认值")
    enum: Optional[List[Any]] = Field(default=None, description="枚举值列表")


class ToolSchema(BaseModel):
    """工具模式定义."""
    
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    parameters: List[ToolParameter] = Field(default_factory=list, description="参数列表")
    returns: str = Field(..., description="返回值描述")
    category: str = Field(default="general", description="工具类别")
    dangerous: bool = Field(default=False, description="是否为危险操作")


class ToolResult(BaseModel):
    """工具执行结果."""
    
    success: bool = Field(..., description="是否成功")
    result: Any = Field(..., description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class Tool(ABC):
    """工具基类抽象."""
    
    def __init__(self):
        """初始化工具."""
        self.schema = self._get_schema()
        logger.debug(f"Initialized tool: {self.schema.name}")
    
    @abstractmethod
    def _get_schema(self) -> ToolSchema:
        """获取工具模式定义."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """执行工具."""
        pass
    
    def validate_parameters(self, **kwargs) -> bool:
        """验证参数."""
        required_params = {p.name for p in self.schema.parameters if p.required}
        provided_params = set(kwargs.keys())
        
        # 检查必需参数
        missing_params = required_params - provided_params
        if missing_params:
            logger.error(f"Missing required parameters: {missing_params}")
            return False
        
        # 检查参数类型（简单验证）
        for param in self.schema.parameters:
            if param.name in kwargs:
                value = kwargs[param.name]
                if not self._validate_parameter_type(param, value):
                    logger.error(f"Invalid parameter type for {param.name}: expected {param.type}, got {type(value)}")
                    return False
        
        return True
    
    def _validate_parameter_type(self, param: ToolParameter, value: Any) -> bool:
        """验证参数类型."""
        if param.type == "string":
            return isinstance(value, str)
        elif param.type == "integer":
            return isinstance(value, int)
        elif param.type == "boolean":
            return isinstance(value, bool)
        elif param.type == "object":
            return isinstance(value, dict)
        elif param.type == "array":
            return isinstance(value, list)
        else:
            return True  # 未知类型，跳过验证
    
    def get_schema_dict(self) -> Dict[str, Any]:
        """获取工具模式的字典表示."""
        return self.schema.model_dump()
    
    def __str__(self) -> str:
        """字符串表示."""
        return f"Tool({self.schema.name})"
    
    def __repr__(self) -> str:
        """详细字符串表示."""
        return f"Tool(name={self.schema.name}, description={self.schema.description})"
