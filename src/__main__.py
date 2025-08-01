#!/usr/bin/env python3
"""JollyAgent CLI 入口点."""

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

def main():
    """CLI入口点."""
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