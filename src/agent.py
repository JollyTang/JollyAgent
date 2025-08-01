"""JollyAgent - ReAct AI Agent implementation."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import os
from uuid import uuid4

import openai
from pydantic import BaseModel, Field

from src.config import get_config
from src.executor import get_executor
from src.tools import AVAILABLE_TOOLS
from src.memory import LayeredMemoryCoordinator

# 配置日志
logger = logging.getLogger(__name__)


class Message(BaseModel):
    """消息数据模型."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: str = Field(..., description="消息角色：user, assistant, tool")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ToolCall(BaseModel):
    """工具调用数据模型."""
    
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(..., description="工具参数")
    id: Optional[str] = Field(default=None, description="工具调用ID")


class Thought(BaseModel):
    """思考过程数据模型."""
    
    content: str = Field(..., description="思考内容")
    reasoning: Optional[str] = Field(default=None, description="推理过程")
    plan: Optional[List[str]] = Field(default=None, description="执行计划")


class Observation(BaseModel):
    """观察结果数据模型."""
    
    tool_name: str = Field(..., description="工具名称")
    result: str = Field(..., description="执行结果")
    success: bool = Field(..., description="是否成功")
    error: Optional[str] = Field(default=None, description="错误信息")


class ReActStep(BaseModel):
    """ReAct步骤数据模型."""
    
    thought: Optional[Thought] = Field(default=None, description="思考过程")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="工具调用")
    observations: List[Observation] = Field(default_factory=list, description="观察结果")
    final_answer: Optional[str] = Field(default=None, description="最终答案")


class AgentState(BaseModel):
    """Agent状态数据模型."""
    
    conversation_id: str = Field(..., description="对话ID")
    messages: List[Message] = Field(default_factory=list, description="消息历史")
    react_steps: List[ReActStep] = Field(default_factory=list, description="ReAct步骤")
    current_step: Optional[ReActStep] = Field(default=None, description="当前步骤")
    is_completed: bool = Field(default=False, description="是否完成")


