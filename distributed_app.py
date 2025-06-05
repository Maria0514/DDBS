"""
增强的分布式数据库应用程序
实现复杂的业务场景，包括银行转账、库存管理等
"""
import mysql.connector
from mysql.connector import Error
import time
import random
from typing import Dict, List, Optional, Tuple
from transaction_manager import EnhancedTransactionManager
from database_manager import get_db_manager
from logger import system_logger, log_system_info, log_system_error

class BankingService:
    """银行业务服务类"""

    def __init__(self):
        self.db_manager = get_db_manager()

    def transfer_money(self, from_account: int, to_account: int, amount: float) -> bool:
        """转账操作 - 分布式事务示例"""
        connections = None
        tm = None

        try:
            # 获取数据库连接
            connections = self.db_manager.get_all_connections()
            tm = EnhancedTransactionManager(connections)

            # 开始事务
            tm.begin_transaction()

            # 定义数据库操作函数
            def check_balance(conn, account_id):
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT balance FROM accounts WHERE id = %s", (account_id,))
                result = cursor.fetchone()
                cursor.close()
                return result['balance'] if result else 0

            def update_balance(conn, account_id, new_balance):
                cursor = conn.cursor()
                cursor.execute("UPDATE accounts SET balance = %s WHERE id = %s",
                             (new_balance, account_id))
                cursor.close()
                return cursor.rowcount > 0

            def insert_transaction_log(conn, from_acc, to_acc, amount, tx_type):
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (from_account, to_account, amount, transaction_type, timestamp)
                    VALUES (%s, %s, %s, %s, NOW())
                """, (from_acc, to_acc, amount, tx_type))
                cursor.close()
                return cursor.lastrowid

            # 检查源账户余额
            from_balance = tm.execute_operation("participant_1", check_balance, from_account)
            if from_balance < amount:
                raise Exception(f"Insufficient balance. Available: {from_balance}, Required: {amount}")

            # 检查目标账户是否存在
            to_balance = tm.execute_operation("participant_1", check_balance, to_account)

            # 更新账户余额
            tm.execute_operation("participant_1", update_balance, from_account, float(from_balance) - amount)
            tm.execute_operation("participant_1", update_balance, to_account, float(to_balance) + amount)

            # 记录交易日志
            tm.execute_operation("participant_2", insert_transaction_log,
                               from_account, to_account, amount, "TRANSFER")

            # 准备提交
            tm.prepare()

            # 提交事务
            tm.commit()

            log_system_info("BankingService",
                          f"Transfer successful: {from_account} -> {to_account}, Amount: {amount}")
            return True

        except Exception as e:
            log_system_error("BankingService.transfer_money", str(e))
            if tm:
                tm.rollback()
            return False
        finally:
            if tm:
                tm.cleanup()

    def delete_account(self, account_id: int) -> bool:
        """删除账户"""
        conn = None
        try:
            conn = self.db_manager.get_connection('db1')
            cursor = conn.cursor()
            cursor.execute("DELETE FROM accounts WHERE id = %s", (account_id,))
            conn.commit()
            cursor.close()

            log_system_info("BankingService", f"Account {account_id} deleted")
            return True

        except Exception as e:
            log_system_error("BankingService.delete_account", f"Database error: {str(e)}")
            return False
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    def create_account(self, account_id: int, initial_balance: float = 0) -> bool:
        """创建账户"""
        conn = None
        try:
            conn = self.db_manager.get_connection('db1')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO accounts (id, balance) VALUES (%s, %s)",
                         (account_id, initial_balance))
            # cursor.execute("UPDATE accounts SET balance = (%s) where account_id = (%s)", (initial_balance, account_id))
            conn.commit()
            cursor.close()

            log_system_info("BankingService", f"Account {account_id} created with balance {initial_balance}")
            return True

        except Exception as e:
            log_system_error("BankingService.create_account", f"Database error: {str(e)}")
            return False
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

    def get_account_balance(self, account_id: int) -> Optional[float]:
        """获取账户余额"""
        try:
            result = self.db_manager.execute_query('db1',
                "SELECT balance FROM accounts WHERE id = %s", (account_id,))
            return result[0]['balance'] if result else None

        except Exception as e:
            log_system_error("BankingService.get_account_balance", str(e))
            return None

    def get_transaction_history(self, account_id: int) -> List[Dict]:
        """获取交易历史"""
        try:
            result = self.db_manager.execute_query('db2', """
                SELECT * FROM transactions
                WHERE from_account = %s OR to_account = %s
                ORDER BY timestamp DESC LIMIT 10
            """, (account_id, account_id))
            return result

        except Exception as e:
            log_system_error("BankingService.get_transaction_history", str(e))
            return []

class InventoryService:
    """库存管理服务类"""

    def __init__(self):
        self.db_manager = get_db_manager()

    def process_order(self, product_id: int, quantity: int, customer_id: int) -> bool:
        """处理订单 - 分布式事务示例"""
        connections = None
        tm = None

        try:
            connections = self.db_manager.get_all_connections()
            tm = EnhancedTransactionManager(connections)

            tm.begin_transaction()

            def check_inventory(conn, prod_id):
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT quantity FROM inventory WHERE product_id = %s", (prod_id,))
                result = cursor.fetchone()
                cursor.close()
                return result['quantity'] if result else 0

            def update_inventory(conn, prod_id, new_quantity):
                cursor = conn.cursor()
                cursor.execute("UPDATE inventory SET quantity = %s WHERE product_id = %s",
                             (new_quantity, prod_id))
                cursor.close()
                return cursor.rowcount > 0

            def create_order(conn, prod_id, qty, cust_id):
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO orders (product_id, quantity, customer_id, status, created_at)
                    VALUES (%s, %s, %s, 'CONFIRMED', NOW())
                """, (prod_id, qty, cust_id))
                cursor.close()
                return cursor.lastrowid

            # 检查库存
            current_stock = tm.execute_operation("participant_1", check_inventory, product_id)
            if current_stock < quantity:
                raise Exception(f"Insufficient stock. Available: {current_stock}, Required: {quantity}")

            # 更新库存
            tm.execute_operation("participant_1", update_inventory, product_id, current_stock - quantity)

            # 创建订单
            order_id = tm.execute_operation("participant_2", create_order,
                                          product_id, quantity, customer_id)

            # 准备和提交
            tm.prepare()
            tm.commit()

            log_system_info("InventoryService",
                          f"Order processed: Product {product_id}, Quantity {quantity}, Order ID {order_id}")
            return True

        except Exception as e:
            log_system_error("InventoryService.process_order", str(e))
            if tm:
                tm.rollback()
            return False
        finally:
            if tm:
                tm.cleanup()

