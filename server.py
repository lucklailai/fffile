import os
import json
import sys

# 确保当前目录在模块搜索路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# 创建Flask应用实例
app = create_app()

if __name__ == '__main__':
    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), 'app', 'config', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    host = config['server']['host']
    port = config['server']['port']
    debug = config['server']['debug']
    
    app.run(host=host, port=port, debug=debug) 