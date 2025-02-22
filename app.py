from flask import Flask, request, jsonify
from mysql.connector import connect, Error
import re
import os
from functools import wraps
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'test')
}

# API密钥
API_KEY = os.getenv('API_KEY', 'your-secret-key')

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == API_KEY:
            return f(*args, **kwargs)
        return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401
    return decorated

def is_safe_sql(sql):
    # 检查SQL语句长度
    if len(sql) > 1000:
        return False

    # 检查是否只包含SELECT语句
    sql = sql.strip().upper()
    if not sql.startswith('SELECT'):
        return False
    
    # 检查是否包含危险关键字
    dangerous_keywords = ['DELETE', 'DROP', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'TRUNCATE', 
                         'EXEC', 'EXECUTE', 'UNION', 'INTO OUTFILE', 'LOAD_FILE']
    if any(keyword in sql for keyword in dangerous_keywords):
        return False

    # 检查是否包含注释
    if '--' in sql or '/*' in sql or '*/' in sql:
        return False

    # 检查是否包含多个语句
    if ';' in sql:
        return False

    return True

@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'})

@app.route('/query')
@require_api_key
def query():
    sql = request.args.get('sql')
    if not sql:
        return jsonify({'status': 'error', 'message': 'SQL query is required'}), 400
    
    if not is_safe_sql(sql):
        return jsonify({'status': 'error', 'message': 'Invalid SQL query'}), 400
    
    try:
        with connect(**DB_CONFIG) as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(sql)
                results = cursor.fetchall()
                return jsonify({
                    'status': 'success',
                    'data': results
                })
    except Error as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)