import os
import json
from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # 加载配置
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 确保上传路径是绝对路径
    upload_folder = config['upload']['upload_folder']
    if not os.path.isabs(upload_folder):
        upload_folder = os.path.abspath(upload_folder)
    
    app.config.update(
        MAX_CONTENT_LENGTH=config['upload']['max_file_size'] * 1024 * 1024,
        UPLOAD_FOLDER=upload_folder,
        ALLOWED_EXTENSIONS=set(config['upload']['allowed_extensions']),
        AUTH_TOKENS=set(config['auth']['tokens'])
    )
    
    print(f"配置的上传目录: {app.config['UPLOAD_FOLDER']}")
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app 