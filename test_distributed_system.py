"""
分布式数据库系统测试套件
包含单元测试和集成测试
"""
import pytest
import mysql.connector
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from transaction_manager import EnhancedTransactionManager, TransactionState, ParticipantState
from database_manager import DatabaseManager, DatabaseNode
from distributed_app import BankingService, InventoryService
from config import DatabaseConfig, TransactionConfig

class TestTransactionManager:
    """事务管理器测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        # 创建模拟连接
        self.mock_connections = [Mock(), Mock()]
        for conn in self.mock_connections:
            conn.cursor.return_value = Mock()
        
        self.tm = EnhancedTransactionManager(self.mock_connections)
    
    def test_transaction_initialization(self):
        """测试事务初始化"""
        assert self.tm.state == TransactionState.INIT
        assert len(self.tm.participants) == 2
        assert self.tm.transaction_id is not None
        assert len(self.tm.operations) == 0
    
    def test_begin_transaction_success(self):
        """测试成功开始事务"""
        # 模拟成功的XA START
        for conn in self.mock_connections:
            conn.cursor.return_value.execute.return_value = None
        
        result = self.tm.begin_transaction()
        
        assert result is True
        assert self.tm.state == TransactionState.ACTIVE
        
        # 验证XA START被调用
        for conn in self.mock_connections:
            conn.cursor.return_value.execute.assert_called()
    
    def test_begin_transaction_failure(self):
        """测试开始事务失败"""
        # 模拟XA START失败
        self.mock_connections[0].cursor.return_value.execute.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception) as exc_info:
            self.tm.begin_transaction()
        
        assert "Failed to start transaction" in str(exc_info.value)
        assert self.tm.state == TransactionState.ABORTED
    
    def test_prepare_success(self):
        """测试成功准备阶段"""
        # 先开始事务
        self.tm.state = TransactionState.ACTIVE
        for participant in self.tm.participants.values():
            participant.xa_id = f"test_xa_{participant.participant_id}"
        
        # 模拟成功的准备阶段
        for conn in self.mock_connections:
            conn.cursor.return_value.execute.return_value = None
        
        result = self.tm.prepare()
        
        assert result is True
        assert self.tm.state == TransactionState.PREPARED
        
        # 验证所有参与者状态
        for participant in self.tm.participants.values():
            assert participant.state == ParticipantState.PREPARED
    
    def test_prepare_failure(self):
        """测试准备阶段失败"""
        self.tm.state = TransactionState.ACTIVE
        for participant in self.tm.participants.values():
            participant.xa_id = f"test_xa_{participant.participant_id}"
        
        # 模拟准备失败
        self.mock_connections[0].cursor.return_value.execute.side_effect = Exception("Prepare failed")
        
        with pytest.raises(Exception) as exc_info:
            self.tm.prepare()
        
        assert "Prepare phase failed" in str(exc_info.value)
        assert self.tm.state == TransactionState.ABORTED
    
    def test_commit_success(self):
        """测试成功提交"""
        self.tm.state = TransactionState.PREPARED
        for participant in self.tm.participants.values():
            participant.xa_id = f"test_xa_{participant.participant_id}"
            participant.state = ParticipantState.PREPARED
        
        # 模拟成功提交
        for conn in self.mock_connections:
            conn.cursor.return_value.execute.return_value = None
        
        result = self.tm.commit()
        
        assert result is True
        assert self.tm.state == TransactionState.COMMITTED
    
    def test_rollback_success(self):
        """测试成功回滚"""
        self.tm.state = TransactionState.ACTIVE
        for participant in self.tm.participants.values():
            participant.xa_id = f"test_xa_{participant.participant_id}"
        
        # 模拟成功回滚
        for conn in self.mock_connections:
            conn.cursor.return_value.execute.return_value = None
        
        result = self.tm.rollback()
        
        assert result is True
        assert self.tm.state == TransactionState.ABORTED
    
    def test_execute_operation(self):
        """测试执行操作"""
        self.tm.state = TransactionState.ACTIVE
        
        def mock_operation(conn, arg1, arg2):
            return f"result_{arg1}_{arg2}"
        
        result = self.tm.execute_operation("participant_1", mock_operation, "test", "data")
        
        assert result == "result_test_data"
        assert len(self.tm.operations) == 1
        assert self.tm.operations[0]['operation'] == 'mock_operation'
    
    def test_transaction_timeout(self):
        """测试事务超时"""
        # 设置很短的超时时间
        self.tm.timeout = 0.1
        self.tm.start_time = time.time() - 1  # 模拟已经超时
        
        with pytest.raises(Exception) as exc_info:
            self.tm.begin_transaction()
        
        assert "timed out" in str(exc_info.value)

class TestDatabaseManager:
    """数据库管理器测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        # 使用模拟配置
        with patch('database_manager.DatabaseConfig') as mock_config:
            mock_config.get_db1_config.return_value = {
                'host': 'localhost',
                'port': 3306,
                'user': 'test',
                'password': 'test',
                'database': 'test_db1'
            }
            mock_config.get_db2_config.return_value = {
                'host': 'localhost',
                'port': 3307,
                'user': 'test',
                'password': 'test',
                'database': 'test_db2'
            }
            
            with patch('database_manager.pooling.MySQLConnectionPool'):
                self.db_manager = DatabaseManager()
    
    def test_initialization(self):
        """测试数据库管理器初始化"""
        assert 'db1' in self.db_manager.nodes
        assert 'db2' in self.db_manager.nodes
        assert len(self.db_manager.nodes) == 2
    
    @patch('database_manager.pooling.MySQLConnectionPool')
    def test_get_connection(self, mock_pool):
        """测试获取连接"""
        mock_connection = Mock()
        mock_pool.return_value.get_connection.return_value = mock_connection
        
        # 重新创建节点以使用模拟的连接池
        node = DatabaseNode('test', {'host': 'localhost', 'port': 3306, 'user': 'test', 'password': 'test', 'database': 'test'})
        
        conn = node.get_connection()
        assert conn == mock_connection
    
    def test_node_health_check(self):
        """测试节点健康检查"""
        with patch('database_manager.pooling.MySQLConnectionPool'):
            node = DatabaseNode('test', {'host': 'localhost', 'port': 3306, 'user': 'test', 'password': 'test', 'database': 'test'})
            
            # 模拟健康检查成功
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            
            with patch.object(node, 'get_connection', return_value=mock_conn):
                result = node.check_health()
                assert result is True
                assert node.is_available is True

