**中文** | [English](README.md)

# MySQL 查询 API 服务

基于 Flask 的 MySQL 查询 API 服务，提供安全的只读 SQL 查询接口。

## 1. 使用场景

该服务特别适合与大型语言模型(LLM)工作流平台集成，例如：

- **Dify.ai**：在 Dify 应用中通过 API 调用轻松连接到 MySQL 数据库
- **FastGPT**：将实时数据库查询集成到 FastGPT 工作流中
- **Coze**：在 Coze 应用中启用数据库访问功能

LLM 工作流集成的主要优势：
- 简单的 REST API 接口，配置要求最小化
- 安全的只读访问，防止意外数据修改
- 内置 SQL 注入保护
- 易于部署和维护

## 2. 功能特点

- RESTful API 接口（同时支持 GET 和 POST 方法）
- 安全的只读 SQL 查询
- API 密钥认证
- Docker 容器化部署
- 健康检查端点
- 详细的错误信息用于故障排除
- 请求 ID 跟踪，便于调试
- 查询超时控制，防止长时间运行的查询
- 结果大小限制，防止内存问题
- 自动添加 LIMIT 子句（对于没有 LIMIT 的查询）
- 增强的错误处理，提供详细诊断信息

## 2. API 文档

### 2.1 端点

| 端点 | 方法 | 路径 | 描述 |
|----------|--------|------|-------------|
| 查询 | GET/POST | /query | 执行 SQL 查询并返回结果 |
| 健康检查 | GET | /health | 检查服务状态 |

### 2.2 查询端点

#### 请求参数

| 参数 | 位置 | 类型 | 必需 | 描述 |
|-----------|----------|------|----------|-------------|
| X-API-Key | header | 字符串 | 是 | API 密钥 |
| sql | 查询参数/请求体 | 字符串 | 是 | SQL 查询语句 |

#### 请求方法

**GET 方法**:
- SQL 查询作为 URL 参数传递
- 示例：`/query?sql=SELECT * FROM users LIMIT 5`

**POST 方法（推荐）**:
- 支持 JSON 和表单数据格式
- JSON 格式：`{"sql": "SELECT * FROM users LIMIT 5"}`
- 表单数据：`sql=SELECT * FROM users LIMIT 5`
- 推荐使用 POST 方法处理复杂或较长的查询，避免 URL 长度限制导致的问题

#### 安全限制

- 仅支持 SELECT 和 WITH 语句
- 查询长度不得超过 3000 个字符
- 不允许多条语句（不允许使用分号）
- 禁止使用危险关键字（DELETE、DROP、INSERT 等）
- 没有 LIMIT 子句的查询将自动添加一个

#### 响应格式

成功响应：
```json
{
    "status": "success",
    "data": [],
    "metadata": {
        "row_count": 10,
        "execution_time": "0.25s",
        "truncated": false
    }
}
```

错误响应：
```json
{
    "status": "error",
    "code": 1064,  // MySQL 错误代码（如适用）
    "message": "详细错误信息",
    "details": "原始数据库错误消息",
    "metadata": {
        "execution_time": "0.15s"
    },
    "request_id": "a1b2c3d4"  // 用于错误报告
}
```

#### 示例

GET 请求：
```bash
curl -X GET "http://localhost:8888/query?sql=SELECT%20*%20FROM%20users%20LIMIT%205" \
     -H "X-API-Key: your-secret-key"
```

POST 请求（JSON）：
```bash
curl -X POST "http://localhost:8888/query" \
     -H "X-API-Key: your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{"sql": "SELECT * FROM users LIMIT 5"}'
```

POST 请求（表单）：
```bash
curl -X POST "http://localhost:8888/query" \
     -H "X-API-Key: your-secret-key" \
     -d "sql=SELECT * FROM users LIMIT 5"
```

### 2.3 健康检查端点

#### 响应格式

```json
{
    "status": "ok",
    "database": "connected"
}
```

## 3. 环境设置

### 3.1 要求

- Python 3.9+
- MySQL 8.0+
- Docker（可选）

### 3.2 配置

1. 使用环境文件配置

创建 `.env` 文件：

```ini
# MySQL 配置
MYSQL_HOST=mysql      # MySQL 服务器地址
MYSQL_PORT=3306      # MySQL 服务器端口
MYSQL_USER=root      # MySQL 用户名
MYSQL_PASSWORD=your_password   # MySQL 密码
MYSQL_DATABASE=test   # MySQL 数据库名
MYSQL_TIMEOUT=10     # 连接超时时间（秒）

# API 密钥
API_KEY=your-secret-key   # API 访问密钥

# 性能设置
MAX_RESULT_ROWS=10000    # 返回的最大行数
QUERY_TIMEOUT=30         # 查询执行超时时间（秒）
```

2. 或直接设置环境变量

```bash
export MYSQL_HOST=mysql
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=test
export API_KEY=your-secret-key
export MAX_RESULT_ROWS=10000
export QUERY_TIMEOUT=30
```

### 3.3 安全建议

1. 数据库账户权限
   - 强烈建议使用只读数据库账户
   - 由于此服务仅提供查询功能，使用只读账户可有效防止意外数据修改
   - 创建只读用户示例：
   ```sql
   CREATE USER 'readonly_user'@'%' IDENTIFIED BY 'password';
   GRANT SELECT ON database_name.* TO 'readonly_user'@'%';
   FLUSH PRIVILEGES;
   ```

2. API 密钥
   - 使用足够复杂的 API 密钥
   - 定期轮换 API 密钥
   - 避免在代码中硬编码 API 密钥

3. 查询限制
   - 根据数据库大小和性能设置适当的 `MAX_RESULT_ROWS` 和 `QUERY_TIMEOUT` 值
   - 对于大型数据库，考虑使用较低的值以防止资源耗尽

## 4. 部署

### 4.1 Docker 部署

1. 克隆仓库

```bash
git clone https://github.com/shawnsky/flask-sql.git
cd flask-sql
```

2. 配置环境变量

复制 `.env.example` 到 `.env` 并根据需要修改配置：

```bash
cp .env.example .env
```

3. 启动服务

```bash
docker-compose up -d
```

服务将在端口 `8888` 上启动，可通过 `http://localhost:8888` 访问。

### 4.2 本地部署

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 配置环境变量（参考上面的配置部分）

3. 启动服务

```bash
python app.py
```

## 5. 故障排除

### 5.1 使用请求 ID

每个请求都会分配一个唯一的请求 ID，包含在：
- 与请求相关的日志条目中
- 错误响应中

报告问题时，请始终包含请求 ID 以帮助调试。

### 5.2 常见问题

1. **查询超时**
   - 错误："查询执行在 X 秒后超时"
   - 解决方案：优化查询或增加 `QUERY_TIMEOUT` 值

2. **结果截断**
   - 症状：响应中的元数据包含 `"truncated": true`
   - 解决方案：在查询中添加更严格的 LIMIT 子句或增加 `MAX_RESULT_ROWS`

3. **权限错误**
   - 错误："数据库权限被拒绝"
   - 解决方案：确保数据库用户具有适当的 SELECT 权限

## 6. 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。
