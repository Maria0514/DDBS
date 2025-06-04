"""
演示2PC事务的正确性
模拟两个并发事务对同一银行账户和库存的操作
展示事务的提交和回滚过程
"""

import threading
import time
from distributed_app import BankingService, InventoryService
from database_manager import get_db_manager
from logger import system_logger, log_system_info, log_system_error
from init_databases import setup_database_1, setup_database_2
from web_interface import socketio, app  # 导入 Flask 和 SocketIO 实例

# 创建银行服务和库存服务实例
banking_service = BankingService()
inventory_service = InventoryService()

def transfer_task(from_account, to_account, amount):
    """
    执行转账任务
    :param from_account: 转出账户ID
    :param to_account: 转入账户ID
    :param amount: 转账金额
    """
    try:
        # 执行转账操作
        success = banking_service.transfer_money(from_account, to_account, amount)
        
        if success:
            log_system_info("demo_2pc", f"Transfer succeeded: {from_account} -> {to_account}, Amount: {amount}")
            socketio.emit('transfer_completed', {
                'from_account': from_account,
                'to_account': to_account,
                'amount': amount,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            log_system_info("demo_2pc", f"Transfer failed: {from_account} -> {to_account}, Amount: {amount}")
            socketio.emit('transfer_failed', {
                'from_account': from_account,
                'to_account': to_account,
                'amount': amount,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
    
    except Exception as e:
        log_system_error("demo_2pc", f"Transfer error: {str(e)}")
        socketio.emit('transfer_error', {
            'error': str(e),
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        })

def inventory_task(product_id, quantity, customer_id):
    """
    执行库存任务
    :param product_id: 产品ID
    :param quantity: 订购数量
    :param customer_id: 客户ID
    """
    try:
        # 执行订单处理
        success = inventory_service.process_order(product_id, quantity, customer_id)
        
        if success:
            log_system_info("demo_2pc", f"Order succeeded: Product {product_id}, Quantity {quantity}, Customer {customer_id}")
            socketio.emit('order_completed', {
                'product_id': product_id,
                'quantity': quantity,
                'customer_id': customer_id,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            log_system_info("demo_2pc", f"Order failed: Product {product_id}, Quantity {quantity}, Customer {customer_id}")
            socketio.emit('order_failed', {
                'product_id': product_id,
                'quantity': quantity,
                'customer_id': customer_id,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
    
    except Exception as e:
        log_system_error("demo_2pc", f"Order error: {str(e)}")
        socketio.emit('order_error', {
            'error': str(e),
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        })

def initialize_demo_data():
    """
    初始化演示数据
    """
    # 初始化数据库1和数据库2
    setup_database_1()
    setup_database_2()

    # 确保账户存在并有足够的余额
    banking_service.create_account(2001, 1000.0)
    banking_service.create_account(2002, 1500.0)

    # 确保产品存在并有足够的库存
    conn = get_db_manager().get_connection('db1')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT IGNORE INTO inventory (product_id, product_name, quantity, price)
        VALUES (101, 'Laptop', 10, 999.99)
    """)
    conn.commit()
    cursor.close()
    conn.close()

def run_concurrent_transactions():
    """
    运行并发事务演示
    """
    # 初始化演示数据
    initialize_demo_data()

    # 创建线程，模拟两个用户同时操作同一账户和同一产品
    # 转账任务1：从账户2001转500到2002（成功）
    thread1 = threading.Thread(target=transfer_task, args=(2001, 2002, 500))
    
    # 转账任务2：从账户2001转600到2002（失败，余额不足）
    thread2 = threading.Thread(target=transfer_task, args=(2001, 2002, 600))
    
    # 库存任务1：订购产品101，数量5（成功）
    thread3 = threading.Thread(target=inventory_task, args=(101, 5, 3001))
    
    # 库存任务2：订购产品101，数量10（失败，库存不足）
    thread4 = threading.Thread(target=inventory_task, args=(101, 10, 3002))

    # 启动线程
    thread1.start()
    thread2.start()
    thread3.start()
    thread4.start()

    # 等待线程完成
    thread1.join()
    thread2.join()
    thread3.join()
    thread4.join()

    # 显示最终账户余额和产品库存
    final_balance_2001 = banking_service.get_account_balance(2001)
    final_balance_2002 = banking_service.get_account_balance(2002)
    
    conn = get_db_manager().get_connection('db1')
    cursor = conn.cursor()
    cursor.execute("SELECT quantity FROM inventory WHERE product_id = %s", (101,))
    result = cursor.fetchone()
    final_stock_101 = result['quantity'] if result else 0
    cursor.close()
    conn.close()

    log_system_info("demo_2pc", f"Final balance of account 2001: {final_balance_2001}")
    log_system_info("demo_2pc", f"Final balance of account 2002: {final_balance_2002}")
    log_system_info("demo_2pc", f"Final stock of product 101: {final_stock_101}")

if __name__ == "__main__":
    from database_manager import get_db_manager  # 确保可以访问数据库管理器
    import time

    # 运行演示
    run_concurrent_transactions()

    # 启动 Flask 应用
    socketio.run(app, host='0.0.0.0', port=5000)