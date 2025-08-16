"""
Instrumentation 魔法演示

展示如何在不修改原始代码的情况下添加全面的监控功能。
"""

import asyncio
import time
from src.monitoring.custom_instrumentation import instrument_agent, InstrumentationConfig

# 尝试导入 OpenTelemetry，如果不存在则使用模拟
try:
    from src.monitoring.opentelemetry_integration import initialize_global_integration
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    print("⚠️  OpenTelemetry 未安装，将使用模拟模式")
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
        await asyncio.sleep(0.1)  # 模拟处理时间
        self.counter += 1
        return f"处理结果: {message} (第{self.counter}次)"
        
    async def calculate(self, a: int, b: int) -> int:
        """另一个原始方法"""
        print(f"🔧 计算: {a} + {b}")
        await asyncio.sleep(0.05)
        return a + b
        
    # 添加缺失的方法以匹配真实 Agent 的接口
    async def _think(self, step):
        """模拟思考过程"""
        print(f"🧠 思考过程")
        await asyncio.sleep(0.02)
        step.thought = type('MockThought', (), {'content': '这是一个思考过程'})()
        step.tool_calls = []
        step.final_answer = None
        
    async def _act(self, step):
        """模拟行动过程"""
        print(f"⚡ 行动过程")
        await asyncio.sleep(0.02)
        step.observations = []
        
    async def _observe(self, step):
        """模拟观察过程"""
        print(f"👁️ 观察过程")
        await asyncio.sleep(0.02)
        step.final_answer = "最终答案"
        
    async def _call_llm(self, messages):
        """模拟 LLM 调用"""
        print(f"🤖 LLM 调用")
        await asyncio.sleep(0.05)
        return {
            "content": "LLM 响应内容",
            "usage": {
                "total_tokens": 100,
                "prompt_tokens": 80,
                "completion_tokens": 20
            }
        }


async def demo_magic():
    """演示 instrumentation 的魔法"""
    
    print("🎪 Instrumentation 魔法演示")
    print("=" * 50)
    
    # 1. 创建原始 Agent（没有任何监控代码）
    print("1️⃣ 创建原始 Agent（无监控）")
    agent = SimpleAgent()
    
    # 2. 正常使用原始 Agent
    print("\n2️⃣ 正常使用原始 Agent")
    result1 = await agent.process_message("第一条消息")
    print(f"   结果: {result1}")
    
    result2 = await agent.calculate(10, 20)
    print(f"   计算: {result2}")
    
    # 3. 现在添加监控（不修改任何原始代码！）
    print("\n3️⃣ 添加监控（不修改原始代码！）")
    
    # 初始化 OpenTelemetry
    ot_integration = initialize_global_integration()
    
    # 创建监控配置
    config = InstrumentationConfig(
        enable_agent_tracing=True,
        enable_performance_metrics=True,
        enable_error_tracking=True
    )
    
    # 添加监控
    instrumentation = instrument_agent(agent, config)
    print("   ✅ 监控已添加！")
    
    # 4. 继续使用 Agent（现在有监控了）
    print("\n4️⃣ 继续使用 Agent（现在有监控）")
    result3 = await agent.process_message("第二条消息")
    print(f"   结果: {result3}")
    
    result4 = await agent.calculate(30, 40)
    print(f"   计算: {result4}")
    
    # 5. 查看监控数据
    print("\n5️⃣ 查看监控数据")
    metrics = instrumentation.get_performance_metrics()
    print(f"   性能指标: {metrics}")
    
    stats = instrumentation.get_statistics()
    print(f"   完整统计: {stats}")
    
    # 6. 演示错误监控
    print("\n6️⃣ 演示错误监控")
    try:
        # 故意制造一个错误
        await agent.process_message(None)  # 传入 None 会出错
    except Exception as e:
        print(f"   捕获错误: {e}")
    
    # 查看错误统计
    metrics_after_error = instrumentation.get_performance_metrics()
    print(f"   错误后的指标: {metrics_after_error}")
    
    # 7. 关闭监控
    print("\n7️⃣ 关闭监控")
    ot_integration.shutdown()
    print("   ✅ 监控已关闭，Agent 继续正常工作")
    
    # 8. 验证 Agent 仍然正常工作
    result5 = await agent.process_message("最后一条消息")
    print(f"   最终结果: {result5}")
    
    print("\n🎉 演示完成！")
    print("=" * 50)
    print("关键点：")
    print("✅ 没有修改 SimpleAgent 的任何代码")
    print("✅ 监控是动态添加和移除的")
    print("✅ 原始功能完全不受影响")
    print("✅ 可以随时开启或关闭监控")


async def demo_comparison():
    """对比演示：有监控 vs 无监控"""
    
    print("\n🔄 对比演示：有监控 vs 无监控")
    print("=" * 50)
    
    # 创建两个相同的 Agent
    agent1 = SimpleAgent()  # 无监控
    agent2 = SimpleAgent()  # 有监控
    
    # 为 agent2 添加监控
    ot_integration = initialize_global_integration()
    config = InstrumentationConfig(enable_agent_tracing=True, enable_performance_metrics=True)
    instrumentation = instrument_agent(agent2, config)
    
    print("Agent1 (无监控) vs Agent2 (有监控)")
    print("-" * 30)
    
    # 执行相同操作
    for i in range(3):
        print(f"\n第 {i+1} 轮:")
        
        # Agent1 无监控
        start1 = time.time()
        result1 = await agent1.process_message(f"消息{i}")
        time1 = time.time() - start1
        print(f"  Agent1: {result1} (耗时: {time1:.3f}s)")
        
        # Agent2 有监控
        start2 = time.time()
        result2 = await agent2.process_message(f"消息{i}")
        time2 = time.time() - start2
        print(f"  Agent2: {result2} (耗时: {time2:.3f}s)")
        
        # 显示监控数据
        metrics = instrumentation.get_performance_metrics()
        print(f"  监控数据: {metrics}")
    
    print(f"\n结论:")
    print(f"✅ 功能完全相同: {result1 == result2}")
    print(f"✅ 性能影响很小: {abs(time1 - time2):.3f}s")
    print(f"✅ 获得了详细的监控数据")
    
    ot_integration.shutdown()


if __name__ == "__main__":
    # 运行魔法演示
    asyncio.run(demo_magic())
    
    # 运行对比演示
    asyncio.run(demo_comparison()) 