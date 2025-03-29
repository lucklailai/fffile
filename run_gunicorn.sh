#!/bin/bash

# 激活虚拟环境
source venv/bin/activate

# 创建日志目录
mkdir -p logs

# 杀死正在运行的进程
pkill -f gunicorn || true

# 加载配置
CONFIG_FILE="app/config/config.json"
HOST=$(cat $CONFIG_FILE | grep -o '"host": "[^"]*"' | cut -d'"' -f4)
PORT=$(cat $CONFIG_FILE | grep -o '"port": [0-9]*' | cut -d':' -f2 | tr -d ' ')

# 启动Gunicorn服务 - 使用配置文件中的host和port
gunicorn --bind=${HOST}:${PORT} \
    --workers=4 \
    --worker-class=sync \
    --access-logfile=logs/access.log \
    --error-logfile=logs/error.log \
    server:app 