class Agent:
    """JollyAgent 主类，实现 ReAct 循环."""
    
    def __init__(self, config=None, enable_confirmation: bool = True, auto_confirm: bool = False):
        """初始化 Agent.
        
        Args:
            config: 配置对象
            enable_confirmation: 是否启用用户确认机制
            auto_confirm: 是否自动确认所有操作
        """
        self.config = config or get_config()
        self.state: Optional[AgentState] = None
        
        # 初始化用户确认管理器
        if enable_confirmation:
            from src.cli import UserConfirmation
            self.confirmation_manager = UserConfirmation(auto_confirm=auto_confirm)
        else:
            self.confirmation_manager = None
        
        # 初始化 OpenAI 客户端
        self.client = openai.OpenAI(
            base_url=self.config.llm.base_url,
            api_key=self.config.llm.api_key,
        )
        
        # 初始化分层记忆管理器
        memory_config = {
            "persist_directory": self.config.memory.persist_directory,
            "embedding_dimension": self.config.memory.embedding_dimension,
            "index_type": self.config.memory.index_type,
            "embedding_model": self.config.memory.embedding_model,
            "max_memory_items": self.config.memory.max_memory_items,
            "similarity_threshold": self.config.memory.similarity_threshold,
            "openai_api_key": self.config.llm.api_key,
            # 分层记忆配置
            "conversation_length_threshold": self.config.memory.conversation_length_threshold,
            "short_term_rounds": self.config.memory.short_term_rounds,
            "summary_model": self.config.memory.summary_model,
            "summary_max_tokens": self.config.memory.summary_max_tokens
        }
        
        if self.config.memory.enable_layered_memory:
            self.memory_manager = LayeredMemoryCoordinator(memory_config)
            logger.info("Using layered memory management system")
        else:
            # 回退到原有的FAISS记忆管理器
            from src.memory import FAISSMemoryManager
            self.memory_manager = FAISSMemoryManager(memory_config)
            logger.info("Using legacy FAISS memory management system")
        
        # 注册工具
        self._register_tools()
        
        # 设置日志
        self._setup_logging()
        
        logger.info("Agent initialized successfully")
    
    def _register_tools(self):
        """注册所有可用的工具."""
        executor = get_executor()
        executor.register_tools(AVAILABLE_TOOLS)
        logger.info(f"Registered {len(AVAILABLE_TOOLS)} tools")
    
    def _setup_logging(self):
        """设置日志配置."""
        # 确保日志文件路径是绝对路径
        log_file = self.config.logging.file
        if log_file and not os.path.isabs(log_file):
            # 如果是相对路径，转换为绝对路径（相对于项目根目录）
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_file = os.path.join(project_root, log_file)
        
        # 确保日志目录存在
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.logging.level),
            format=self.config.logging.format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file) if log_file else logging.NullHandler()
            ]
        )
    
    async def _save_conversation_memory(self):
        """保存对话记忆到记忆管理器."""
        try:
            # 确保记忆管理器已初始化
            if not self.memory_manager._is_initialized:
                await self.memory_manager.initialize()
            
            # 保存所有对话消息（不仅仅是最近4条）
            for message in self.state.messages:
                # 跳过系统消息
                if message.role == "system":
                    continue
                
                # 添加元数据
                metadata = {
                    "conversation_id": self.state.conversation_id,
                    "timestamp": message.timestamp.isoformat(),
                    "message_id": message.id if hasattr(message, 'id') else None
                }
                
                # 保存到记忆管理器（分层记忆管理器会自动决定存储层级）
                await self.memory_manager.add_memory(
                    content=message.content,
                    role=message.role,
                    metadata=metadata
                )
            
            logger.info(f"Saved {len(self.state.messages)} messages to layered memory system")
            
        except Exception as e:
            logger.error(f"Failed to save conversation memory: {e}")
    
    async def start_conversation(self, conversation_id: Optional[str] = None) -> AgentState:
        """开始新的对话."""
        # 如果没有提供conversation_id，自动生成一个
        if conversation_id is None:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid4())[:8]}"
        
        self.state = AgentState(conversation_id=conversation_id)
        
        # 初始化记忆管理器
        try:
            await self.memory_manager.initialize()
            
            # 如果是分层记忆管理器，启动新会话
            if hasattr(self.memory_manager, 'start_conversation'):
                await self.memory_manager.start_conversation(conversation_id)
            
            logger.info("Memory manager initialized and conversation started")
        except Exception as e:
            logger.warning(f"Failed to initialize memory manager: {e}")
        
        return self.state
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """添加消息到对话历史."""
        if not self.state:
            raise ValueError("No active conversation. Call start_conversation() first.")
        
        message = Message(
            role=role,
            content=content,
            metadata=metadata
        )
        self.state.messages.append(message)
        logger.debug(f"Added {role} message: {content[:50]}...")
        return message
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词."""
        executor = get_executor()
        tool_schemas = executor.get_tool_schemas()
        
        # 构建工具描述
        tools_description = []
        for schema in tool_schemas:
            tool_desc = f"- {schema['name']}: {schema['description']}"
            if schema['parameters']:
                params_desc = []
                for param in schema['parameters']:
                    required = "必需" if param['required'] else "可选"
                    params_desc.append(f"{param['name']} ({param['type']}, {required})")
                tool_desc += f" 参数: {', '.join(params_desc)}"
            tools_description.append(tool_desc)
        
        tools_text = "\n".join(tools_description)
        
        return f"""你是一个智能的 AI Agent，能够通过 ReAct（思考-行动-观察）循环来解决问题。

你的能力包括：
1. 思考：分析问题并制定解决方案
2. 行动：调用合适的工具来执行任务
3. 观察：分析工具执行结果并决定下一步

可用工具：
{tools_text}

请按照以下格式进行响应：
1. 首先进行思考（Thought）
2. 然后调用工具（Tool Calls）
3. 最后给出最终答案（Final Answer）

工具调用格式：
{{
    "thought": "思考过程...",
    "tool_calls": [
        {{
            "name": "工具名称",
            "arguments": {{
                "参数名": "参数值"
            }}
        }}
    ],
    "final_answer": "最终答案（如果任务完成）"
}}

