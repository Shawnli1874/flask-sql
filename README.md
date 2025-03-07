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

- RESTful API interface (supports both GET and POST methods)
- Secure read-only SQL queries
- API key authentication
- Docker containerized deployment
- Health check endpoint
- Detailed error messages for troubleshooting
- Request ID tracking for easier debugging
- Query timeout control to prevent long-running queries
- Result size limitation to prevent memory issues
- Automatic LIMIT clause addition for queries without one
- Enhanced error handling with detailed diagnostics

## 2. API Documentation

### 2.1 Endpoints

| Endpoint | Method | Path | Description |
|----------|--------|------|-------------|
| Query | GET/POST | /query | Execute SQL queries and return results |
| Health Check | GET | /health | Check service status |

### 2.2 Query Endpoint

#### Request Parameters

| Parameter | Location | Type | Required | Description |
|-----------|----------|------|----------|-------------|
| X-API-Key | Header | string | Yes | API key |
| sql | Query/Body | string | Yes | SQL query statement |

#### Request Methods

**GET Method**:
- SQL query is passed as a URL parameter
- Example: `/query?sql=SELECT * FROM users LIMIT 5`

**POST Method (Recommended)**:
- Supports both JSON and form data formats
- JSON format: `{"sql": "SELECT * FROM users LIMIT 5"}`
- Form data: `sql=SELECT * FROM users LIMIT 5`
- POST method is recommended for complex or longer queries that might cause issues with URL length limitations

#### Security Restrictions

- Only SELECT and WITH statements are supported
- Query length must not exceed 3000 characters
- Multiple statements are not allowed (no semicolons)
- Dangerous keywords are forbidden (DELETE, DROP, INSERT, etc.)
- Queries without a LIMIT clause will automatically have one added

#### Response Format

Success response:
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

Error response:
```json
{
    "status": "error",
    "code": 1064,  // MySQL error code (if applicable)
    "message": "Detailed error message",
    "details": "Original database error message",
    "metadata": {
        "execution_time": "0.15s"
    },
    "request_id": "a1b2c3d4"  // For error reporting
}
```

#### Example

GET Request:
```bash
curl -X GET "http://localhost:8888/query?sql=SELECT%20*%20FROM%20users%20LIMIT%205" \
     -H "X-API-Key: your-secret-key"
```

POST Request (JSON):
```bash
curl -X POST "http://localhost:8888/query" \
     -H "X-API-Key: your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{"sql": "SELECT * FROM users LIMIT 5"}'
```

POST Request (Form):
```bash
curl -X POST "http://localhost:8888/query" \
     -H "X-API-Key: your-secret-key" \
     -d "sql=SELECT * FROM users LIMIT 5"
```

### 2.3 Health Check Endpoint

#### Response Format

```json
{
    "status": "ok",
    "database": "connected"
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
MYSQL_TIMEOUT=10     # Connection timeout in seconds

# API Key
API_KEY=your-secret-key   # API access key

# Performance Settings
MAX_RESULT_ROWS=10000    # Maximum number of rows to return
QUERY_TIMEOUT=30         # Query execution timeout in seconds
```

2. Or set environment variables directly

```bash
export MYSQL_HOST=mysql
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=test
export API_KEY=your-secret-key
export MAX_RESULT_ROWS=10000
export QUERY_TIMEOUT=30
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

3. Query Limits
   - Set appropriate values for `MAX_RESULT_ROWS` and `QUERY_TIMEOUT` based on your database size and performance
   - For large databases, consider lower values to prevent resource exhaustion

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

## 5. Troubleshooting

### 5.1 Using Request IDs

Each request is assigned a unique request ID that is included in:
- Log entries related to the request
- Error responses

When reporting issues, always include the request ID to help with debugging.

### 5.2 Common Issues

1. **Query Timeout**
   - Error: "Query execution timed out after X seconds"
   - Solution: Optimize your query or increase the `QUERY_TIMEOUT` value

2. **Result Truncation**
   - Symptom: Response includes `"truncated": true` in metadata
   - Solution: Add a more restrictive LIMIT clause to your query or increase `MAX_RESULT_ROWS`

3. **Permission Errors**
   - Error: "Database permission denied"
   - Solution: Ensure the database user has appropriate SELECT permissions

## 6. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.