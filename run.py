#!/usr/bin/env python3
"""
Anti-FOMO 运行脚本
"""
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from main import main
from asset_configurator import run_asset_configurator

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "configure":
        run_asset_configurator()
    else:
        main()
