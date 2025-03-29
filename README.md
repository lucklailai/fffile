# 文件上传服务

一个简单而强大的文件上传服务应用，提供API接口和前端界面，支持文件上传、下载和管理。

## 功能特点

- 提供文件上传的API接口
- 提供文件访问、下载的API接口
- 提供文件在服务器上的物理路径
- 可以通过接口设置上传文件限制（文件大小、文件类型等）
- 提供简洁的前端示例页面
- 支持多个文件同时上传
- UUID目录命名，避免文件重名
- Bearer Token鉴权保护（文件下载接口除外）
- 支持开发环境和生产环境（Gunicorn）
- 所有配置均在配置文件中管理，包括服务器地址和端口

## 快速开始

### 安装依赖

项目使用Python虚拟环境，首次下载项目后需执行以下步骤：

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install flask flask-cors python-dotenv gunicorn pytest
```

### 运行服务

开发环境运行：

```bash
# 方式1：直接运行
./run.sh

# 方式2：手动运行
source venv/bin/activate
python app.py
```

生产环境运行 (使用Gunicorn)：

```bash
# 方式1：使用脚本
./run_gunicorn.sh

# 方式2：手动运行
source venv/bin/activate
gunicorn -c gunicorn_config.py wsgi:app
```

服务会根据配置文件中的设置运行，默认为 http://localhost:9012

> **注意**：开发环境使用Flask内置服务器运行时会有警告信息，这是正常的。生产环境请使用Gunicorn服务器（run_gunicorn.sh）。

## 配置说明

配置文件位于 `app/config/config.json`，可以修改以下配置项：

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 9012,
        "debug": false
    },
    "upload": {
        "max_file_size": 50,
        "allowed_extensions": ["jpg", "jpeg", "png", "pdf", "doc", "docx", "xls", "xlsx", "txt", "zip", "rar"],
        "upload_folder": "app/uploads"
    },
    "auth": {
        "tokens": [
            "zBEWv6K1NdS7Lnq8XmCjP9",
            "rA5pJ2TfH8kV3GxD6QbYc7"
        ]
    }
}
```

- `server`: 服务器配置
  - `host`: 绑定的主机地址（开发和生产环境都使用此设置）
  - `port`: 端口号（开发和生产环境都使用此设置）
  - `debug`: 是否启用调试模式（仅开发环境）
- `upload`: 上传设置
  - `max_file_size`: 最大文件大小（MB）
  - `allowed_extensions`: 允许的文件类型
  - `upload_folder`: 上传文件存储目录
- `auth`: 认证配置
  - `tokens`: 有效的访问令牌列表

修改配置文件后，需要重启服务才能生效。

## API文档

所有API接口（除主页和文件下载接口外）都需要通过Bearer Token进行认证，请在HTTP请求头中添加：
```
Authorization: Bearer YOUR_TOKEN
```

### 1. 上传文件

**POST** /api/upload

Content-Type: multipart/form-data

请求参数：
- `files`: 文件对象（可多个）

响应示例：
```json
{
  "message": "文件上传成功",
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "files": [
    {
      "filename": "example.jpg",
      "url": "http://localhost:9012/public/download/550e8400-e29b-41d4-a716-446655440000/example.jpg",
      "physical_path": "/absolute/path/to/app/uploads/550e8400-e29b-41d4-a716-446655440000/example.jpg"
    }
  ]
}
```

### 2. 获取文件

**GET** /public/download/{upload_id}/{filename}

直接返回文件内容。此接口不需要认证就可以访问，方便在浏览器中直接打开文件。

文件会以附件形式下载，名称保持原始文件名。

### 3. 列出上传的文件

**GET** /api/files/{upload_id}

响应示例：
```json
{
  "upload_id": "550e8400-e29b-41d4-a716-446655440000",
  "files": [
    {
      "filename": "example.jpg",
      "url": "http://localhost:9012/public/download/550e8400-e29b-41d4-a716-446655440000/example.jpg",
      "physical_path": "/absolute/path/to/app/uploads/550e8400-e29b-41d4-a716-446655440000/example.jpg",
      "size": 12345
    }
  ]
}
```

### 4. 获取配置

**GET** /api/config

响应示例：
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 9012,
    "debug": false
  },
  "upload": {
    "max_file_size": 50,
    "allowed_extensions": ["jpg", "jpeg", "png", "pdf", "doc", "docx", "xls", "xlsx", "txt", "zip", "rar"],
    "upload_folder": "app/uploads"
  }
}
```

### 5. 更新配置

**POST** /api/config

Content-Type: application/json

请求示例：
```json
{
  "upload": {
    "max_file_size": 100,
    "allowed_extensions": ["jpg", "jpeg", "png", "gif"]
  }
}
```

响应示例：
```json
{
  "message": "配置已更新",
  "config": {
    "server": {
      "host": "0.0.0.0",
      "port": 9012,
      "debug": false
    },
    "upload": {
      "max_file_size": 100,
      "allowed_extensions": ["jpg", "jpeg", "png", "gif"],
      "upload_folder": "app/uploads"
    }
  }
}
```

## API客户端示例

### Python示例

```python
import requests
import json

# 配置
API_URL = "http://localhost:9012"  # 根据配置文件中的设置修改
TOKEN = "zBEWv6K1NdS7Lnq8XmCjP9"  # 使用配置文件中的令牌

# 设置认证头
headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# 上传文件
def upload_files(file_paths):
    files = [('files', (open(path, 'rb'))) for path in file_paths]
    response = requests.post(f"{API_URL}/api/upload", headers=headers, files=files)
    for file in files:
        file[1].close()
    return response.json()

# 获取上传ID下的所有文件
def list_files(upload_id):
    response = requests.get(f"{API_URL}/api/files/{upload_id}", headers=headers)
    return response.json()

# 下载文件（无需认证）
def download_file(upload_id, filename):
    response = requests.get(f"{API_URL}/public/download/{upload_id}/{filename}")
    return response.content

# 获取配置
def get_config():
    response = requests.get(f"{API_URL}/api/config", headers=headers)
    return response.json()

# 更新配置
def update_config(config_data):
    response = requests.post(
        f"{API_URL}/api/config", 
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(config_data)
    )
    return response.json()
```

### cURL示例

上传文件：
```bash
curl -X POST \
  -H "Authorization: Bearer zBEWv6K1NdS7Lnq8XmCjP9" \
  -F "files=@/path/to/your/file.jpg" \
  -F "files=@/path/to/another/file.pdf" \
  http://localhost:9012/api/upload
```

列出文件：
```bash
curl -X GET \
  -H "Authorization: Bearer zBEWv6K1NdS7Lnq8XmCjP9" \
  http://localhost:9012/api/files/YOUR_UPLOAD_ID
```

下载文件（无需认证）：
```bash
curl -X GET \
  http://localhost:9012/public/download/YOUR_UPLOAD_ID/filename.jpg \
  -o downloaded_file.jpg
```

获取配置：
```bash
curl -X GET \
  -H "Authorization: Bearer zBEWv6K1NdS7Lnq8XmCjP9" \
  http://localhost:9012/api/config
```

更新配置：
```bash
curl -X POST \
  -H "Authorization: Bearer zBEWv6K1NdS7Lnq8XmCjP9" \
  -H "Content-Type: application/json" \
  -d '{"upload": {"max_file_size": 100, "allowed_extensions": ["jpg", "jpeg", "png", "gif"]}}' \
  http://localhost:9012/api/config
``` 