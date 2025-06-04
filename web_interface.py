"""
Web可视化界面
提供分布式数据库系统的Web管理界面
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
import json
import threading
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, List
from config import WebConfig
from database_manager import get_db_manager
from distributed_app import BankingService, InventoryService
from logger import web_logger, log_web_request, log_system_info
from demo_2pc import run_concurrent_transactions 

def convert_decimal_and_datetime(obj):
    """转换Decimal和datetime对象为JSON可序列化的类型"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def process_query_result(data):
    """处理查询结果，转换Decimal和datetime类型"""
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    item[key] = convert_decimal_and_datetime(value)
    elif isinstance(data, dict):
        for key, value in data.items():
            data[key] = convert_decimal_and_datetime(value)
    return data

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = WebConfig.SECRET_KEY

# 创建SocketIO实例
try:
    socketio = SocketIO(app, async_mode=WebConfig.SOCKETIO_ASYNC_MODE, cors_allowed_origins="*")
except Exception as e:
    # 如果SocketIO初始化失败，尝试使用threading模式
    print(f"SocketIO初始化失败，尝试使用threading模式: {e}")
    socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# 全局服务实例
banking_service = BankingService()
inventory_service = InventoryService()

# 全局状态存储
system_status = {
    'databases': {},
    'transactions': [],
    'last_update': None
}

@app.route('/')
def index():
    """主页"""
    log_web_request('GET', '/', 200)
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """仪表板页面"""
    log_web_request('GET', '/dashboard', 200)
    return render_template('dashboard.html')

@app.route('/transactions')
def transactions():
    """事务管理页面"""
    log_web_request('GET', '/transactions', 200)
    return render_template('transactions.html')

@app.route('/monitoring')
def monitoring():
    """系统监控页面"""
    log_web_request('GET', '/monitoring', 200)
    return render_template('monitoring.html')

