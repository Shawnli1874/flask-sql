from flask import Flask, request, jsonify
from mysql.connector import connect, Error
import re
import os
import logging
from functools import wraps
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info('Environment variables loaded successfully')

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'test')
}
logger.info(f'Database configuration completed: host={DB_CONFIG["host"]}, port={DB_CONFIG["port"]}, database={DB_CONFIG["database"]}')

# API密钥
API_KEY = os.getenv('API_KEY', 'your-secret-key')

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            logger.info(f'API authentication successful: {request.path}')
            return f(*args, **kwargs)
        logger.warning(f'API authentication failed: {request.path}')
        return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401
    return decorated

def is_safe_sql(sql):
    # 检查SQL语句长度
    if len(sql) > 2000:
        logger.warning(f'SQL query length exceeds limit: {len(sql)}')
        return False

    # Check if query is SELECT or WITH
    sql = sql.strip().upper()
    if not (sql.startswith('SELECT') or sql.startswith('WITH')):
        logger.warning('SQL query is not a SELECT or WITH statement')
        return False
    
    # Check for dangerous keywords
    dangerous_keywords = ['DELETE', 'DROP', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE', 
                         'EXEC', 'EXECUTE', 'INTO OUTFILE', 'LOAD_FILE']
    if any(keyword in sql for keyword in dangerous_keywords):
        logger.warning(f'SQL query contains dangerous keywords: {sql}')
        return False

    logger.info('SQL query security check passed')
    return True

@app.route('/health')
def health_check():
    logger.info('Health check request received')
    return jsonify({'status': 'ok'})

@app.route('/query')
@require_api_key
def query():
    logger.info(f'Query request received from: {request.remote_addr}')
    sql = request.args.get('sql')
    if not sql:
        logger.warning('No SQL query provided')
        return jsonify({'status': 'error', 'message': 'SQL query is required'}), 400
    
    if not is_safe_sql(sql):
        logger.warning('SQL query failed security check')
        return jsonify({'status': 'error', 'message': 'Invalid SQL query'}), 400
    
    try:
        with connect(**DB_CONFIG) as conn:
            with conn.cursor(dictionary=True) as cursor:
                logger.info(f'Executing SQL query: {sql}')
                cursor.execute(sql)
                results = cursor.fetchall()
                logger.info(f'Query successful, returned {len(results)} records')
                return jsonify({
                    'status': 'success',
                    'data': results
                })
    except Error as e:
        logger.error(f'Database error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info('Starting Flask application server')
    app.run(host='0.0.0.0', port=8888)