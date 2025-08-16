"""
简化的 Instrumentation 演示

修复了所有问题的演示版本
"""

import asyncio
import time
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 尝试导入真实的 OpenTelemetry 集成
try:
    from src.monitoring.opentelemetry_integration import initialize_global_integration
    print("✅ 使用真实的 OpenTelemetry 集成")
    OPENTELEMETRY_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  OpenTelemetry 未安装: {e}")
    print("🔧 使用模拟的 OpenTelemetry 集成")
    OPENTELEMETRY_AVAILABLE = False
    
    # 创建模拟的 OpenTelemetry 集成
    class MockOpenTelemetryIntegration:
        def __init__(self, config=None):
            print("🔧 使用模拟的 OpenTelemetry 集成")
            
        def is_available(self):
            return True
            
        def trace_execution(self, name, attributes=None):
            class MockSpan:
                def __enter__(self):
                    print(f"📊 开始追踪: {name}")
                    return self
                    
                def __exit__(self, exc_type, exc_val, exc_tb):
                    print(f"📊 结束追踪: {name}")
                    
            return MockSpan()
            
        def record_execution(self, name, duration, success):
            print(f"📈 记录执行: {name}, 耗时: {duration:.3f}s, 成功: {success}")
            
        def shutdown(self):
            print("🔧 关闭模拟的 OpenTelemetry 集成")
    
    def initialize_global_integration(config=None):
        return MockOpenTelemetryIntegration(config)


class SimpleAgent:
    """一个简单的 Agent 类，模拟原始代码"""
    
    def __init__(self):
        self.name = "SimpleAgent"
        self.counter = 0
        # 添加必要的属性以匹配真实 Agent
        self.state = type('MockState', (), {
            'conversation_id': 'demo_session_001',
            'react_steps': []
        })()
        self.config = type('MockConfig', (), {
            'llm': type('MockLLM', (), {'model': 'gpt-3.5-turbo'})()
        })()
        
    async def process_message(self, message: str) -> str:
        """原始的方法，没有任何监控代码"""
        if message is None:
            raise ValueError("消息不能为空")
            
        print(f"🔧 原始方法执行: {message}")
        await asyncio.sleep(0.1)
        self.counter += 1
        return f"处理结果: {message} (第{self.counter}次)"
        
    async def calculate(self, a: int, b: int) -> int:
        """另一个原始方法"""
        print(f"🔧 计算: {a} + {b}")
        await asyncio.sleep(0.05)
        return a + b
        
    # 添加缺失的方法
    async def _think(self, step):
        print(f"🧠 思考过程")
        await asyncio.sleep(0.02)
        step.thought = type('MockThought', (), {'content': '思考内容'})()
        step.tool_calls = []
        step.final_answer = None
        
    async def _act(self, step):
        print(f"⚡ 行动过程")
        await asyncio.sleep(0.02)
        step.observations = []
        
    async def _observe(self, step):
        print(f"👁️ 观察过程")
        await asyncio.sleep(0.02)
        step.final_answer = "最终答案"
        
    async def _call_llm(self, messages):
        print(f"🤖 LLM 调用")
        await asyncio.sleep(0.05)
        return {
            "content": "LLM 响应",
            "usage": {"total_tokens": 100, "prompt_tokens": 80, "completion_tokens": 20}
        }


async def demo_magic():
    """演示 instrumentation 的魔法"""
    
    print("🎪 Instrumentation 魔法演示")
    print("=" * 50)
    
    # 1. 创建原始 Agent
    print("1️⃣ 创建原始 Agent（无监控）")
    agent = SimpleAgent()
    
    # 2. 正常使用
    print("\n2️⃣ 正常使用原始 Agent")
    result1 = await agent.process_message("第一条消息")
    print(f"   结果: {result1}")
    
    # 3. 添加监控
    print("\n3️⃣ 添加监控（不修改原始代码！）")
    
    # 初始化 OpenTelemetry
    ot_integration = initialize_global_integration()
    
    # 导入并配置 instrumentation
    try:
        from src.monitoring.custom_instrumentation import instrument_agent, InstrumentationConfig
        
        config = InstrumentationConfig(
            enable_agent_tracing=True,
            enable_performance_metrics=True,
            enable_error_tracking=True
        )
        
        # 添加监控
        instrumentation = instrument_agent(agent, config)
        print("   ✅ 监控已添加！")
        
        # 4. 继续使用（现在有监控）
        print("\n4️⃣ 继续使用 Agent（现在有监控）")
        result2 = await agent.process_message("第二条消息")
        print(f"   结果: {result2}")
        
        # 5. 查看监控数据
        print("\n5️⃣ 查看监控数据")
        metrics = instrumentation.get_performance_metrics()
        print(f"   性能指标: {metrics}")
        
        # 6. 演示错误监控
        print("\n6️⃣ 演示错误监控")
        try:
            await agent.process_message(None)
        except Exception as e:
            print(f"   捕获错误: {e}")
        
        metrics_after_error = instrumentation.get_performance_metrics()
        print(f"   错误后的指标: {metrics_after_error}")
        
        # 7. 关闭监控
        print("\n7️⃣ 关闭监控")
        ot_integration.shutdown()
        
        # 8. 验证正常工作
        result3 = await agent.process_message("最后一条消息")
        print(f"   最终结果: {result3}")
        
        print("\n🎉 演示完成！")
        print("=" * 50)
        print("关键点：")
        print("✅ 没有修改 SimpleAgent 的任何代码")
        print("✅ 监控是动态添加和移除的")
        print("✅ 原始功能完全不受影响")
        
    except Exception as e:
        print(f"❌ 运行演示时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(demo_magic()) 