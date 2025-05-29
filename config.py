"""
配置管理模块
管理分布式数据库系统的所有配置参数
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class DatabaseConfig:
    """数据库配置类"""

    # 数据库1配置
    DB1_HOST = os.getenv('DB1_HOST', 'localhost')
    DB1_PORT = int(os.getenv('DB1_PORT', 3306))
    DB1_USER = os.getenv('DB1_USER', 'root')
    DB1_PASSWORD = os.getenv('DB1_PASSWORD', 'password')
    DB1_DATABASE = os.getenv('DB1_DATABASE', 'db1')

    # 数据库2配置
    DB2_HOST = os.getenv('DB2_HOST', 'localhost')
    DB2_PORT = int(os.getenv('DB2_PORT', 3307))
    DB2_USER = os.getenv('DB2_USER', 'root')
    DB2_PASSWORD = os.getenv('DB2_PASSWORD', 'password')
    DB2_DATABASE = os.getenv('DB2_DATABASE', 'db2')

    # 连接池配置
    CONNECTION_POOL_SIZE = int(os.getenv('CONNECTION_POOL_SIZE', 5))
    CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', 30))

    @classmethod
    def get_db1_config(cls):
        """获取数据库1配置"""
        return {
            'host': cls.DB1_HOST,
            'port': cls.DB1_PORT,
            'user': cls.DB1_USER,
            'password': cls.DB1_PASSWORD,
            'database': cls.DB1_DATABASE,
            'autocommit': False,
            'connection_timeout': cls.CONNECTION_TIMEOUT
        }

    @classmethod
    def get_db2_config(cls):
        """获取数据库2配置"""
        return {
            'host': cls.DB2_HOST,
            'port': cls.DB2_PORT,
            'user': cls.DB2_USER,
            'password': cls.DB2_PASSWORD,
            'database': cls.DB2_DATABASE,
            'autocommit': False,
            'connection_timeout': cls.CONNECTION_TIMEOUT
        }

class TransactionConfig:
    """事务配置类"""

    # 事务超时时间（秒）
    TRANSACTION_TIMEOUT = int(os.getenv('TRANSACTION_TIMEOUT', 60))

    # 重试次数
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', 3))

    # 重试间隔（秒）
    RETRY_INTERVAL = int(os.getenv('RETRY_INTERVAL', 1))

    # 2PC准备阶段超时时间（秒）
    PREPARE_TIMEOUT = int(os.getenv('PREPARE_TIMEOUT', 30))

class WebConfig:
    """Web界面配置类"""

    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    HOST = os.getenv('WEB_HOST', '0.0.0.0')
    PORT = int(os.getenv('WEB_PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # SocketIO配置
    SOCKETIO_ASYNC_MODE = os.getenv('SOCKETIO_ASYNC_MODE', 'threading')

class LogConfig:
    """日志配置类"""

    # 日志级别
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # 日志文件路径
    LOG_FILE = os.getenv('LOG_FILE', 'logs/distributed_db.log')

    # 日志格式
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # 日志文件最大大小（MB）
    MAX_LOG_SIZE = int(os.getenv('MAX_LOG_SIZE', 10))

    # 保留的日志文件数量
    BACKUP_COUNT = int(os.getenv('BACKUP_COUNT', 5))
