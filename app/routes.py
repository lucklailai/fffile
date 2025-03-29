import os
import uuid
import json
import datetime
from flask import Blueprint, request, jsonify, send_from_directory, render_template, current_app, url_for, abort, send_file
from werkzeug.utils import safe_join

main_bp = Blueprint('main', __name__)

@main_bp.before_app_request
def log_request_info():
    """记录请求详细信息"""
    print(f"[{datetime.datetime.now()}] 请求: {request.method} {request.path}")
    print(f"  端点: {request.endpoint}")
    print(f"  远程地址: {request.remote_addr}")
    if request.headers:
        print(f"  请求头: {dict(request.headers)}")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def verify_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return False
    token = auth_header.split(' ')[1]
    return token in current_app.config['AUTH_TOKENS']

@main_bp.before_request
def check_auth():
    # 记录检查认证
    print(f"[{datetime.datetime.now()}] 检查认证: {request.endpoint}")
    
    # 主页、静态资源和文件下载不需要认证
    if request.endpoint == 'main.index' or request.endpoint == 'static' or \
       request.endpoint == 'main.download_file' or request.endpoint == 'main.simple_download' or \
       request.endpoint == 'main.test_file_access' or request.endpoint == 'main.public_download':
        print("  跳过认证")
        return
    
    if not verify_token():
        print("  认证失败")
        return jsonify({'error': '未授权访问'}), 401
    
    print("  认证成功")

@main_bp.route('/')
def index():
    # 加载配置获取当前设置
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return render_template('index.html', 
                           max_file_size=config['upload']['max_file_size'],
                           allowed_extensions=config['upload']['allowed_extensions'],
                           tokens=config['auth']['tokens'])

@main_bp.route('/api/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 创建唯一文件夹用于本次上传
    upload_id = str(uuid.uuid4())
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_id)
    os.makedirs(upload_folder, exist_ok=True)
    
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = file.filename
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            # 返回文件URLs和物理路径
            file_url = url_for('main.public_download', upload_id=upload_id, filename=filename, _external=True)
            print(f"生成的URL: {file_url}")
            print(f"保存的文件路径: {file_path}")
            
            uploaded_files.append({
                'filename': filename,
                'url': file_url,
                'physical_path': os.path.abspath(file_path)
            })
    
    if not uploaded_files:
        return jsonify({'error': '没有符合条件的文件被上传'}), 400
    
    return jsonify({
        'message': '文件上传成功',
        'upload_id': upload_id,
        'files': uploaded_files
    })

@main_bp.route('/api/files/<upload_id>/<filename>')
def download_file(upload_id, filename):
    print(f"尝试访问文件: upload_id={upload_id}, filename={filename}")
    print(f"UPLOAD_FOLDER配置: {current_app.config['UPLOAD_FOLDER']}")
    
    try:
        # 使用safe_join防止目录遍历漏洞
        upload_dir = current_app.config['UPLOAD_FOLDER']
        target_dir = safe_join(upload_dir, upload_id)
        target_file = safe_join(target_dir, filename)
        
        print(f"构建的文件路径: {target_file}")
        
        if not os.path.exists(target_dir):
            print(f"目录不存在: {target_dir}")
            return jsonify({'error': '上传目录不存在'}), 404
            
        if not os.path.isfile(target_file):
            print(f"文件不存在: {target_file}")
            return jsonify({'error': '文件不存在'}), 404
        
        print(f"找到文件，准备发送: {target_file}")
        
        # 使用send_file直接发送文件
        return send_file(
            target_file,
            as_attachment=False,
            download_name=filename
        )
    except Exception as e:
        print(f"下载文件时出错: {str(e)}")
        return jsonify({'error': f'下载文件时出错: {str(e)}'}), 500

@main_bp.route('/api/files/<upload_id>')
def list_files(upload_id):
    directory = os.path.join(current_app.config['UPLOAD_FOLDER'], upload_id)
    
    if not os.path.exists(directory):
        return jsonify({'error': '目录不存在'}), 404
    
    files = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_url = url_for('main.public_download', upload_id=upload_id, filename=filename, _external=True)
            files.append({
                'filename': filename,
                'url': file_url,
                'physical_path': os.path.abspath(file_path),
                'size': os.path.getsize(file_path)
            })
    
    return jsonify({
        'upload_id': upload_id,
        'files': files
    })

@main_bp.route('/api/config', methods=['GET'])
def get_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 安全起见，不返回认证令牌
    if 'auth' in config:
        del config['auth']
    
    return jsonify(config)

@main_bp.route('/api/config', methods=['POST'])
def update_config():
    data = request.json
    
    if not data:
        return jsonify({'error': '无效的请求数据'}), 400
    
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.json')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 更新配置（仅允许更新某些字段）
    if 'upload' in data:
        if 'max_file_size' in data['upload']:
            config['upload']['max_file_size'] = data['upload']['max_file_size']
        if 'allowed_extensions' in data['upload']:
            config['upload']['allowed_extensions'] = data['upload']['allowed_extensions']
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    
    # 更新应用程序配置
    current_app.config.update(
        MAX_CONTENT_LENGTH=config['upload']['max_file_size'] * 1024 * 1024,
        ALLOWED_EXTENSIONS=set(config['upload']['allowed_extensions'])
    )
    
    return jsonify({'message': '配置已更新', 'config': config})

@main_bp.route('/api/test-file/<upload_id>/<filename>')
def test_file_access(upload_id, filename):
    """测试路由，用于诊断文件访问问题"""
    upload_dir = current_app.config['UPLOAD_FOLDER']
    target_dir = os.path.join(upload_dir, upload_id)
    target_file = os.path.join(target_dir, filename)
    
    result = {
        "config_upload_folder": upload_dir,
        "requested_upload_id": upload_id,
        "requested_filename": filename,
        "target_dir": target_dir,
        "target_file": target_file,
        "target_dir_exists": os.path.exists(target_dir),
        "target_file_exists": os.path.exists(target_file) and os.path.isfile(target_file),
        "file_stats": None
    }
    
    if result["target_file_exists"]:
        stats = os.stat(target_file)
        result["file_stats"] = {
            "size": stats.st_size,
            "created": stats.st_ctime,
            "modified": stats.st_mtime,
            "permissions": oct(stats.st_mode)[-3:]
        }
    
    return jsonify(result)

@main_bp.route('/api/simple-download/<upload_id>/<filename>')
def simple_download(upload_id, filename):
    """极简的文件下载路由"""
    try:
        upload_dir = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_dir, upload_id, filename)
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({"error": "文件不存在", "path": file_path}), 404
            
        return send_file(
            file_path,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/public/download/<upload_id>/<filename>')
def public_download(upload_id, filename):
    """公共下载接口，不需要认证"""
    try:
        upload_dir = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_dir, upload_id, filename)
        
        print(f"尝试下载文件: {file_path}")
        print(f"文件存在: {os.path.exists(file_path)}")
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({"error": "文件不存在", "path": file_path}), 404
            
        return send_file(
            file_path,
            mimetype='application/octet-stream',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        print(f"下载文件出错: {str(e)}")
        return jsonify({"error": str(e)}), 500 