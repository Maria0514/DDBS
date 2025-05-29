#!/usr/bin/env python3
"""
简化的Web界面启动脚本
避免SSL和eventlet相关问题
"""

def start_web_simple():
    """启动简化的Web界面"""
    print("🚀 启动分布式数据库Web管理界面...")
    
    try:
        # 导入必要的模块
        from flask import Flask, render_template, request, jsonify
        from flask_socketio import SocketIO, emit
        from config import WebConfig
        from database_manager import get_db_manager
        from distributed_app import BankingService, InventoryService
        from datetime import datetime
        
        print("✅ 模块导入成功")
        
        # 创建Flask应用
        app = Flask(__name__)
        app.config['SECRET_KEY'] = WebConfig.SECRET_KEY
        
        # 创建SocketIO实例（使用threading模式）
        socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")
        
        # 创建服务实例
        banking_service = BankingService()
        inventory_service = InventoryService()
        
        print("✅ 应用初始化成功")
        
        # 基本路由
        @app.route('/')
        def index():
            return render_template('index.html')
        
        @app.route('/dashboard')
        def dashboard():
            return render_template('dashboard.html')
        
        @app.route('/api/system/status')
        def get_system_status():
            try:
                status = get_db_manager().get_node_status()
                return jsonify({
                    'success': True,
                    'data': status,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/accounts')
        def get_accounts():
            try:
                accounts = get_db_manager().execute_query('db1', "SELECT * FROM accounts ORDER BY id")
                return jsonify({
                    'success': True,
                    'data': accounts
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/accounts', methods=['POST'])
        def create_account():
            try:
                data = request.get_json()
                account_id = data.get('account_id')
                initial_balance = data.get('initial_balance', 0)
                
                success = banking_service.create_account(account_id, initial_balance)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Account {account_id} created successfully'
                    }), 201
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Failed to create account'
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @app.route('/api/transfer', methods=['POST'])
        def transfer_money():
            try:
                data = request.get_json()
                from_account = data.get('from_account')
                to_account = data.get('to_account')
                amount = float(data.get('amount'))
                
                success = banking_service.transfer_money(from_account, to_account, amount)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': 'Transfer completed successfully'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Transfer failed'
                    }), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        # SocketIO事件
        @socketio.on('connect')
        def handle_connect():
            print(f"客户端连接: {request.sid}")
            emit('connected', {'message': 'Connected to distributed database system'})
        
        @socketio.on('disconnect')
        def handle_disconnect():
            print(f"客户端断开: {request.sid}")
        
        # 启动服务器
        host = WebConfig.HOST
        port = WebConfig.PORT
        
        print(f"🌐 Web界面启动地址: http://{host}:{port}")
        print("📊 可用页面:")
        print(f"  - 主页: http://{host}:{port}/")
        print(f"  - 仪表板: http://{host}:{port}/dashboard")
        print(f"  - 系统状态API: http://{host}:{port}/api/system/status")
        print("\n按 Ctrl+C 停止服务器")
        
        # 使用threading模式启动
        socketio.run(app, 
                    host=host, 
                    port=port, 
                    debug=False,
                    use_reloader=False)
        
    except Exception as e:
        print(f"❌ Web界面启动失败: {e}")
        print("\n可能的解决方案:")
        print("1. 检查端口5000是否被占用")
        print("2. 确保数据库容器正在运行")
        print("3. 检查依赖是否正确安装")
        return False

if __name__ == "__main__":
    start_web_simple()