记住：
- 每个危险操作都需要用户确认
- 优先使用安全的工具和命令
- 如果任务完成，给出清晰的最终答案
- 如果工具执行失败，分析错误原因并尝试其他方法
"""
    
    async def _build_messages_for_llm(self) -> List[Dict[str, str]]:
        """构建发送给 LLM 的消息列表."""
        messages = [{"role": "system", "content": self._build_system_prompt()}]
        
        # 使用分层记忆管理器获取记忆上下文
        if self.state.messages:
            # 获取当前用户消息作为查询
            current_user_message = None
            for msg in reversed(self.state.messages):
                if msg.role == "user":
                    current_user_message = msg.content
                    break
            
            if current_user_message and hasattr(self.memory_manager, 'get_memory_context'):
                try:
                    # 获取分层记忆上下文
                    memory_context = await self.memory_manager.get_memory_context(
                        self.state.conversation_id, 
                        current_user_message
                    )
                    
                    # 构建记忆上下文文本
                    context_parts = []
                    
                    # 添加会话摘要
                    if memory_context.conversation_summary:
                        context_parts.append(f"会话摘要：{memory_context.conversation_summary}")
                    
                    # 添加相关长期记忆
                    if memory_context.relevant_memories:
                        context_parts.append("相关历史记忆：")
                        for i, memory in enumerate(memory_context.relevant_memories, 1):
                            context_parts.append(f"{i}. [{memory.role}] {memory.content}")
                    
                    # 添加短期记忆（最近N轮）
                    if memory_context.short_term_messages:
                        context_parts.append("最近对话：")
                        for msg in memory_context.short_term_messages:
                            context_parts.append(f"[{msg.role}] {msg.content}")
                    
                    if context_parts:
                        memory_context_text = "\n".join(context_parts)
                        messages.append({
                            "role": "system", 
                            "content": memory_context_text
                        })
                        logger.info(f"Added layered memory context: mode={memory_context.memory_mode}")
                        
                except Exception as e:
                    logger.warning(f"Failed to retrieve layered memory context: {e}")
                    # 回退到原有的简单记忆检索
                    try:
                        relevant_memories = await self.memory_manager.search_relevant_memories(
                            current_user_message, 
                            limit=3
                        )
                        
                        if relevant_memories:
                            memory_context = "相关历史记忆：\n"
                            for i, memory in enumerate(relevant_memories, 1):
                                memory_context += f"{i}. [{memory.role}] {memory.content}\n"
                            
                            messages.append({
                                "role": "system", 
                                "content": memory_context
                            })
                            logger.info(f"Added fallback memory context: {len(relevant_memories)} memories")
                    except Exception as e2:
                        logger.warning(f"Fallback memory retrieval also failed: {e2}")
        
        # 添加当前对话历史（只保留最近几条，避免重复）
        recent_messages = self.state.messages[-3:]  # 只保留最近3条消息
        for msg in recent_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    async def _call_llm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """调用 LLM API."""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.config.llm.model,
                messages=messages,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens,
                stream=False
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": response.usage.dict() if response.usage else None
            }
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def _parse_llm_response(self, response: str) -> ReActStep:
        """解析 LLM 响应，提取思考、工具调用和最终答案."""
        step = ReActStep()
        
        # 添加调试信息
        logger.debug(f"Raw LLM response: {response[:200]}...")
        
        try:
            # 尝试解析 JSON 格式的响应
            if response.strip().startswith('{'):
                logger.debug("Attempting to parse JSON response")
                data = json.loads(response)
                
                # 解析思考过程
                if 'thought' in data:
                    step.thought = Thought(content=data['thought'])
                
                # 解析工具调用
                if 'tool_calls' in data:
                    for tool_call_data in data['tool_calls']:
                        step.tool_calls.append(ToolCall(**tool_call_data))
                
                # 解析最终答案
                if 'final_answer' in data:
                    step.final_answer = data['final_answer']
                
                logger.debug(f"Parsed JSON: thought={bool(step.thought)}, tool_calls={len(step.tool_calls)}, final_answer={bool(step.final_answer)}")
            
            else:
                logger.debug("Attempting to parse text response")
                # 简单文本解析（备用方案）
                lines = response.split('\n')
                current_section = None
                thought_content = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.lower().startswith('thought:'):
                        current_section = 'thought'
                        thought_content.append(line[7:].strip())
                    elif line.lower().startswith('action:'):
                        current_section = 'action'
                        # 简单的工具调用解析
                        if 'run_shell' in line:
                            command = line.split('run_shell')[-1].strip()
                            step.tool_calls.append(ToolCall(
                                name='run_shell',
                                arguments={'command': command}
                            ))
                    elif line.lower().startswith('answer:'):
                        step.final_answer = line[7:].strip()
                    elif current_section == 'thought':
                        thought_content.append(line)
                
                if thought_content:
                    step.thought = Thought(content=' '.join(thought_content))
                
                logger.debug(f"Parsed text: thought={bool(step.thought)}, tool_calls={len(step.tool_calls)}, final_answer={bool(step.final_answer)}")
        
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            # 如果解析失败，将整个响应作为思考内容
            step.thought = Thought(content=response)
        
        return step
    
    async def process_message(self, user_message: str) -> str:
        """处理用户消息，执行 ReAct 循环."""
        if not self.state:
            raise ValueError("No active conversation. Call start_conversation() first.")
        
        # 重置完成状态，确保每个新消息都能进入ReAct循环
        self.state.is_completed = False
        
        # 添加用户消息
        self.add_message("user", user_message)
        
        logger.info(f"Processing message: {user_message[:50]}...")
        
        # 开始 ReAct 循环
        max_iterations = 5  # 最大迭代次数
        iteration = 0
        
        while iteration < max_iterations and not self.state.is_completed:
            iteration += 1
            logger.info(f"ReAct iteration {iteration}")
            
            # 创建当前步骤
            current_step = ReActStep()
            self.state.current_step = current_step
            
            try:
                # 1. 思考阶段
                logger.debug("Calling _think method")
                await self._think(current_step)
                logger.debug(f"After _think: thought={bool(current_step.thought)}, tool_calls={len(current_step.tool_calls)}, final_answer={bool(current_step.final_answer)}")
                
                # 2. 行动阶段
                if current_step.tool_calls:
                    logger.debug("Calling _act method")
                    await self._act(current_step)
                
                # 3. 观察阶段
                if current_step.observations:
                    logger.debug("Calling _observe method")
                    await self._observe(current_step)
                
                # 4. 检查是否完成
                if current_step.final_answer:
                    logger.debug("Task completed with final answer")
                    self.state.is_completed = True
                    self.add_message("assistant", current_step.final_answer)
                    break
                
                # 将当前步骤添加到历史
                self.state.react_steps.append(current_step)
                
            except Exception as e:
                logger.error(f"Error in ReAct iteration {iteration}: {e}")
                # 如果出错，给出错误回答
                final_answer = f"抱歉，处理过程中出现错误：{str(e)}"
                self.state.is_completed = True
                self.add_message("assistant", final_answer)
                break
        
        if not self.state.is_completed:
            # 如果达到最大迭代次数仍未完成，给出默认回答
            final_answer = "抱歉，我无法在有限步骤内完成这个任务。请尝试将任务分解为更小的步骤。"
            self.state.is_completed = True
            self.add_message("assistant", final_answer)
        
        # 保存对话记忆
        await self._save_conversation_memory()
        
        return self.state.messages[-1].content
    
    async def _think(self, step: ReActStep):
        """思考阶段：分析问题并制定计划."""
        logger.debug("Starting think phase")
        
        # 构建提示词
        messages = await self._build_messages_for_llm()
        
        messages.append({
            "role": "user",
            "content": """请分析当前问题并制定解决方案。

