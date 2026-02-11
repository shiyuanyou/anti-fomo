#!/usr/bin/env python3
"""
Anti-FOMO 运行脚本

Usage:
    python run.py            # 单次波动检查
    python run.py schedule   # 每日定时检查

资产配置已迁移至 Web 工具：python serve.py
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from main import main

if __name__ == '__main__':
    main()
