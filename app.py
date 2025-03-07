from flask import Flask, request, jsonify
from mysql.connector import connect, Error
import re
import os
import logging
import time
import uuid
import traceback
from functools import wraps
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(request_id)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)

# 添加请求ID过滤器
class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(record, 'request_id', 'N/A')
        return True

logger = logging.getLogger(__name__)
logger.addFilter(RequestIDFilter())

# Load environment variables
load_dotenv()
logger.info('Environment variables loaded successfully', extra={'request_id': 'STARTUP'})

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'test'),
    'connection_timeout': int(os.getenv('MYSQL_TIMEOUT', '10')),  # 连接超时设置
    'consume_results': True  # 自动消费结果，避免内存问题
}

# 查询结果限制
MAX_RESULT_ROWS = int(os.getenv('MAX_RESULT_ROWS', '10000'))
QUERY_TIMEOUT = int(os.getenv('QUERY_TIMEOUT', '30'))  # 查询超时时间（秒）

logger.info(f'Database configuration completed: host={DB_CONFIG["host"]}, port={DB_CONFIG["port"]}, database={DB_CONFIG["database"]}', 
           extra={'request_id': 'STARTUP'})

# API密钥
API_KEY = os.getenv('API_KEY', 'your-secret-key')

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        request_id = str(uuid.uuid4())[:8]
        request.request_id = request_id
        
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            logger.info(f'API authentication successful: {request.path}', 
                       extra={'request_id': request_id})
            return f(*args, **kwargs)
        logger.warning(f'API authentication failed: {request.path}', 
                      extra={'request_id': request_id})
        return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401
    return decorated

def is_safe_sql(sql, request_id):
    # 检查SQL语句长度
    if len(sql) > 3000:
        logger.warning(f'SQL query length exceeds limit: {len(sql)}', 
                      extra={'request_id': request_id})
        return False, "SQL query length exceeds the 3000 character limit"

    # Check if query is SELECT or WITH
    sql_upper = sql.strip().upper()
    if not (sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')):
        logger.warning('SQL query is not a SELECT or WITH statement', 
                      extra={'request_id': request_id})
        return False, "Only SELECT or WITH statements are allowed"
    
    # Check for dangerous keywords using regex pattern
    dangerous_keywords = ['DELETE', 'DROP', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE', 
                         'EXEC', 'EXECUTE', 'INTO OUTFILE', 'LOAD_FILE']
    # 使用正则表达式匹配完整的SQL关键字
    for keyword in dangerous_keywords:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_upper):
            logger.warning(f'SQL query contains dangerous keyword: {keyword}', 
                          extra={'request_id': request_id})
            return False, f"SQL query contains forbidden keyword: {keyword}"

    # Check for multiple statements (semicolons)
    if ';' in sql:
        logger.warning('SQL query contains multiple statements', 
                      extra={'request_id': request_id})
        return False, "Multiple SQL statements are not allowed"
    
    # 检查是否包含LIMIT子句，如果没有则警告
    if 'LIMIT' not in sql_upper:
        logger.warning('SQL query does not contain LIMIT clause', 
                      extra={'request_id': request_id})
    
    logger.info('SQL query security check passed', extra={'request_id': request_id})
    return True, ""

@app.route('/health')
def health_check():
    request_id = str(uuid.uuid4())[:8]
    logger.info('Health check request received', extra={'request_id': request_id})
    
    # 简单的数据库连接测试
    try:
        with connect(**DB_CONFIG) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        logger.error(f'Database connection failed: {str(e)}', 
                    extra={'request_id': request_id})
        return jsonify({
            'status': 'error', 
            'message': 'Database connection failed',
            'database': 'disconnected'
        }), 500

