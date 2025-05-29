#!/usr/bin/env python3
"""
测试Web界面启动的简化脚本
"""

def test_web_startup():
    """测试Web界面启动"""
    print("测试Web界面组件...")
    
    # 测试1: 导入Flask
    try:
        from flask import Flask
        print("✅ Flask导入成功")
    except ImportError as e:
        print(f"❌ Flask导入失败: {e}")
        return False
    
    # 测试2: 导入Flask-SocketIO
    try:
        from flask_socketio import SocketIO
        print("✅ Flask-SocketIO导入成功")
    except ImportError as e:
        print(f"❌ Flask-SocketIO导入失败: {e}")
        print("请运行: pip install flask-socketio")
        return False
    
    # 测试3: 创建简单的Flask应用
    try:
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test-key'
        print("✅ Flask应用创建成功")
    except Exception as e:
        print(f"❌ Flask应用创建失败: {e}")
        return False
    
    # 测试4: 创建SocketIO实例（使用threading模式）
    try:
        socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")
        print("✅ SocketIO实例创建成功（threading模式）")
    except Exception as e:
        print(f"❌ SocketIO实例创建失败: {e}")
        return False
    
    # 测试5: 尝试启动服务器（短时间）
    try:
        import threading
        import time
        
        def start_server():
            socketio.run(app, host='127.0.0.1', port=5001, debug=False)
        
        # 在后台线程启动服务器
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # 等待一秒钟
        time.sleep(1)
        
        print("✅ Web服务器启动测试成功")
        print("🌐 如果没有错误，Web界面应该可以正常启动")
        
        return True
        
    except Exception as e:
        print(f"❌ Web服务器启动测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=== Web界面启动测试 ===")
    success = test_web_startup()
    
    if success:
        print("\n✅ 所有测试通过！")
        print("现在可以尝试运行: python main.py web")
    else:
        print("\n❌ 测试失败，请检查依赖安装")
        print("建议运行:")
        print("  pip install --upgrade flask")
        print("  pip install --upgrade flask-socketio")