你必须严格按照以下JSON格式返回响应：
{
    "thought": "你的思考过程...",
    "tool_calls": [
        {
            "name": "工具名称",
            "arguments": {
                "参数名": "参数值"
            }
        }
    ],
    "final_answer": "最终答案（如果任务完成）"
}

如果不需要使用工具，tool_calls可以是空数组。
如果任务完成，请提供final_answer。
如果还需要继续执行，final_answer可以是null。"""
        })
        
        # 调用 LLM
        response = await self._call_llm(messages)
        
        # 解析响应
        parsed_step = self._parse_llm_response(response["content"])
        step.thought = parsed_step.thought
        step.tool_calls = parsed_step.tool_calls
        step.final_answer = parsed_step.final_answer
        
        if step.thought:
            logger.debug(f"Thought: {step.thought.content[:100]}...")
    
    async def _act(self, step: ReActStep):
        """行动阶段：执行工具调用."""
        logger.debug("Starting act phase")
        
        executor = get_executor()
        
        # 如果有用户确认管理器，先确认工具调用
        if self.confirmation_manager and step.tool_calls:
            step_info = f"步骤 {len(self.state.react_steps) + 1}"
            if step.thought:
                step_info += f" - {step.thought.content[:50]}..."
            
            confirmed_calls = await self.confirmation_manager.confirm_tool_calls(
                step.tool_calls, 
                step_info
            )
            
            # 更新步骤中的工具调用为确认后的列表
            step.tool_calls = confirmed_calls
        
        for tool_call in step.tool_calls:
            logger.info(f"Executing tool: {tool_call.name}")
            
            # 执行工具
            result = await executor.execute_tool(
                tool_call.name, 
                **tool_call.arguments
            )
            
            # 创建观察结果
            observation = Observation(
                tool_name=tool_call.name,
                result=str(result.result) if result.success else result.error,
                success=result.success,
                error=result.error
            )
            step.observations.append(observation)
            
            # 记录到确认历史
            if self.confirmation_manager:
                self.confirmation_manager.add_to_history(
                    tool_call, 
                    True, 
                    "执行成功" if result.success else f"执行失败: {result.error}"
                )
            
            logger.debug(f"Tool {tool_call.name} result: {result.success}")
    
    async def _observe(self, step: ReActStep):
        """观察阶段：分析工具执行结果."""
        logger.debug("Starting observe phase")
        
        # 构建包含观察结果的提示词
        messages = await self._build_messages_for_llm()
        
        # 添加观察结果
        observations_text = "\n".join([
            f"Tool {obs.tool_name}: {obs.result}" 
            for obs in step.observations
        ])
        
        messages.append({
            "role": "user",
            "content": f"""基于以下观察结果，请决定下一步行动或给出最终答案：