def execute_query(sql, request_id):
    """Execute SQL query and return results or error message"""
    start_time = time.time()
    
    if not sql:
        logger.warning('No SQL query provided', extra={'request_id': request_id})
        return jsonify({'status': 'error', 'message': 'SQL query is required'}), 400
    
    # 记录原始SQL查询
    logger.info(f'Original SQL query: {sql}', extra={'request_id': request_id})
    
    is_safe, error_message = is_safe_sql(sql, request_id)
    if not is_safe:
        logger.warning(f'SQL query failed security check: {error_message}', 
                      extra={'request_id': request_id})
        return jsonify({'status': 'error', 'message': error_message}), 400
    
    # 如果查询没有LIMIT子句，自动添加LIMIT
    sql_upper = sql.strip().upper()
    if 'LIMIT' not in sql_upper:
        sql = f"{sql} LIMIT {MAX_RESULT_ROWS}"
        logger.info(f'Added LIMIT clause to query: {sql}', 
                   extra={'request_id': request_id})
    
    try:
        with connect(**DB_CONFIG) as conn:
            # 设置会话变量以限制查询执行时间
            with conn.cursor() as setup_cursor:
                setup_cursor.execute(f"SET SESSION MAX_EXECUTION_TIME = {QUERY_TIMEOUT * 1000}")
            
            with conn.cursor(dictionary=True) as cursor:
                logger.info(f'Executing SQL query: {sql}', 
                           extra={'request_id': request_id})
                cursor.execute(sql)
                
                # 获取结果并限制行数
                results = []
                row_count = 0
                for row in cursor:
                    results.append(row)
                    row_count += 1
                    if row_count >= MAX_RESULT_ROWS:
                        logger.warning(f'Query result truncated at {MAX_RESULT_ROWS} rows', 
                                      extra={'request_id': request_id})
                        break
                
                execution_time = time.time() - start_time
                logger.info(f'Query successful, returned {len(results)} records in {execution_time:.2f}s', 
                           extra={'request_id': request_id})
                
                return jsonify({
                    'status': 'success',
                    'data': results,
                    'metadata': {
                        'row_count': len(results),
                        'execution_time': f"{execution_time:.2f}s",
                        'truncated': row_count >= MAX_RESULT_ROWS
                    }
                })
    except Error as e:
        error_code = getattr(e, 'errno', None)
        error_msg = str(e)
        execution_time = time.time() - start_time
        
        # 获取详细的错误堆栈
        stack_trace = traceback.format_exc()
        logger.error(f'Database error: {error_code} - {error_msg}\n{stack_trace}', 
                    extra={'request_id': request_id})
        
        # 提供更友好的错误消息
        user_message = error_msg
        if "command denied" in error_msg.lower():
            user_message = "Database permission denied. The query contains operations not allowed by your user account."
        elif "timeout" in error_msg.lower():
            user_message = f"Query execution timed out after {QUERY_TIMEOUT} seconds. Please optimize your query."
        
        return jsonify({
            'status': 'error',
            'code': error_code,
            'message': user_message,
            'details': error_msg,
            'metadata': {
                'execution_time': f"{execution_time:.2f}s"
            }
        }), 500
    except Exception as e:
        # 捕获所有其他异常
        execution_time = time.time() - start_time
        stack_trace = traceback.format_exc()
        logger.error(f'Unexpected error: {str(e)}\n{stack_trace}', 
                    extra={'request_id': request_id})
        
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred',
            'details': str(e),
            'metadata': {
                'execution_time': f"{execution_time:.2f}s"
            }
        }), 500

@app.route('/query', methods=['GET', 'POST'])
@require_api_key
def query():
    request_id = getattr(request, 'request_id', str(uuid.uuid4())[:8])
    client_ip = request.remote_addr
    logger.info(f'Query request received from: {client_ip} via {request.method}', 
               extra={'request_id': request_id})
    
    # 记录请求头信息（用于调试）
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['x-api-key', 'authorization']}
    logger.debug(f'Request headers: {headers}', extra={'request_id': request_id})
    
    # 处理GET请求
    if request.method == 'GET':
        sql = request.args.get('sql')
        logger.info(f'GET request with query length: {len(sql) if sql else 0}', 
                   extra={'request_id': request_id})
        return execute_query(sql, request_id)
    
    # 处理POST请求
    elif request.method == 'POST':
        # 支持JSON和表单数据
        if request.is_json:
            try:
                data = request.get_json()
                sql = data.get('sql')
                logger.info(f'POST JSON request with query length: {len(sql) if sql else 0}', 
                           extra={'request_id': request_id})
            except Exception as e:
                logger.error(f'Failed to parse JSON: {str(e)}', 
                            extra={'request_id': request_id})
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid JSON format',
                    'details': str(e)
                }), 400
        else:
            sql = request.form.get('sql')
            logger.info(f'POST form request with query length: {len(sql) if sql else 0}', 
                       extra={'request_id': request_id})
        
        return execute_query(sql, request_id)

@app.errorhandler(Exception)
def handle_exception(e):
    """全局异常处理器"""
    request_id = getattr(request, 'request_id', str(uuid.uuid4())[:8])
    stack_trace = traceback.format_exc()
    logger.error(f'Unhandled exception: {str(e)}\n{stack_trace}', 
                extra={'request_id': request_id})
    
    return jsonify({
        'status': 'error',
        'message': 'An unexpected error occurred',
        'details': str(e),
        'request_id': request_id  # 返回请求ID便于用户报告问题
    }), 500

if __name__ == '__main__':
    logger.info('Starting Flask application server', extra={'request_id': 'STARTUP'})
    app.run(host='0.0.0.0', port=8888)