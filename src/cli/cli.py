"""JollyAgent CLI interface using Typer."""

import asyncio
import logging
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.console import Group
from rich.markdown import Markdown

from src.agent import get_agent, reset_agent
from src.config import get_config
from src.cli import get_undo_manager, get_cli_logger

# 创建Typer应用
app = typer.Typer(
    name="jollyagent",
    help="JollyAgent - ReAct AI Agent with tool calling and memory management",
    add_completion=False,
)

# 创建Rich控制台
console = Console()

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 改为WARNING级别，减少INFO日志
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def print_banner():
    """打印欢迎横幅."""
    banner = Text("🤖 JollyAgent", style="bold blue")
    subtitle = Text("ReAct AI Agent with Tool Calling & Memory", style="italic")
    
    panel = Panel(
        f"{banner}\n{subtitle}",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


def print_help():
    """打印帮助信息."""
    help_text = """
[bold]可用命令:[/bold]
• [green]chat[/green] - 开始与Agent对话
• [green]config[/green] - 查看当前配置
• [green]reset[/green] - 重置Agent状态
• [green]undo[/green] - 撤销操作
• [green]history[/green] - 查看撤销历史
• [green]help[/green] - 显示此帮助信息

[bold]示例:[/bold]
• jollyagent chat
• jollyagent chat --stream
• jollyagent chat --no-confirm
• jollyagent chat --auto-confirm
• jollyagent config
• jollyagent reset
• jollyagent undo
• jollyagent history
    """
    console.print(Panel(help_text, title="帮助", border_style="green"))


@app.command()
def chat(
    stream: bool = typer.Option(True, "--stream/--no-stream", help="启用流式输出"),
    conversation_id: Optional[str] = typer.Option(None, "--conversation-id", "-c", help="指定对话ID"),
    max_steps: int = typer.Option(10, "--max-steps", "-m", help="最大ReAct步骤数"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="详细输出模式"),
    enable_confirmation: bool = typer.Option(True, "--confirm/--no-confirm", help="启用用户确认机制"),
    auto_confirm: bool = typer.Option(False, "--auto-confirm", help="自动确认所有操作"),
    show_thoughts: bool = typer.Option(True, "--show-thoughts/--hide-thoughts", help="显示思考过程"),
    log_file: Optional[str] = typer.Option(None, "--log-file", help="日志文件路径")
):
    """开始与JollyAgent对话."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print_banner()
    console.print("\n[green]开始对话...[/green] (输入 'quit' 或 'exit' 退出)\n")
    
    # 显示模式信息
    mode_info = []
    if stream:
        mode_info.append("流式输出")
    if enable_confirmation and not auto_confirm:
        mode_info.append("用户确认")
    elif auto_confirm:
        mode_info.append("自动确认")
    if show_thoughts:
        mode_info.append("显示思考")
    if log_file:
        mode_info.append("日志记录")
    
    if mode_info:
        console.print(f"[dim]模式: {', '.join(mode_info)}[/dim]\n")
    
    # 运行异步对话
    asyncio.run(run_chat_session(
        stream, conversation_id, max_steps, verbose, 
        enable_confirmation, auto_confirm, show_thoughts, log_file
    ))


@app.command()
def config():
    """显示当前配置信息."""
    print_banner()
    
    try:
        config = get_config()
        
        table = Table(title="当前配置")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")
        
        # LLM配置
        table.add_row("LLM Base URL", config.llm.base_url)
        table.add_row("LLM Model", config.llm.model)
        table.add_row("Max Tokens", str(config.llm.max_tokens))
        table.add_row("Temperature", str(config.llm.temperature))
        
        # 记忆配置
        table.add_row("记忆目录", config.memory.persist_directory)
        table.add_row("向量维度", str(config.memory.embedding_dimension))
        table.add_row("索引类型", config.memory.index_type)
        table.add_row("嵌入模型", config.memory.embedding_model)
        table.add_row("分层记忆", str(config.memory.enable_layered_memory))
        
        # 工具配置
        table.add_row("启用Shell", str(config.tools.enable_shell))
        table.add_row("启用文件操作", str(config.tools.enable_file_ops))
        table.add_row("启用MCP", str(config.tools.enable_mcp))
        
        # 沙箱配置
        table.add_row("沙箱类型", config.sandbox.docker_image)
        table.add_row("内存限制", config.sandbox.memory_limit)
        table.add_row("网络访问", str(config.sandbox.enable_network))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]配置加载失败: {e}[/red]")


@app.command()
def reset():
    """重置Agent状态."""
    try:
        reset_agent()
        console.print("[green]Agent状态已重置[/green]")
    except Exception as e:
        console.print(f"[red]重置失败: {e}[/red]")


@app.command()
def undo(
    action_id: Optional[str] = typer.Option(None, "--id", "-i", help="指定动作ID"),
    last: bool = typer.Option(False, "--last", "-l", help="撤销最后一个动作")
):
    """撤销操作."""
    print_banner()
    
    try:
        undo_manager = get_undo_manager()
        
        if action_id:
            # 撤销指定ID的动作
            asyncio.run(undo_manager.undo_action_by_id(action_id))
        elif last:
            # 撤销最后一个动作
            asyncio.run(undo_manager.undo_last_action())
        else:
            # 显示历史记录并让用户选择
            undo_manager.show_history()
            
            if undo_manager.history:
                choice = Prompt.ask(
                    "选择要撤销的动作 (输入序号或 'q' 退出)",
                    default="q"
                )
                
                if choice.lower() != 'q':
                    try:
                        index = int(choice) - 1
                        if 0 <= index < len(undo_manager.history):
                            action = undo_manager.history[-(index + 1)]  # 从后往前数
                            asyncio.run(undo_manager.undo_action_by_id(action.id))
                        else:
                            console.print("[red]无效的序号[/red]")
                    except ValueError:
                        console.print("[red]请输入有效的数字[/red]")
        
    except Exception as e:
        console.print(f"[red]撤销操作失败: {e}[/red]")


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-l", help="显示数量限制"),
    clear: bool = typer.Option(False, "--clear", "-c", help="清空历史记录")
):
    """查看撤销历史记录."""
    print_banner()
    
    try:
        undo_manager = get_undo_manager()
        
        if clear:
            undo_manager.clear_history()
        else:
            undo_manager.show_history(limit)
        
    except Exception as e:
        console.print(f"[red]查看历史记录失败: {e}[/red]")


@app.command()
def help():
    """显示帮助信息."""
    print_help()


async def run_chat_session(
    stream: bool, 
    conversation_id: Optional[str], 
    max_steps: int, 
    verbose: bool,
    enable_confirmation: bool,
    auto_confirm: bool,
    show_thoughts: bool,
    log_file: Optional[str]
):
    """运行聊天会话."""
    # 初始化日志记录器
    cli_logger = get_cli_logger()
    if log_file:
        from src.cli import setup_cli_logging
        cli_logger = setup_cli_logging(log_file=log_file)
    
    # 初始化消息计数
    message_count = 0
    
    try:
        # 记录会话开始
        session_info = {
            "stream": stream,
            "conversation_id": conversation_id,
            "max_steps": max_steps,
            "verbose": verbose,
            "enable_confirmation": enable_confirmation,
            "auto_confirm": auto_confirm,
            "show_thoughts": show_thoughts
        }
        cli_logger.log_session_start(session_info)
        
        # 获取Agent实例
        agent = await get_agent()
        
        # 如果Agent没有确认管理器，重新创建
        if enable_confirmation and not hasattr(agent, 'confirmation_manager'):
            from src.cli import UserConfirmation
            agent.confirmation_manager = UserConfirmation(auto_confirm=auto_confirm)
        
        # 开始对话
        if conversation_id:
            state = await agent.start_conversation(conversation_id)
        else:
            state = await agent.start_conversation()
        
        console.print(f"[dim]对话ID: {state.conversation_id}[/dim]\n")
        
        # 显示特殊命令帮助
        console.print("[dim]特殊命令: 'undo' - 撤销操作, 'history' - 查看历史[/dim]\n")
        
        # 主对话循环
        while True:
            # 获取用户输入
            user_input = Prompt.ask("[bold cyan]你[/bold cyan]")
            
            # 记录用户输入
            cli_logger.log_user_input(user_input)
            
            # 检查退出命令
            if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                console.print("\n[yellow]结束对话...[/yellow]")
                break
            
            # 检查特殊命令
            if user_input.lower() == 'undo':
                undo_manager = get_undo_manager()
                success = await undo_manager.undo_last_action()
                cli_logger.log_undo_action("undo", "撤销最后一个动作", success)
                continue
            
            if user_input.lower() == 'history':
                undo_manager = get_undo_manager()
                undo_manager.show_history()
                continue
            
            if not user_input.strip():
                continue
            
            message_count += 1
            
            # 处理用户消息
            await process_user_message(
                agent, user_input, stream, max_steps, verbose, show_thoughts, cli_logger
            )
            
    except KeyboardInterrupt:
        console.print("\n[yellow]对话被中断[/yellow]")
        cli_logger.log_error("对话被用户中断")
    except Exception as e:
        console.print(f"[red]对话出错: {e}[/red]")
        cli_logger.log_error(f"对话出错: {e}", e)
        logger.exception("对话会话出错")
    finally:
        # 结束对话
        try:
            if 'agent' in locals():
                # 显示确认历史摘要
                if hasattr(agent, 'confirmation_manager') and agent.confirmation_manager:
                    agent.confirmation_manager.display_history_summary()
                
                summary = await agent.end_conversation()
                if summary:
                    console.print(f"\n[dim]对话摘要: {summary}[/dim]")
                
                # 记录会话结束
                session_summary = {
                    "message_count": message_count,
                    "conversation_id": state.conversation_id if 'state' in locals() else None,
                    "summary": summary
                }
                cli_logger.log_session_end(session_summary)
                
        except Exception as e:
            logger.exception("结束对话时出错")


async def process_user_message(
    agent, 
    user_input: str, 
    stream: bool, 
    max_steps: int, 
    verbose: bool,
    show_thoughts: bool,
    cli_logger
):
    """处理用户消息."""
    try:
        if stream:
            # 流式处理
            response = await process_message_stream(agent, user_input, max_steps, verbose, show_thoughts)
        else:
            # 非流式处理
            response = await process_message_simple(agent, user_input, max_steps, verbose, show_thoughts)
        
        # 记录Agent响应
        cli_logger.log_agent_response(response)
            
    except Exception as e:
        console.print(f"[red]处理消息失败: {e}[/red]")
        cli_logger.log_error(f"处理消息失败: {e}", e)
        logger.exception("处理用户消息时出错")


async def process_message_stream(
    agent, 
    user_input: str, 
    max_steps: int, 
    verbose: bool,
    show_thoughts: bool
):
    """流式处理消息."""
    # 添加用户消息
    agent.add_message("user", user_input)
    
    # 创建布局
    layout = Layout()
    layout.split_column(
        Layout(name="status", size=3),
        Layout(name="content", ratio=1)
    )
    
    # 显示思考过程
    with Live(layout, console=console, refresh_per_second=4) as live:
        try:
            # 更新状态
            layout["status"].update(Panel("🤔 思考中...", title="状态", border_style="blue"))
            
            # 调用Agent处理消息
            response = await agent.process_message(user_input)
            
            # 显示最终回答
            layout["content"].update(Panel(
                f"[bold green]Agent:[/bold green]\n{response}",
                title="回答",
                border_style="green"
            ))
            
            # 等待一下让用户看到结果
            await asyncio.sleep(1)
            
        except Exception as e:
            layout["status"].update(Panel(f"[red]处理失败: {e}[/red]", title="错误", border_style="red"))
            await asyncio.sleep(2)
    
    # 注释掉重复显示的回答，只保留框框中的显示
    # console.print(f"\n[bold green]Agent[/bold green]: {response}\n")
    return response


async def process_message_simple(
    agent, 
    user_input: str, 
    max_steps: int, 
    verbose: bool,
    show_thoughts: bool
):
    """简单处理消息（非流式）."""
    # 添加用户消息
    agent.add_message("user", user_input)
    
    # 显示处理状态
    with console.status("[bold green]处理中...", spinner="dots"):
        try:
            # 调用Agent处理消息
            response = await agent.process_message(user_input)
            
            # 显示最终回答
            console.print(f"\n[bold green]Agent[/bold green]: {response}\n")
            
            return response
            
        except Exception as e:
            console.print(f"[red]处理失败: {e}[/red]")
            raise e


def main():
    """主入口函数."""
    try:
        app()
    except Exception as e:
        console.print(f"[red]程序出错: {e}[/red]")
        logger.exception("程序执行出错")
        sys.exit(1)


if __name__ == "__main__":
    main() 