class TestBankingService:
    """银行服务测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        # with patch('distributed_app.db_manager') as mock_db_manager:
        self.banking_service = BankingService()
        self.mock_db_manager = MagicMock()
        self.banking_service.db_manager = self.mock_db_manager
    
    def test_create_account_success(self):
        """测试成功创建账户"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        
        self.mock_db_manager.get_connection.return_value = mock_conn
        
        result = self.banking_service.create_account(1001, 1000.0)
        
        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    def test_create_account_failure(self):
        """测试创建账户失败"""
        self.mock_db_manager.get_connection.side_effect = Exception("Database error")
        
        result = self.banking_service.create_account(1001, 1000.0)
        
        assert result is False
    
    def test_get_account_balance(self):
        """测试获取账户余额"""
        self.mock_db_manager.execute_query.return_value = [{'balance': 1500.0}]
        
        balance = self.banking_service.get_account_balance(1001)
        
        assert balance == 1500.0
    
    def test_get_account_balance_not_found(self):
        """测试获取不存在账户的余额"""
        self.mock_db_manager.execute_query.return_value = []
        
        balance = self.banking_service.get_account_balance(9999)
        
        assert balance is None

class TestInventoryService:
    """库存服务测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        with patch('distributed_app.db_manager') as mock_db_manager:
            self.mock_db_manager = mock_db_manager
            self.inventory_service = InventoryService()

class TestIntegration:
    """集成测试类"""
    
    @pytest.mark.integration
    def test_full_transaction_flow(self):
        """测试完整的事务流程"""
        # 这个测试需要真实的数据库连接
        # 在CI/CD环境中可以跳过
        pytest.skip("需要真实数据库连接的集成测试")
    
    @pytest.mark.integration
    def test_concurrent_transactions(self):
        """测试并发事务"""
        pytest.skip("需要真实数据库连接的并发测试")

class TestPerformance:
    """性能测试类"""
    
    def test_transaction_manager_performance(self):
        """测试事务管理器性能"""
        # 创建大量模拟连接
        connections = [Mock() for _ in range(10)]
        for conn in connections:
            conn.cursor.return_value = Mock()
        
        start_time = time.time()
        
        # 创建事务管理器
        tm = EnhancedTransactionManager(connections)
        
        # 执行基本操作
        tm.begin_transaction()
        
        end_time = time.time()
        
        # 验证性能（应该在合理时间内完成）
        assert end_time - start_time < 1.0  # 1秒内完成
    
    def test_concurrent_transaction_managers(self):
        """测试并发事务管理器"""
        def create_and_run_transaction():
            connections = [Mock(), Mock()]
            for conn in connections:
                conn.cursor.return_value = Mock()
            
            tm = EnhancedTransactionManager(connections)
            tm.begin_transaction()
            return tm.transaction_id
        
        # 创建多个线程同时运行事务
        threads = []
        results = []
        
        for _ in range(5):
            thread = threading.Thread(target=lambda: results.append(create_and_run_transaction()))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有事务ID都是唯一的
        assert len(set(results)) == len(results)

def run_tests():
    """运行所有测试"""
    print("开始运行分布式数据库系统测试...")
    
    # 运行测试
    pytest_args = [
        __file__,
        '-v',  # 详细输出
        '--tb=short',  # 简短的错误回溯
        '-x',  # 遇到第一个失败就停止
    ]
    
    # 如果有真实数据库连接，可以运行集成测试
    # pytest_args.append('-m not integration')
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("所有测试通过！")
    else:
        print("部分测试失败！")
    
    return exit_code

if __name__ == "__main__":
    run_tests()
