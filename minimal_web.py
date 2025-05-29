#!/usr/bin/env python3
"""
最小化的Web界面，用于测试和演示
"""

from flask import Flask, jsonify, render_template_string
from database_manager import get_db_manager
from distributed_app import BankingService

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-key'

# 创建服务实例
banking_service = BankingService()

# 简单的HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>分布式数据库系统</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .info { background-color: #d1ecf1; color: #0c5460; }
        button { padding: 10px 20px; margin: 5px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }
        button:hover { background: #0056b3; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏦 分布式数据库系统</h1>
        
        <div class="status info">
            <h3>系统状态</h3>
            <p>✅ Web界面运行正常</p>
            <p>🔗 数据库连接状态: <span id="db-status">检查中...</span></p>
        </div>
        
        <div class="status success">
            <h3>可用功能</h3>
            <ul>
                <li><a href="/api/system/status">系统状态API</a></li>
                <li><a href="/api/accounts">账户列表API</a></li>
                <li><a href="/test">功能测试页面</a></li>
            </ul>
        </div>
        
        <div>
            <h3>快速操作</h3>
            <button onclick="checkStatus()">检查系统状态</button>
            <button onclick="listAccounts()">查看账户</button>
            <button onclick="createTestAccount()">创建测试账户</button>
        </div>
        
        <div id="result" style="margin-top: 20px;"></div>
    </div>
    
    <script>
        function checkStatus() {
            fetch('/api/system/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('result').innerHTML = 
                        '<div class="status success"><h4>系统状态</h4><pre>' + 
                        JSON.stringify(data, null, 2) + '</pre></div>';
                })
                .catch(error => {
                    document.getElementById('result').innerHTML = 
                        '<div class="status error"><h4>错误</h4><p>' + error + '</p></div>';
                });
        }
        
        function listAccounts() {
            fetch('/api/accounts')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        let html = '<div class="status success"><h4>账户列表</h4><table><tr><th>账户ID</th><th>余额</th></tr>';
                        data.data.forEach(account => {
                            html += `<tr><td>${account[0]}</td><td>¥${account[1]}</td></tr>`;
                        });
                        html += '</table></div>';
                        document.getElementById('result').innerHTML = html;
                    } else {
                        document.getElementById('result').innerHTML = 
                            '<div class="status error"><h4>错误</h4><p>' + data.error + '</p></div>';
                    }
                })
                .catch(error => {
                    document.getElementById('result').innerHTML = 
                        '<div class="status error"><h4>错误</h4><p>' + error + '</p></div>';
                });
        }
        
        function createTestAccount() {
            const accountId = Math.floor(Math.random() * 9000) + 1000;
            fetch('/api/accounts', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({account_id: accountId, initial_balance: 1000})
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('result').innerHTML = 
                            '<div class="status success"><h4>成功</h4><p>' + data.message + '</p></div>';
                    } else {
                        document.getElementById('result').innerHTML = 
                            '<div class="status error"><h4>错误</h4><p>' + data.error + '</p></div>';
                    }
                })
                .catch(error => {
                    document.getElementById('result').innerHTML = 
                        '<div class="status error"><h4>错误</h4><p>' + error + '</p></div>';
                });
        }
        
        // 页面加载时检查数据库状态
        window.onload = function() {
            fetch('/api/system/status')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('db-status').innerHTML = '✅ 连接正常';
                    } else {
                        document.getElementById('db-status').innerHTML = '❌ 连接失败';
                    }
                })
                .catch(error => {
                    document.getElementById('db-status').innerHTML = '❌ 连接失败';
                });
        };
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/system/status')
def get_system_status():
    """获取系统状态"""
    try:
        status = get_db_manager().get_node_status()
        return jsonify({
            'success': True,
            'data': status,
            'message': '系统运行正常'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/accounts')
def get_accounts():
    """获取账户列表"""
    try:
        accounts = get_db_manager().execute_query('db1', "SELECT id, balance FROM accounts ORDER BY id")
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
    """创建账户"""
    try:
        from flask import request
        data = request.get_json()
        account_id = data.get('account_id')
        initial_balance = data.get('initial_balance', 0)
        
        success = banking_service.create_account(account_id, initial_balance)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'账户 {account_id} 创建成功，初始余额 ¥{initial_balance}'
            })
        else:
            return jsonify({
                'success': False,
                'error': '账户创建失败'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 启动最小化Web界面...")
    print("🌐 访问地址: http://localhost:5000")
    print("📊 功能: 系统状态查看、账户管理")
    print("按 Ctrl+C 停止服务器\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
