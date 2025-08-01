"""命令撤销功能模块."""

import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()


@dataclass
class UndoAction:
    """撤销动作数据类."""
    
    id: str
    action_type: str
    description: str
    timestamp: datetime
    data: Dict[str, Any]
    can_undo: bool = True
    undo_function: Optional[str] = None  # 存储函数名称，不存储函数对象


class UndoManager:
    """撤销管理器."""
    
    def __init__(self, history_file: Optional[str] = None, max_history: int = 50):
        """初始化撤销管理器.
        
        Args:
            history_file: 历史文件路径
            max_history: 最大历史记录数
        """
        self.history_file = history_file or "undo_history.json"
        self.max_history = max_history
        self.history: List[UndoAction] = []
        self.undo_functions: Dict[str, Callable] = {}
        
        # 加载历史记录
        self._load_history()
    
    def register_undo_function(self, action_type: str, undo_func: Callable):
        """注册撤销函数.
        
        Args:
            action_type: 动作类型
            undo_func: 撤销函数
        """
        self.undo_functions[action_type] = undo_func
    
    def add_action(self, action_type: str, description: str, data: Dict[str, Any], 
                   can_undo: bool = True, undo_function: Optional[str] = None) -> str:
        """添加动作到历史记录.
        
        Args:
            action_type: 动作类型
            description: 动作描述
            data: 动作数据
            can_undo: 是否可以撤销
            undo_function: 撤销函数名称
            
        Returns:
            动作ID
        """
        import uuid
        
        action_id = str(uuid.uuid4())
        action = UndoAction(
            id=action_id,
            action_type=action_type,
            description=description,
            timestamp=datetime.now(),
            data=data,
            can_undo=can_undo,
            undo_function=undo_function
        )
        
        self.history.append(action)
        
        # 限制历史记录数量
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        # 保存到文件
        self._save_history()
        
        return action_id
    
    async def undo_last_action(self) -> bool:
        """撤销最后一个动作.
        
        Returns:
            是否成功撤销
        """
        if not self.history:
            console.print("[yellow]没有可撤销的动作[/yellow]")
            return False
        
        # 找到最后一个可撤销的动作
        for action in reversed(self.history):
            if action.can_undo:
                return await self._undo_action(action)
        
        console.print("[yellow]没有可撤销的动作[/yellow]")
        return False
    
    async def undo_action_by_id(self, action_id: str) -> bool:
        """根据ID撤销动作.
        
        Args:
            action_id: 动作ID
            
        Returns:
            是否成功撤销
        """
        for action in self.history:
            if action.id == action_id:
                if not action.can_undo:
                    console.print(f"[red]动作 '{action.description}' 不可撤销[/red]")
                    return False
                return await self._undo_action(action)
        
        console.print(f"[red]未找到动作ID: {action_id}[/red]")
        return False
    
    async def _undo_action(self, action: UndoAction) -> bool:
        """执行撤销动作.
        
        Args:
            action: 要撤销的动作
            
        Returns:
            是否成功撤销
        """
        try:
            console.print(f"[yellow]正在撤销: {action.description}[/yellow]")
            
            # 如果有注册的撤销函数，调用它
            if action.undo_function and action.undo_function in self.undo_functions:
                undo_func = self.undo_functions[action.undo_function]
                if asyncio.iscoroutinefunction(undo_func):
                    await undo_func(action.data)
                else:
                    undo_func(action.data)
            
            # 从历史记录中移除
            self.history.remove(action)
            self._save_history()
            
            console.print(f"[green]成功撤销: {action.description}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]撤销失败: {e}[/red]")
            return False
    
    def show_history(self, limit: int = 10):
        """显示历史记录.
        
        Args:
            limit: 显示数量限制
        """
        if not self.history:
            console.print("[dim]暂无历史记录[/dim]")
            return
        
        table = Table(title="撤销历史记录")
        table.add_column("序号", style="cyan", justify="center")
        table.add_column("时间", style="blue")
        table.add_column("类型", style="green")
        table.add_column("描述", style="white")
        table.add_column("可撤销", style="yellow", justify="center")
        table.add_column("ID", style="dim")
        
        # 显示最近的记录
        recent_history = self.history[-limit:]
        
        for i, action in enumerate(recent_history, 1):
            table.add_row(
                str(i),
                action.timestamp.strftime("%H:%M:%S"),
                action.action_type,
                action.description[:50] + "..." if len(action.description) > 50 else action.description,
                "✓" if action.can_undo else "✗",
                action.id[:8] + "..."
            )
        
        console.print(table)
    
    def clear_history(self):
        """清空历史记录."""
        if Confirm.ask("确定要清空所有历史记录吗？"):
            self.history.clear()
            self._save_history()
            console.print("[green]历史记录已清空[/green]")
    
    def _save_history(self):
        """保存历史记录到文件."""
        try:
            # 转换历史记录为可序列化的格式
            history_data = []
            for action in self.history:
                action_dict = asdict(action)
                # 将datetime转换为字符串
                action_dict['timestamp'] = action.timestamp.isoformat()
                history_data.append(action_dict)
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            console.print(f"[red]保存历史记录失败: {e}[/red]")
    
    def _load_history(self):
        """从文件加载历史记录."""
        try:
            if not os.path.exists(self.history_file):
                return
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
            
            for action_dict in history_data:
                # 将字符串转换回datetime
                action_dict['timestamp'] = datetime.fromisoformat(action_dict['timestamp'])
                action = UndoAction(**action_dict)
                self.history.append(action)
                
        except Exception as e:
            console.print(f"[red]加载历史记录失败: {e}[/red]")


# 预定义的撤销函数
async def undo_file_write(data: Dict[str, Any]):
    """撤销文件写入操作."""
    file_path = data.get('file_path')
    original_content = data.get('original_content')
    
    if file_path and original_content is not None:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            console.print(f"[green]已恢复文件: {file_path}[/green]")
        except Exception as e:
            console.print(f"[red]恢复文件失败: {e}[/red]")


async def undo_file_delete(data: Dict[str, Any]):
    """撤销文件删除操作."""
    file_path = data.get('file_path')
    original_content = data.get('original_content')
    
    if file_path and original_content is not None:
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            console.print(f"[green]已恢复删除的文件: {file_path}[/green]")
        except Exception as e:
            console.print(f"[red]恢复文件失败: {e}[/red]")


async def undo_shell_command(data: Dict[str, Any]):
    """撤销Shell命令操作."""
    command = data.get('command')
    console.print(f"[yellow]无法自动撤销Shell命令: {command}[/yellow]")
    console.print("[yellow]请手动执行相应的撤销命令[/yellow]")


# 全局撤销管理器实例
_undo_manager: Optional[UndoManager] = None


def get_undo_manager() -> UndoManager:
    """获取全局撤销管理器实例."""
    global _undo_manager
    if _undo_manager is None:
        _undo_manager = UndoManager()
        
        # 注册预定义的撤销函数
        _undo_manager.register_undo_function("file_write", undo_file_write)
        _undo_manager.register_undo_function("file_delete", undo_file_delete)
        _undo_manager.register_undo_function("shell_command", undo_shell_command)
    
    return _undo_manager


def reset_undo_manager():
    """重置全局撤销管理器实例."""
    global _undo_manager
    _undo_manager = None 