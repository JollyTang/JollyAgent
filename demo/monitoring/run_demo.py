#!/usr/bin/env python3
"""
监控模块演示运行脚本

运行监控功能的演示
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from integration_example import example_usage


def main():
    """运行演示"""
    print("=== JollyAgent 监控系统演示 ===")
    print()
    
    try:
        example_usage()
        print("\n演示完成！")
        return 0
    except Exception as e:
        print(f"\n演示失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main()) 