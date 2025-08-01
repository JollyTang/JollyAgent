#!/usr/bin/env python3
"""JollyAgent CLI 入口点."""

import sys
import os

# 添加src目录到Python路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 添加项目根目录到Python路径
project_root = os.path.dirname(__file__)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """主入口函数."""
    try:
        from cli.cli import app
        app()
    except ImportError as e:
        print(f"导入错误: {e}")
        print(f"当前Python路径: {sys.path}")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 