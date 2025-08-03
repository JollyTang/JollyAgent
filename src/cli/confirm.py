"""用户确认机制模块."""

import asyncio
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm, Prompt
from rich.text import Text
from rich.syntax import Syntax

from src.agent import ToolCall

console = Console()


class UserConfirmation:
    """用户确认管理器."""
    
    def __init__(self, auto_confirm: bool = False):
        """初始化确认管理器.
        
        Args:
            auto_confirm: 是否自动确认所有操作
        """
        self.auto_confirm = auto_confirm
        self.confirmation_history: List[Dict[str, Any]] = []
    
    async def confirm_tool_calls(self, tool_calls: List[ToolCall], step_info: Optional[str] = None) -> List[ToolCall]:
        """确认工具调用.
        
        Args:
            tool_calls: 工具调用列表
            step_info: 步骤信息
            
        Returns:
            确认后的工具调用列表
        """
        if not tool_calls:
            return []
        
        if self.auto_confirm:
            console.print("[yellow]自动确认模式：所有工具调用将被执行[/yellow]")
            return tool_calls
        
        # 显示工具调用信息
        self._display_tool_calls(tool_calls, step_info)
        
        # 获取用户确认
        confirmed_calls = []
        for i, tool_call in enumerate(tool_calls):
            if await self._confirm_single_tool_call(tool_call, i + 1, len(tool_calls)):
                confirmed_calls.append(tool_call)
            else:
                console.print(f"[red]跳过工具调用: {tool_call.name}[/red]")
        
        return confirmed_calls
    
    def _display_tool_calls(self, tool_calls: List[ToolCall], step_info: Optional[str] = None):
        """显示工具调用信息."""
        console.print("\n" + "="*50)
        console.print("[bold blue]🔧 工具调用确认[/bold blue]")
        
        if step_info:
            console.print(f"[dim]{step_info}[/dim]")
        
        # 简化显示，不使用复杂表格
        for i, tool_call in enumerate(tool_calls, 1):
            args_str = self._format_arguments_simple(tool_call.arguments)
            description = self._get_tool_description(tool_call.name)
            
            console.print(f"\n[bold]工具 {i}:[/bold] {tool_call.name}")
            console.print(f"[dim]描述:[/dim] {description}")
            console.print(f"[dim]参数:[/dim] {args_str}")
        
        console.print("="*50)
    
    async def _confirm_single_tool_call(self, tool_call: ToolCall, index: int, total: int) -> bool:
        """确认单个工具调用."""
        console.print(f"\n[bold]工具调用 {index}/{total}:[/bold] {tool_call.name}")
        
        # 显示简化信息
        args_str = self._format_arguments_simple(tool_call.arguments)
        description = self._get_tool_description(tool_call.name)
        
        console.print(f"[dim]描述:[/dim] {description}")
        console.print(f"[dim]参数:[/dim] {args_str}")
        
        # 获取用户选择
        while True:
            choice = Prompt.ask(
                "确认执行此工具调用？",
                choices=["y", "n", "a", "s", "d", "h"],
                default="y"
            )
            
            if choice == "y":
                return True
            elif choice == "n":
                return False
            elif choice == "a":
                # 确认所有
                self.auto_confirm = True
                console.print("[yellow]已启用自动确认模式[/yellow]")
                return True
            elif choice == "s":
                # 跳过所有
                console.print("[yellow]跳过所有剩余工具调用[/yellow]")
                return False
            elif choice == "d":
                # 显示详细信息
                self._display_tool_call_details_simple(tool_call)
                continue
            elif choice == "h":
                # 显示帮助
                self._show_help()
                continue
    
    def _display_tool_call_details_simple(self, tool_call: ToolCall):
        """显示简化的工具调用详细信息."""
        console.print(f"\n[bold green]工具名称:[/bold green] {tool_call.name}")
        console.print(f"[bold yellow]参数详情:[/bold yellow]")
        
        for key, value in tool_call.arguments.items():
            if isinstance(value, str):
                console.print(f"  {key}: {value}")
            else:
                console.print(f"  {key}: {value}")
        
        console.print(f"[bold cyan]工具描述:[/bold cyan] {self._get_tool_description(tool_call.name)}")
        console.print(f"[bold red]安全警告:[/bold red] {self._get_tool_safety_warning(tool_call.name)}")
    
    def _format_arguments(self, arguments: Dict[str, Any]) -> str:
        """格式化参数显示."""
        if not arguments:
            return "无参数"
        
        formatted = []
        for key, value in arguments.items():
            if isinstance(value, str) and len(value) > 50:
                formatted.append(f"{key}: {value[:50]}...")
            else:
                formatted.append(f"{key}: {value}")
        
        return "\n".join(formatted)
    
    def _format_arguments_detailed(self, arguments: Dict[str, Any]) -> str:
        """格式化详细参数显示."""
        if not arguments:
            return "无参数"
        
        formatted = []
        for key, value in arguments.items():
            if isinstance(value, str):
                # 使用语法高亮
                syntax = Syntax(str(value), "python", theme="monokai")
                formatted.append(f"[bold]{key}:[/bold]\n{syntax}")
            else:
                formatted.append(f"[bold]{key}:[/bold] {value}")
        
        return "\n\n".join(formatted)
    
    def _format_arguments_simple(self, arguments: Dict[str, Any]) -> str:
        """简化参数格式化."""
        if not arguments:
            return "无参数"
        
        formatted = []
        for key, value in arguments.items():
            if isinstance(value, str) and len(value) > 30:
                formatted.append(f"{key}: {value[:30]}...")
            else:
                formatted.append(f"{key}: {value}")
        
        return ", ".join(formatted)
    
    def _get_tool_description(self, tool_name: str) -> str:
        """获取工具描述."""
        descriptions = {
            "run_shell": "执行Shell命令，可以运行系统命令和脚本",
            "read_file": "读取文件内容，支持文本和二进制文件",
            "write_file": "写入文件内容，可以创建或修改文件",
            "mcp_client": "MCP协议客户端，用于与外部服务通信",
            "codebase_search": "代码库搜索，查找相关代码片段",
            "grep_search": "文本搜索，使用正则表达式查找内容",
            "file_search": "文件搜索，根据文件名模糊匹配",
            "read_file": "读取文件内容",
            "edit_file": "编辑文件内容",
            "delete_file": "删除文件",
            "run_terminal_cmd": "执行终端命令"
        }
        
        return descriptions.get(tool_name, "未知工具")
    
    def _get_tool_safety_warning(self, tool_name: str) -> str:
        """获取工具安全警告."""
        warnings = {
            "run_shell": "⚠️  此工具可以执行系统命令，请确保命令安全",
            "write_file": "⚠️  此工具可以修改文件，请确保路径正确",
            "delete_file": "⚠️  此工具可以删除文件，操作不可逆",
            "run_terminal_cmd": "⚠️  此工具可以执行终端命令，请确保命令安全"
        }
        
        return warnings.get(tool_name, "⚠️  请谨慎使用此工具")
    
    def _show_help(self):
        """显示帮助信息."""
        help_text = """
[bold]确认选项:[/bold]
• [green]y[/green] - 确认执行此工具调用
• [red]n[/red] - 拒绝执行此工具调用
• [yellow]a[/yellow] - 确认所有剩余工具调用（启用自动确认）
• [yellow]s[/yellow] - 跳过所有剩余工具调用
• [cyan]d[/cyan] - 显示详细信息
• [cyan]h[/cyan] - 显示此帮助信息
        """
        
        console.print(help_text)
    
    def add_to_history(self, tool_call: ToolCall, confirmed: bool, reason: str = ""):
        """添加到确认历史."""
        self.confirmation_history.append({
            "tool_name": tool_call.name,
            "arguments": tool_call.arguments,
            "confirmed": confirmed,
            "reason": reason,
            "timestamp": asyncio.get_event_loop().time()
        })
    
    def get_history_summary(self) -> Dict[str, Any]:
        """获取确认历史摘要."""
        if not self.confirmation_history:
            return {"total": 0, "confirmed": 0, "rejected": 0}
        
        total = len(self.confirmation_history)
        confirmed = sum(1 for item in self.confirmation_history if item["confirmed"])
        rejected = total - confirmed
        
        return {
            "total": total,
            "confirmed": confirmed,
            "rejected": rejected,
            "confirmation_rate": confirmed / total if total > 0 else 0
        }
    
    def display_history_summary(self):
        """显示确认历史摘要."""
        summary = self.get_history_summary()
        
        if summary["total"] == 0:
            console.print("[dim]暂无确认历史[/dim]")
            return
        
        table = Table(title="确认历史摘要")
        table.add_column("指标", style="cyan")
        table.add_column("数值", style="green")
        
        table.add_row("总工具调用数", str(summary["total"]))
        table.add_row("已确认", str(summary["confirmed"]))
        table.add_row("已拒绝", str(summary["rejected"]))
        table.add_row("确认率", f"{summary['confirmation_rate']:.1%}")
        
        console.print(table) 