class DistributedApplication:
    """分布式应用程序主类"""

    def __init__(self):
        self.banking_service = BankingService()
        self.inventory_service = InventoryService()

    def initialize_sample_data(self):
        """初始化示例数据"""
        try:
            # 创建示例账户
            self.banking_service.create_account(1011, 5000.0)
            self.banking_service.create_account(1012, 3000.0)
            self.banking_service.create_account(1013, 1000.0)

            # 创建示例库存
            conn = get_db_manager().get_connection('db1')
            cursor = conn.cursor()

            # 确保inventory表存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventory (
                    product_id INT PRIMARY KEY,
                    product_name VARCHAR(100),
                    quantity INT,
                    price DECIMAL(10, 2)
                )
            """)

            # 插入示例库存数据
            cursor.execute("INSERT IGNORE INTO inventory VALUES (111, 'Laptop', 50, 999.99)")
            cursor.execute("INSERT IGNORE INTO inventory VALUES (112, 'Mouse', 200, 29.99)")
            cursor.execute("INSERT IGNORE INTO inventory VALUES (113, 'Keyboard', 150, 79.99)")

            conn.commit()
            cursor.close()
            conn.close()

            # 创建订单表
            conn = get_db_manager().get_connection('db2')
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INT AUTO_INCREMENT PRIMARY KEY,
                    product_id INT,
                    quantity INT,
                    customer_id INT,
                    status VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            cursor.close()
            conn.close()

            log_system_info("DistributedApplication", "Sample data initialized successfully")

        except Exception as e:
            log_system_error("DistributedApplication.initialize_sample_data", str(e))

    def run_demo_scenarios(self):
        """运行演示场景"""
        print("=== 分布式数据库系统演示 ===\n")

        # 场景1：银行转账
        print("场景1：银行转账")
        print(f"账户1011余额: {self.banking_service.get_account_balance(1011)}")
        print(f"账户1012余额: {self.banking_service.get_account_balance(1012)}")

        success = self.banking_service.transfer_money(1011, 1012, 500.0)
        print(f"转账结果: {'成功' if success else '失败'}")

        print(f"转账后账户1011余额: {self.banking_service.get_account_balance(1011)}")
        print(f"转账后账户1012余额: {self.banking_service.get_account_balance(1012)}")
        print()

        # 场景2：库存管理
        print("场景2：库存管理")
        try:
            result = get_db_manager().execute_query('db1', "SELECT * FROM inventory WHERE product_id = 111")
            if result:
                print(f"产品111库存: {result[0]['quantity']}")

            success = self.inventory_service.process_order(111, 2, 2001)
            print(f"订单处理结果: {'成功' if success else '失败'}")

            result = get_db_manager().execute_query('db1', "SELECT * FROM inventory WHERE product_id = 111")
            if result:
                print(f"订单处理后产品111库存: {result[0]['quantity']}")
        except Exception as e:
            print(f"库存管理演示出错: {e}")

        print()

        # 场景3：异常处理（余额不足）
        print("场景3：异常处理（余额不足）")
        success = self.banking_service.transfer_money(1013, 1011, 2000.0)  # 余额不足
        print(f"转账结果: {'成功' if success else '失败（余额不足）'}")
        print()

        # 显示系统状态
        print("=== 系统状态 ===")
        status = get_db_manager().get_node_status()
        for node_id, node_status in status.items():
            print(f"{node_id}: {'可用' if node_status['available'] else '不可用'} "
                  f"({node_status['host']}:{node_status['port']})")

def main():
    """主函数"""
    try:
        app = DistributedApplication()

        # 初始化数据
        app.initialize_sample_data()

        # 运行演示
        app.run_demo_scenarios()

    except Exception as e:
        log_system_error("main", str(e))
        print(f"应用程序启动失败: {e}")
    finally:
        # 清理资源
        get_db_manager().close_all_connections()

if __name__ == "__main__":
    main()