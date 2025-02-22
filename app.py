from flask import Flask, request, jsonify
from mysql.connector import connect, Error
import re
import os
import logging
from functools import wraps
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()
logger.info('环境变量加载完成')

app = Flask(__name__)

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'test')
}
logger.info(f'数据库配置完成: host={DB_CONFIG["host"]}, port={DB_CONFIG["port"]}, database={DB_CONFIG["database"]}')

# API密钥
API_KEY = os.getenv('API_KEY', 'your-secret-key')

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            logger.info(f'API认证成功: {request.path}')
            return f(*args, **kwargs)
        logger.warning(f'API认证失败: {request.path}')
        return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401
    return decorated

def is_safe_sql(sql):
    # 检查SQL语句长度
    if len(sql) > 1000:
        logger.warning(f'SQL语句长度超过限制: {len(sql)}')
        return False

    # 检查是否只包含SELECT语句
    sql = sql.strip().upper()
    if not sql.startswith('SELECT'):
        logger.warning('SQL语句不是SELECT语句')
        return False
    
    # 检查是否包含危险关键字
    dangerous_keywords = ['DELETE', 'DROP', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE', 
                         'EXEC', 'EXECUTE', 'UNION', 'INTO OUTFILE', 'LOAD_FILE']
    if any(keyword in sql for keyword in dangerous_keywords):
        logger.warning(f'SQL语句包含危险关键字: {sql}')
        return False

    # 检查是否包含注释
    if '--' in sql or '/*' in sql or '*/' in sql:
        logger.warning('SQL语句包含注释')
        return False

    # 检查是否包含多个语句
    if ';' in sql:
        logger.warning('SQL语句包含多个语句')
        return False

    logger.info('SQL语句安全检查通过')
    return True

@app.route('/health')
def health_check():
    logger.info('健康检查请求')
    return jsonify({'status': 'ok'})

@app.route('/query')
@require_api_key
def query():
    logger.info(f'收到查询请求: {request.remote_addr}')
    sql = request.args.get('sql')
    if not sql:
        logger.warning('未提供SQL查询语句')
        return jsonify({'status': 'error', 'message': 'SQL query is required'}), 400
    
    if not is_safe_sql(sql):
        logger.warning('SQL语句未通过安全检查')
        return jsonify({'status': 'error', 'message': 'Invalid SQL query'}), 400
    
    try:
        with connect(**DB_CONFIG) as conn:
            with conn.cursor(dictionary=True) as cursor:
                logger.info(f'执行SQL查询: {sql}')
                cursor.execute(sql)
                results = cursor.fetchall()
                logger.info(f'查询成功，返回{len(results)}条记录')
                return jsonify({
                    'status': 'success',
                    'data': results
                })
    except Error as e:
        logger.error(f'数据库错误: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info('启动Flask应用服务器')
    app.run(host='0.0.0.0', port=8888)