**中文** | [English](README.md)

# MySQL 查询 API 服务

一个基于 Flask 的 MySQL 查询 API 服务，提供安全的只读 SQL 查询接口。

## 1. 功能特点

- 提供 RESTful API 接口
- 支持安全的只读 SQL 查询
- API 密钥认证
- Docker 容器化部署
- 健康检查接口

## 2. API 接口说明

### 2.1 接口列表

| 接口 | 方法 | 请求路径 | 说明 |
|------|------|----------|------|
| 查询接口 | GET | /query | 执行 SQL 查询并返回结果 |
| 健康检查 | GET | /health | 检查服务运行状态 |

### 2.2 查询接口

#### 请求参数

| 参数名 | 位置 | 类型 | 必填 | 说明 |
|--------|------|------|------|------|
| X-API-Key | Header | string | 是 | API 密钥 |
| sql | Query | string | 是 | SQL 查询语句 |

#### 安全限制

- 仅支持 SELECT 语句
- 查询语句长度不超过 1000 字符
- 不支持多语句查询（禁止使用分号）
- 禁止使用注释
- 禁止使用危险关键字（DELETE、DROP、INSERT 等）

#### 响应格式

成功响应：
```json
{
    "status": "success",
    "data": []
}
```

错误响应：
```json
{
    "status": "error",
    "message": "错误信息"
}
```

#### 示例

请求：
```bash
curl -X GET "http://localhost:8888/query?sql=SELECT%20*%20FROM%20users%20LIMIT%205" \
     -H "X-API-Key: your-secret-key"
```

### 2.3 健康检查接口

#### 响应格式

```json
{
    "status": "ok"
}
```

## 3. 环境配置

### 3.1 环境要求

- Python 3.9+
- MySQL 8.0+
- Docker（可选）

### 3.2 配置方式

1. 通过环境变量文件配置

创建 `.env` 文件：

```ini
# MySQL配置
MYSQL_HOST=mysql      # MySQL 服务器地址
MYSQL_PORT=3306      # MySQL 服务器端口
MYSQL_USER=root      # MySQL 用户名
MYSQL_PASSWORD=your_password   # MySQL 密码
MYSQL_DATABASE=test   # MySQL 数据库名

# API密钥
API_KEY=your-secret-key   # API 访问密钥
```

2. 或直接设置环境变量

```bash
export MYSQL_HOST=mysql
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=test
export API_KEY=your-secret-key
```

### 3.3 安全建议

1. 数据库账号权限
   - 强烈建议使用只读数据库账号
   - 由于本服务仅提供查询功能，使用只读账号可以有效防止意外的数据修改
   - 创建只读用户示例：
   ```sql
   CREATE USER 'readonly_user'@'%' IDENTIFIED BY 'password';
   GRANT SELECT ON database_name.* TO 'readonly_user'@'%';
   FLUSH PRIVILEGES;
   ```

2. API密钥
   - 使用足够复杂的API密钥
   - 定期更换API密钥
   - 避免在代码中硬编码API密钥

## 4. 部署说明

### 4.1 Docker 部署

1. 克隆项目代码

```bash
git clone https://github.com/shawnsky/flask-sql.git
cd flask-sql
```

2. 配置环境变量

复制 `.env.example` 文件为 `.env` 并根据实际情况修改配置：

```bash
cp .env.example .env
```

3. 启动服务

```bash
docker-compose up -d
```

服务将在 `8888` 端口启动，可通过 `http://localhost:8888` 访问。

### 4.2 本地部署

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 配置环境变量（参考上述配置方式）

3. 启动服务

```bash
python app.py
```

## 5. 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。
