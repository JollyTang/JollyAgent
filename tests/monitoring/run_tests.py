#!/usr/bin/env python3
"""
监控模块测试运行脚本

运行所有监控相关的测试
"""

import sys
import os
import unittest

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def run_monitoring_tests():
    """运行监控模块的所有测试"""
    # 发现并运行测试
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='*_test.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_monitoring_tests()
    sys.exit(0 if success else 1) 