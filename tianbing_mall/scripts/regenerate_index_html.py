#!/usr/bin/env/ python

"""
脚本功能:手动生成所有SKU的静态detail html文件
"""
import sys

import os

# 添加系统导包路径
sys.path.insert(0, "../")
# 默认使用当天django的配置
if not os.getenv("DJANGO_SETTINGS_MODULE"):
    os.environ["DJANGO_SETTINGS_MODULE"] = "tianbing_mall.settings.dev"

# 让django初始化配置
import django
django.setup()

# 导入任务
from contents.crons import generate_static_index_html


if __name__ == '__main__':
    generate_static_index_html()