# -*- coding: utf-8 -*-

import sys
import os

env = os.environ.get('DEPLOY_ENV', None)
if len(sys.argv) > 1:
    env = sys.argv[1]
if env in ['test', 'pre', 'prd']:
    ENV = str(env)
else:
    ENV = 'test'
    
# Cluster Reload 时间间隔(秒)
SPAN_TIME = 300

# 证书过期时间间隔(秒)
SPAN_CERT = 60 * 60 * 24

# 证书过期通知人员邮件
RECEIVERDICT = {
    # 测试
    'test': 'test@aa.com',
    # 测试
    'pre': '',
    # 科技
    'prd': '',
}
RECEIVER = RECEIVERDICT[ENV]

# FLASK CONFIG
FLK = {
    'test': {"PORT": 8081, "Debug": True},
    'pre': {"PORT": 8081, "Debug": False},
    'prd': {"PORT": 8081, "Debug": False}
}

# DNS Resolver
# test环境dns为办公网DNS
DNS = {
    "test": ['8.8.8.8'],
    "pre": ['8.8.8.8'],
    'prd': ['8.8.8.8']
}

# MYSQL CONFIG
MYSQL_CONFIG = {
    'test': 'mysql://root:WA@1.3.2.1:3306/waf_v4?charset=utf8mb4',
    'pre': '',
    'prd': ''
}

# REDIS_CONFIG
REDIS_CONFIG = {
    'test': {
        'host': '1.2.2.1',
        'port': 6379,
        'password': None,
        'db': 1
    },
    'pre': {},
    'prd': {},
}

# auth error
ERROR_COUNT = 3
AUTH_SPAN_TIME = 1  # 分钟
