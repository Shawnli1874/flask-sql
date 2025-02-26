[中文](README_CN.md) | **English**

# MySQL Query API Service

A Flask-based MySQL query API service that provides a secure, read-only SQL query interface.

## 1. Use Cases

This service is particularly well-suited for integration with LLM (Large Language Model) workflow platforms such as:

- **Dify.ai**: Easily connect to your MySQL database through API calls in your Dify applications
- **FastGPT**: Integrate real-time database queries into your FastGPT workflows
- **Coze**: Enable database access capabilities in your Coze applications

Key advantages for LLM workflow integration:
- Simple REST API interface requiring minimal configuration
- Secure read-only access preventing accidental data modifications
- Built-in SQL injection protection
- Easy to deploy and maintain

## 2. Features

- RESTful API interface
- Secure read-only SQL queries
- API key authentication
- Docker containerized deployment
- Health check endpoint

## 2. API Documentation

### 2.1 Endpoints

| Endpoint | Method | Path | Description |
|----------|--------|------|-------------|
| Query | GET | /query | Execute SQL queries and return results |
| Health Check | GET | /health | Check service status |

### 2.2 Query Endpoint

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| X-API-Key | Header | string | Yes | API key |
| sql | Query | string | Yes | SQL query statement |

#### Security Restrictions

- Only SELECT statements are supported
- Query length must not exceed 1000 characters
- Multiple statements are not allowed (no semicolons)
- Comments are not allowed
- Dangerous keywords are forbidden (DELETE, DROP, INSERT, etc.)

#### Response Format

Success response:
```json
{
    "status": "success",
    "data": []
}
```

Error response:
```json
{
    "status": "error",
    "message": "Error message"
}
```

#### Example

Request:
```bash
curl -X GET "http://localhost:8888/query?sql=SELECT%20*%20FROM%20users%20LIMIT%205" \
     -H "X-API-Key: your-secret-key"
```

### 2.3 Health Check Endpoint

#### Response Format

```json
{
    "status": "ok"
}
```

## 3. Environment Setup

### 3.1 Requirements

- Python 3.9+
- MySQL 8.0+
- Docker (optional)

### 3.2 Configuration

1. Configure using environment file

Create a `.env` file:

```ini
# MySQL Configuration
MYSQL_HOST=mysql      # MySQL server address
MYSQL_PORT=3306      # MySQL server port
MYSQL_USER=root      # MySQL username
MYSQL_PASSWORD=your_password   # MySQL password
MYSQL_DATABASE=test   # MySQL database name

# API Key
API_KEY=your-secret-key   # API access key
```

2. Or set environment variables directly

```bash
export MYSQL_HOST=mysql
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=test
export API_KEY=your-secret-key
```

### 3.3 Security Recommendations

1. Database Account Permissions
   - Strongly recommend using a read-only database account
   - Since this service only provides query functionality, using a read-only account can effectively prevent accidental data modifications
   - Example of creating a read-only user:
   ```sql
   CREATE USER 'readonly_user'@'%' IDENTIFIED BY 'password';
   GRANT SELECT ON database_name.* TO 'readonly_user'@'%';
   FLUSH PRIVILEGES;
   ```

2. API Key
   - Use sufficiently complex API keys
   - Regularly rotate API keys
   - Avoid hardcoding API keys in the code

## 4. Deployment

### 4.1 Docker Deployment

1. Clone the repository

```bash
git clone https://github.com/shawnsky/flask-sql.git
cd flask-sql
```

2. Configure environment variables

Copy `.env.example` to `.env` and modify the configuration as needed:

```bash
cp .env.example .env
```

3. Start the service

```bash
docker-compose up -d
```

The service will start on port `8888` and can be accessed at `http://localhost:8888`.

### 4.2 Local Deployment

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Configure environment variables (refer to configuration section above)

3. Start the service

```bash
python app.py
```

## 5. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.