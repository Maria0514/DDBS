"""
日志系统模块
提供统一的日志记录功能
"""
import logging
import logging.handlers
import os
import colorlog
from config import LogConfig

class DistributedDBLogger:
    """分布式数据库日志记录器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name):
        """获取指定名称的日志记录器"""
        if name not in cls._loggers:
            cls._loggers[name] = cls._create_logger(name)
        return cls._loggers[name]
    
    @classmethod
    def _create_logger(cls, name):
        """创建日志记录器"""
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, LogConfig.LOG_LEVEL))
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建日志目录
        log_dir = os.path.dirname(LogConfig.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            LogConfig.LOG_FILE,
            maxBytes=LogConfig.MAX_LOG_SIZE * 1024 * 1024,
            backupCount=LogConfig.BACKUP_COUNT,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(LogConfig.LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器（带颜色）
        console_handler = colorlog.StreamHandler()
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger

# 预定义的日志记录器
transaction_logger = DistributedDBLogger.get_logger('transaction')
database_logger = DistributedDBLogger.get_logger('database')
web_logger = DistributedDBLogger.get_logger('web')
system_logger = DistributedDBLogger.get_logger('system')

def log_transaction_start(transaction_id, participants):
    """记录事务开始"""
    transaction_logger.info(f"Transaction {transaction_id} started with participants: {participants}")

def log_transaction_prepare(transaction_id, participant, success):
    """记录事务准备阶段"""
    status = "SUCCESS" if success else "FAILED"
    transaction_logger.info(f"Transaction {transaction_id} prepare phase - Participant {participant}: {status}")

def log_transaction_commit(transaction_id, success):
    """记录事务提交"""
    status = "COMMITTED" if success else "ROLLBACK"
    transaction_logger.info(f"Transaction {transaction_id} {status}")

def log_database_operation(operation, database, table, success, error=None):
    """记录数据库操作"""
    if success:
        database_logger.info(f"Database operation SUCCESS - {operation} on {database}.{table}")
    else:
        database_logger.error(f"Database operation FAILED - {operation} on {database}.{table}: {error}")

def log_connection_event(event, database, success, error=None):
    """记录连接事件"""
    if success:
        database_logger.info(f"Database connection {event} - {database}")
    else:
        database_logger.error(f"Database connection {event} FAILED - {database}: {error}")

def log_web_request(method, endpoint, status_code):
    """记录Web请求"""
    web_logger.info(f"Web request - {method} {endpoint} - Status: {status_code}")

def log_system_error(component, error):
    """记录系统错误"""
    system_logger.error(f"System error in {component}: {error}")

def log_system_info(component, message):
    """记录系统信息"""
    system_logger.info(f"{component}: {message}")
