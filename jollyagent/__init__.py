#!/usr/bin/env python3
"""JollyAgent CLI 入口点."""

import sys
import os

def main():
    """主入口函数."""
    try:
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(__file__))
        
        # 添加src目录到Python路径
        src_dir = os.path.join(project_root, 'src')
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        
        # 添加项目根目录到Python路径
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # 导入并运行CLI，使用绝对导入
        from src.cli.cli import app
        app()
    except ImportError as e:
        print(f"导入错误: {e}")
        print(f"当前Python路径: {sys.path}")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1) 