@app.route('/api/system/status')
def get_system_status():
    """获取系统状态API"""
    try:
        status = get_db_manager().get_node_status()
        log_web_request('GET', '/api/system/status', 200)
        return jsonify({
            'success': True,
            'data': status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        log_web_request('GET', '/api/system/status', 500)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/accounts')
def get_accounts():
    """获取所有账户信息"""
    try:
        accounts = get_db_manager().execute_query('db1', "SELECT * FROM accounts ORDER BY id")

        # 处理Decimal和datetime类型
        accounts = process_query_result(accounts)

        log_web_request('GET', '/api/accounts', 200)
        return jsonify({
            'success': True,
            'data': accounts
        })
    except Exception as e:
        log_web_request('GET', '/api/accounts', 500)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/accounts', methods=['POST'])
def create_account():
    """创建新账户"""
    try:
        data = request.get_json()
        account_id = data.get('account_id')
        initial_balance = data.get('initial_balance', 0)

        success = banking_service.create_account(account_id, initial_balance)

        if success:
            log_web_request('POST', '/api/accounts', 201)
            # 通知所有客户端
            socketio.emit('account_created', {
                'account_id': account_id,
                'balance': initial_balance
            })
            return jsonify({
                'success': True,
                'message': f'Account {account_id} created successfully'
            }), 201
        else:
            log_web_request('POST', '/api/accounts', 400)
            return jsonify({
                'success': False,
                'error': 'Failed to create account'
            }), 400

    except Exception as e:
        log_web_request('POST', '/api/accounts', 500)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transfer', methods=['POST'])
def transfer_money():
    """执行转账操作"""
    try:
        data = request.get_json()
        from_account = data.get('from_account')
        to_account = data.get('to_account')
        amount = float(data.get('amount'))

        # 执行转账
        success = banking_service.transfer_money(from_account, to_account, amount)

        if success:
            log_web_request('POST', '/api/transfer', 200)
            # 通知所有客户端
            socketio.emit('transfer_completed', {
                'from_account': from_account,
                'to_account': to_account,
                'amount': amount,
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({
                'success': True,
                'message': 'Transfer completed successfully'
            })
        else:
            log_web_request('POST', '/api/transfer', 400)
            return jsonify({
                'success': False,
                'error': 'Transfer failed'
            }), 400

    except Exception as e:
        log_web_request('POST', '/api/transfer', 500)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/inventory')
def get_inventory():
    """获取库存信息"""
    try:
        inventory = get_db_manager().execute_query('db1', "SELECT * FROM inventory ORDER BY product_id")

        # 转换Decimal类型为float，确保前端可以正确处理
        for item in inventory:
            if 'price' in item and item['price'] is not None:
                item['price'] = float(item['price'])

        log_web_request('GET', '/api/inventory', 200)
        return jsonify({
            'success': True,
            'data': inventory
        })
    except Exception as e:
        log_web_request('GET', '/api/inventory', 500)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/orders', methods=['POST'])
def process_order():
    """处理订单"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity'))
        customer_id = data.get('customer_id')

        success = inventory_service.process_order(product_id, quantity, customer_id)

        if success:
            log_web_request('POST', '/api/orders', 200)
            # 通知所有客户端
            socketio.emit('order_processed', {
                'product_id': product_id,
                'quantity': quantity,
                'customer_id': customer_id,
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({
                'success': True,
                'message': 'Order processed successfully'
            })
        else:
            log_web_request('POST', '/api/orders', 400)
            return jsonify({
                'success': False,
                'error': 'Order processing failed'
            }), 400

    except Exception as e:
        log_web_request('POST', '/api/orders', 500)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transactions/history/<int:account_id>')
def get_transaction_history(account_id):
    """获取账户交易历史"""
    try:
        history = banking_service.get_transaction_history(account_id)
        log_web_request('GET', f'/api/transactions/history/{account_id}', 200)
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        log_web_request('GET', f'/api/transactions/history/{account_id}', 500)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
@app.route('/api/test', methods=['POST'])
def run_test():
    """运行并发事务测试"""
    try:
        # 调用 demo_2pc.py 中的 run_concurrent_transactions 函数
        from demo_2pc import run_concurrent_transactions
        run_concurrent_transactions()
        
        return jsonify({
            'success': True,
            'message': 'Test completed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
# SocketIO事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接事件"""
    web_logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to distributed database system'})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接事件"""
    web_logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_status')
def handle_status_request():
    """处理状态请求"""
    try:
        status = get_db_manager().get_node_status()
        emit('status_update', status)
    except Exception as e:
        emit('error', {'message': str(e)})

# 新增事件监听器
@socketio.on('transfer_completed')
def handle_transfer_completed(data):
    """处理转账完成事件"""
    emit('transfer_completed', data)

@socketio.on('transfer_failed')
def handle_transfer_failed(data):
    """处理转账失败事件"""
    emit('transfer_failed', data)

@socketio.on('transfer_error')
def handle_transfer_error(data):
    """处理转账错误事件"""
    emit('transfer_error', data)

@socketio.on('order_completed')
def handle_order_completed(data):
    """处理订单完成事件"""
    emit('order_completed', data)

@socketio.on('order_failed')
def handle_order_failed(data):
    """处理订单失败事件"""
    emit('order_failed', data)

@socketio.on('order_error')
def handle_order_error(data):
    """处理订单错误事件"""
    emit('order_error', data)

def background_monitor():
    """后台监控线程"""
    while True:
        try:
            # 获取系统状态
            status = get_db_manager().get_node_status()

            # 广播状态更新
            socketio.emit('system_status', {
                'databases': status,
                'timestamp': datetime.now().isoformat()
            })

            time.sleep(5)  # 每5秒更新一次

        except Exception as e:
            web_logger.error(f"Background monitor error: {e}")
            time.sleep(10)

def start_background_monitor():
    """启动后台监控"""
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    log_system_info("WebInterface", "Background monitor started")

if __name__ == '__main__':
    # 启动后台监控
    start_background_monitor()

    # 启动Web服务器
    log_system_info("WebInterface", f"Starting web server on {WebConfig.HOST}:{WebConfig.PORT}")
    socketio.run(app,
                host=WebConfig.HOST,
                port=WebConfig.PORT,
                debug=WebConfig.DEBUG)