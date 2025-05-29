"""
数据库管理器模块
管理分布式数据库连接和操作
"""
import mysql.connector
from mysql.connector import Error, pooling
import threading
import time
from typing import List, Dict, Optional, Tuple
from config import DatabaseConfig
from logger import database_logger, log_connection_event, log_database_operation

class DatabaseNode:
    """数据库节点类"""

    def __init__(self, node_id: str, config: Dict):
        self.node_id = node_id
        self.config = config
        self.pool = None
        self.is_available = False
        self.last_check = 0
        self._lock = threading.Lock()
        self._create_connection_pool()

    def _create_connection_pool(self):
        """创建连接池"""
        try:
            pool_config = self.config.copy()
            pool_config.update({
                'pool_name': f'pool_{self.node_id}',
                'pool_size': DatabaseConfig.CONNECTION_POOL_SIZE,
                'pool_reset_session': True
            })

            self.pool = pooling.MySQLConnectionPool(**pool_config)
            self.is_available = True
            log_connection_event(f"Connection pool created for node {self.node_id}",
                               f"{self.config['host']}:{self.config['port']}", True)

        except Error as e:
            self.is_available = False
            log_connection_event(f"Connection pool creation failed for node {self.node_id}",
                               f"{self.config['host']}:{self.config['port']}", False, str(e))
            database_logger.error(f"Failed to create connection pool for {self.node_id}: {e}")

    def get_connection(self):
        """获取数据库连接"""
        if not self.is_available:
            raise Exception(f"Database node {self.node_id} is not available")

        try:
            connection = self.pool.get_connection()
            return connection
        except Error as e:
            log_connection_event(f"Get connection failed for node {self.node_id}",
                               f"{self.config['host']}:{self.config['port']}", False, str(e))
            raise e

    def check_health(self) -> bool:
        """检查节点健康状态"""
        current_time = time.time()

        # 避免频繁检查
        if current_time - self.last_check < 30:
            return self.is_available

        with self._lock:
            try:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                conn.close()

                self.is_available = True
                self.last_check = current_time
                return True

            except Exception as e:
                self.is_available = False
                self.last_check = current_time
                database_logger.warning(f"Health check failed for {self.node_id}: {e}")
                return False

class DatabaseManager:
    """分布式数据库管理器"""

    def __init__(self):
        self.nodes: Dict[str, DatabaseNode] = {}
        self._initialize_nodes()

    def _initialize_nodes(self):
        """初始化数据库节点"""
        # 初始化数据库1
        db1_config = DatabaseConfig.get_db1_config()
        self.nodes['db1'] = DatabaseNode('db1', db1_config)

        # 初始化数据库2
        db2_config = DatabaseConfig.get_db2_config()
        self.nodes['db2'] = DatabaseNode('db2', db2_config)

        database_logger.info("Database manager initialized with nodes: " +
                           ", ".join(self.nodes.keys()))

    def get_all_connections(self) -> List[mysql.connector.MySQLConnection]:
        """获取所有数据库连接"""
        connections = []
        for node_id, node in self.nodes.items():
            try:
                conn = node.get_connection()
                connections.append(conn)
            except Exception as e:
                database_logger.error(f"Failed to get connection from {node_id}: {e}")
                # 清理已获取的连接
                for conn in connections:
                    try:
                        conn.close()
                    except:
                        pass
                raise Exception(f"Failed to get connection from {node_id}: {e}")

        return connections

    def get_connection(self, node_id: str) -> mysql.connector.MySQLConnection:
        """获取指定节点的连接（带重连机制）"""
        if node_id not in self.nodes:
            raise ValueError(f"Unknown database node: {node_id}")

        node = self.nodes[node_id]
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                connection = node.get_connection()
                # 测试连接是否有效
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()

                return connection
            except Exception as e:
                database_logger.warning(f"Connection attempt {attempt + 1} failed for {node_id}: {e}")

                if attempt < max_retries - 1:
                    # 尝试重新创建连接池
                    try:
                        node._create_connection_pool()
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    except Exception as recreate_error:
                        database_logger.error(f"Failed to recreate pool for {node_id}: {recreate_error}")
                else:
                    # 最后一次尝试失败，抛出异常
                    raise Exception(f"Database node {node_id} is not available")

    def get_available_nodes(self) -> List[str]:
        """获取可用的数据库节点"""
        available = []
        for node_id, node in self.nodes.items():
            if node.check_health():
                available.append(node_id)
        return available

    def execute_query(self, node_id: str, query: str, params: Optional[Tuple] = None) -> List:
        """在指定节点执行查询"""
        conn = None
        try:
            conn = self.get_connection(node_id)
            cursor = conn.cursor(dictionary=True)

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            result = cursor.fetchall()
            cursor.close()

            log_database_operation("SELECT", node_id, "query", True)
            return result

        except Exception as e:
            log_database_operation("SELECT", node_id, "query", False, str(e))
            raise e
        finally:
            if conn:
                conn.close()

    def get_node_status(self) -> Dict[str, Dict]:
        """获取所有节点状态"""
        status = {}
        for node_id, node in self.nodes.items():
            status[node_id] = {
                'available': node.check_health(),
                'host': node.config['host'],
                'port': node.config['port'],
                'database': node.config['database'],
                'last_check': node.last_check
            }
        return status

    def close_all_connections(self):
        """关闭所有连接池"""
        for node_id, node in self.nodes.items():
            try:
                if node.pool:
                    # MySQL连接池没有直接的关闭方法，让垃圾回收处理
                    node.pool = None
                    log_connection_event(f"Connection pool closed for node {node_id}",
                                       f"{node.config['host']}:{node.config['port']}", True)
            except Exception as e:
                database_logger.error(f"Error closing connection pool for {node_id}: {e}")

# 全局数据库管理器实例 - 延迟初始化
db_manager = None

def get_db_manager():
    """获取数据库管理器实例（单例模式）"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager
