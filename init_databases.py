"""
数据库初始化脚本
创建分布式数据库系统所需的数据库和表结构
"""
import mysql.connector
from mysql.connector import Error
import sys
import time
from config import DatabaseConfig
from logger import system_logger, log_system_info, log_system_error

def wait_for_database(host, port, user, password, max_retries=30, retry_interval=2):
    """等待数据库服务启动"""
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connection_timeout=5
            )
            conn.close()
            log_system_info("DatabaseInit", f"Database {host}:{port} is ready")
            return True
        except Error as e:
            if attempt < max_retries - 1:
                log_system_info("DatabaseInit",
                               f"Waiting for database {host}:{port} (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                log_system_error("DatabaseInit",
                                f"Failed to connect to database {host}:{port} after {max_retries} attempts: {e}")
                return False
    return False

def setup_database_1():
    """设置数据库1（账户和库存数据）"""
    try:
        # 等待数据库启动
        if not wait_for_database(DatabaseConfig.DB1_HOST, DatabaseConfig.DB1_PORT,
                                DatabaseConfig.DB1_USER, DatabaseConfig.DB1_PASSWORD):
            return False

        # 连接到MySQL服务器
        conn = mysql.connector.connect(
            host=DatabaseConfig.DB1_HOST,
            port=DatabaseConfig.DB1_PORT,
            user=DatabaseConfig.DB1_USER,
            password=DatabaseConfig.DB1_PASSWORD
        )
        cursor = conn.cursor()

        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DatabaseConfig.DB1_DATABASE}")
        cursor.execute(f"USE {DatabaseConfig.DB1_DATABASE}")

        # 创建账户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INT PRIMARY KEY,
            balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_balance (balance)
        )
        """)

        # 创建库存表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            product_id INT PRIMARY KEY,
            product_name VARCHAR(100) NOT NULL,
            quantity INT NOT NULL DEFAULT 0,
            price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_quantity (quantity),
            INDEX idx_price (price)
        )
        """)

        # 插入示例数据
        cursor.execute("""
        INSERT IGNORE INTO accounts (id, balance) VALUES
        (1001, 5000.00),
        (1002, 3000.00),
        (1003, 1000.00),
        (1004, 2500.00),
        (1005, 4000.00)
        """)

        cursor.execute("""
        INSERT IGNORE INTO inventory (product_id, product_name, quantity, price) VALUES
        (101, 'Laptop', 50, 999.99),
        (102, 'Mouse', 200, 29.99),
        (103, 'Keyboard', 150, 79.99),
        (104, 'Monitor', 75, 299.99),
        (105, 'Headphones', 120, 149.99)
        """)

        conn.commit()
        cursor.close()
        conn.close()

        log_system_info("DatabaseInit", f"Database {DatabaseConfig.DB1_DATABASE} setup completed")
        return True

    except Error as e:
        log_system_error("DatabaseInit", f"Failed to setup database 1: {e}")
        return False

def setup_database_2():
    """设置数据库2（交易和订单数据）"""
    try:
        # 等待数据库启动
        if not wait_for_database(DatabaseConfig.DB2_HOST, DatabaseConfig.DB2_PORT,
                                DatabaseConfig.DB2_USER, DatabaseConfig.DB2_PASSWORD):
            return False

        # 连接到MySQL服务器
        conn = mysql.connector.connect(
            host=DatabaseConfig.DB2_HOST,
            port=DatabaseConfig.DB2_PORT,
            user=DatabaseConfig.DB2_USER,
            password=DatabaseConfig.DB2_PASSWORD
        )
        cursor = conn.cursor()

        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DatabaseConfig.DB2_DATABASE}")
        cursor.execute(f"USE {DatabaseConfig.DB2_DATABASE}")

        # 创建交易记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            from_account INT,
            to_account INT,
            amount DECIMAL(10, 2) NOT NULL,
            transaction_type VARCHAR(20) NOT NULL DEFAULT 'TRANSFER',
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_from_account (from_account),
            INDEX idx_to_account (to_account),
            INDEX idx_timestamp (timestamp),
            INDEX idx_status (status)
        )
        """)

        # 创建订单表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            customer_id INT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            total_amount DECIMAL(10, 2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_product_id (product_id),
            INDEX idx_customer_id (customer_id),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        )
        """)

        # 创建事务日志表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            transaction_id VARCHAR(100) NOT NULL,
            participant_id VARCHAR(50) NOT NULL,
            operation_type VARCHAR(20) NOT NULL,
            status VARCHAR(20) NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_transaction_id (transaction_id),
            INDEX idx_participant_id (participant_id),
            INDEX idx_timestamp (timestamp)
        )
        """)

        conn.commit()
        cursor.close()
        conn.close()

        log_system_info("DatabaseInit", f"Database {DatabaseConfig.DB2_DATABASE} setup completed")
        return True

    except Error as e:
        log_system_error("DatabaseInit", f"Failed to setup database 2: {e}")
        return False

def verify_setup():
    """验证数据库设置"""
    try:
        # 验证数据库1
        conn1 = mysql.connector.connect(**DatabaseConfig.get_db1_config())
        cursor1 = conn1.cursor()

        cursor1.execute("SHOW TABLES")
        tables1 = [table[0] for table in cursor1.fetchall()]
        expected_tables1 = ['accounts', 'inventory']

        for table in expected_tables1:
            if table not in tables1:
                log_system_error("DatabaseInit", f"Table {table} not found in database 1")
                return False

        cursor1.execute("SELECT COUNT(*) FROM accounts")
        account_count = cursor1.fetchone()[0]

        cursor1.execute("SELECT COUNT(*) FROM inventory")
        inventory_count = cursor1.fetchone()[0]

        cursor1.close()
        conn1.close()

        # 验证数据库2
        conn2 = mysql.connector.connect(**DatabaseConfig.get_db2_config())
        cursor2 = conn2.cursor()

        cursor2.execute("SHOW TABLES")
        tables2 = [table[0] for table in cursor2.fetchall()]
        expected_tables2 = ['transactions', 'orders', 'transaction_logs']

        for table in expected_tables2:
            if table not in tables2:
                log_system_error("DatabaseInit", f"Table {table} not found in database 2")
                return False

        cursor2.close()
        conn2.close()

        log_system_info("DatabaseInit",
                       f"Database verification completed - Accounts: {account_count}, Products: {inventory_count}")
        return True

    except Error as e:
        log_system_error("DatabaseInit", f"Database verification failed: {e}")
        return False

def setup_databases():
    """设置所有数据库"""
    print("开始初始化分布式数据库系统...")

    success = True

    # 设置数据库1
    print("设置数据库1...")
    if not setup_database_1():
        print("数据库1设置失败")
        success = False
    else:
        print("数据库1设置成功")

    # 设置数据库2
    print("设置数据库2...")
    if not setup_database_2():
        print("数据库2设置失败")
        success = False
    else:
        print("数据库2设置成功")

    # 验证设置
    if success:
        print("验证数据库设置...")
        if verify_setup():
            print("数据库验证成功")
            print("\n分布式数据库系统初始化完成！")
        else:
            print("数据库验证失败")
            success = False

    if not success:
        print("\n数据库初始化失败，请检查错误信息")
        sys.exit(1)

    return success

if __name__ == "__main__":
    setup_databases()