观察结果：
{observations_text}

你必须严格按照以下JSON格式返回响应：
{{
    "thought": "你的思考过程...",
    "tool_calls": [
        {{
            "name": "工具名称",
            "arguments": {{
                "参数名": "参数值"
            }}
        }}
    ],
    "final_answer": "最终答案（如果任务完成）"
}}

如果任务完成，请提供final_answer。
如果还需要继续执行，final_answer可以是null。"""
        })
        
        # 调用 LLM
        response = await self._call_llm(messages)
        
        # 解析响应
        parsed_step = self._parse_llm_response(response["content"])
        step.final_answer = parsed_step.final_answer
        
        if step.final_answer:
            logger.debug(f"Final answer: {step.final_answer[:100]}...")
    
    async def end_conversation(self) -> Optional[str]:
        """结束当前会话并生成摘要."""
        if not self.state:
            logger.warning("No active conversation to end")
            return None
        
        try:
            # 如果是分层记忆管理器，结束会话并生成摘要
            if hasattr(self.memory_manager, 'end_conversation'):
                # 准备消息列表用于生成摘要
                messages_for_summary = []
                for msg in self.state.messages:
                    if msg.role in ["user", "assistant"]:
                        messages_for_summary.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                
                summary = await self.memory_manager.end_conversation(
                    self.state.conversation_id,
                    messages_for_summary
                )
                
                logger.info(f"Conversation ended with summary: {summary[:50]}...")
                return summary
            else:
                logger.info("Conversation ended (no summary generation)")
                return None
                
        except Exception as e:
            logger.error(f"Failed to end conversation: {e}")
            return None
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """获取对话摘要."""
        if not self.state:
            return {}
        
        return {
            "conversation_id": self.state.conversation_id,
            "message_count": len(self.state.messages),
            "react_steps_count": len(self.state.react_steps),
            "is_completed": self.state.is_completed,
            "last_message_time": self.state.messages[-1].timestamp if self.state.messages else None
        }


# 全局 Agent 实例
_agent_instance: Optional[Agent] = None


async def get_agent() -> Agent:
    """获取全局 Agent 实例."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = Agent()
        # 初始化记忆管理器
        try:
            await _agent_instance.memory_manager.initialize()
            logger.info("Global agent memory manager initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize global agent memory manager: {e}")
    return _agent_instance


def reset_agent():
    """重置全局 Agent 实例."""
    global _agent_instance
    if _agent_instance:
        # 关闭记忆管理器
        try:
            asyncio.create_task(_agent_instance.memory_manager.close())
        except Exception as e:
            logger.warning(f"Failed to close memory manager: {e}")
    _agent_instance = None
    logger.info("Agent instance reset")


def main():
    """CLI入口点."""
    import sys
    import os
    
    # 获取当前文件所在目录（src目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 添加src目录到Python路径
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 添加项目根目录到Python路径（用于导入其他模块）
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    try:
        from cli.cli import main as cli_main
        cli_main()
    except ImportError as e:
        print(f"导入错误: {e}")
        print(f"当前Python路径: {sys.path}")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
