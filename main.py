#!/usr/bin/env python3
"""
分布式数据库系统主启动脚本
提供命令行界面来管理和运行系统
"""
import argparse
import sys
import os
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import mysql.connector
        import flask
        import colorlog
        print("所有依赖已安装")
        return True
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_docker():
    """检查Docker是否可用"""
    try:
        result = subprocess.run(['docker', '--version'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("Docker 可用")
            return True
        else:
            print("Docker 不可用")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("Docker 未安装或不可用")
        return False

def start_databases():
    """启动数据库容器"""
    print("启动MySQL数据库容器...")

    # 检查容器是否已存在
    containers = ['mysql1', 'mysql2']
    for container in containers:
        try:
            # 检查容器是否存在
            result = subprocess.run(['docker', 'ps', '-a', '--filter', f'name={container}', '--format', '{{.Names}}'],
                                  capture_output=True, text=True)
            if container in result.stdout:
                print(f"容器 {container} 已存在，正在启动...")
                subprocess.run(['docker', 'start', container], check=True)
            else:
                print(f"创建并启动容器 {container}...")
                if container == 'mysql1':
                    subprocess.run([
                        'docker', 'run', '-d', '--name', 'mysql1',
                        '-e', 'MYSQL_ROOT_PASSWORD=password',
                        '-e', 'MYSQL_DATABASE=db1',
                        '-e', 'MYSQL_USER=dbuser',
                        '-e', 'MYSQL_PASSWORD=dbpass',
                        '-p', '3316:3306',  # 修改为3316端口
                        'mysql:8.4'
                    ], check=True)
                else:
                    subprocess.run([
                        'docker', 'run', '-d', '--name', 'mysql2',
                        '-e', 'MYSQL_ROOT_PASSWORD=password',
                        '-e', 'MYSQL_DATABASE=db2',
                        '-e', 'MYSQL_USER=dbuser',
                        '-e', 'MYSQL_PASSWORD=dbpass',
                        '-p', '3317:3306',  # 修改为3317端口
                        'mysql:8.4'
                    ], check=True)

            print(f"容器 {container} 启动成功")

        except subprocess.CalledProcessError as e:
            print(f"启动容器 {container} 失败: {e}")
            return False

    print("等待数据库服务启动...")
    time.sleep(30)  # 等待MySQL完全启动
    return True

def stop_databases():
    """停止数据库容器"""
    print("停止MySQL数据库容器...")

    containers = ['mysql1', 'mysql2']
    for container in containers:
        try:
            subprocess.run(['docker', 'stop', container], check=True)
            print(f"容器 {container} 已停止")
        except subprocess.CalledProcessError:
            print(f"容器 {container} 可能已经停止")

    return True

def remove_databases():
    """删除数据库容器"""
    print("删除MySQL数据库容器...")

    containers = ['mysql1', 'mysql2']
    for container in containers:
        try:
            subprocess.run(['docker', 'rm', '-f', container], check=True)
            print(f" 容器 {container} 已删除")
        except subprocess.CalledProcessError:
            print(f"容器 {container} 可能不存在")

    return True

def init_databases():
    """初始化数据库"""
    print("初始化数据库...")
    try:
        from init_databases import setup_databases
        return setup_databases()
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

def run_tests():
    """运行测试"""
    print("运行系统测试...")
    try:
        from test_distributed_system import run_tests
        return run_tests() == 0
    except Exception as e:
        print(f"测试运行失败: {e}")
        return False

def start_web_interface():
    """启动Web界面"""
    print("启动Web管理界面...")
    try:
        from web_interface import app, socketio
        from config import WebConfig

        print(f"Web界面将在 http://{WebConfig.HOST}:{WebConfig.PORT} 启动")

        # 尝试启动SocketIO服务器
        try:
            socketio.run(app,
                        host=WebConfig.HOST,
                        port=WebConfig.PORT,
                        debug=WebConfig.DEBUG)
        except Exception as socketio_error:
            print(f"⚠️ SocketIO启动失败: {socketio_error}")
            print("尝试使用标准Flask服务器...")
            # 回退到标准Flask服务器
            app.run(host=WebConfig.HOST,
                   port=WebConfig.PORT,
                   debug=WebConfig.DEBUG)

        return True
    except Exception as e:
        print(f"Web界面启动失败: {e}")
        print("可能的解决方案:")
        print("1. 检查端口是否被占用")
        print("2. 尝试运行: pip install --upgrade flask-socketio")
        print("3. 尝试运行: pip install --upgrade eventlet")
        return False

def run_demo():
    """运行演示程序"""
    print("运行分布式数据库演示...")
    try:
        from distributed_app import main
        main()
        return True
    except Exception as e:
        print(f"演示程序运行失败: {e}")
        return False

def show_status():
    """显示系统状态"""
    print("=== 分布式数据库系统状态 ===")

    # 检查Docker容器状态
    containers = ['mysql1', 'mysql2']
    for container in containers:
        try:
            result = subprocess.run(['docker', 'ps', '--filter', f'name={container}', '--format', '{{.Status}}'],
                                  capture_output=True, text=True)
            if result.stdout.strip():
                print(f"✅ {container}: {result.stdout.strip()}")
            else:
                print(f"{container}: 未运行")
        except subprocess.CalledProcessError:
            print(f"{container}: 状态未知")

    # 检查数据库连接
    try:
        from database_manager import get_db_manager
        status = get_db_manager().get_node_status()
        print("\n数据库连接状态:")
        for node_id, node_status in status.items():
            status_text = "可用" if node_status['available'] else "不可用"
            print(f"  {node_id}: {status_text} ({node_status['host']}:{node_status['port']})")
    except Exception as e:
        print(f"无法获取数据库状态: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='分布式数据库系统管理工具')
    parser.add_argument('command', choices=[
        'setup', 'start-db', 'stop-db', 'remove-db', 'init-db',
        'test', 'web', 'demo', 'status', 'all'
    ], help='要执行的命令')

    args = parser.parse_args()

    print("分布式数据库系统管理工具")
    print("=" * 50)

    if args.command == 'setup':
        print("执行完整系统设置...")
        if not check_dependencies():
            sys.exit(1)
        if not check_docker():
            sys.exit(1)
        if not start_databases():
            sys.exit(1)
        if not init_databases():
            sys.exit(1)
        print("\n系统设置完成！")
        print("现在可以运行: python main.py web 启动Web界面")

    elif args.command == 'start-db':
        if not check_docker():
            sys.exit(1)
        if not start_databases():
            sys.exit(1)

    elif args.command == 'stop-db':
        if not stop_databases():
            sys.exit(1)

    elif args.command == 'remove-db':
        if not remove_databases():
            sys.exit(1)

    elif args.command == 'init-db':
        if not init_databases():
            sys.exit(1)

    elif args.command == 'test':
        if not check_dependencies():
            sys.exit(1)
        if not run_tests():
            sys.exit(1)

    elif args.command == 'web':
        if not check_dependencies():
            sys.exit(1)
        start_web_interface()

    elif args.command == 'demo':
        if not check_dependencies():
            sys.exit(1)
        if not run_demo():
            sys.exit(1)

    elif args.command == 'status':
        show_status()

    elif args.command == 'all':
        print("执行完整流程...")
        if not check_dependencies():
            sys.exit(1)
        if not check_docker():
            sys.exit(1)
        if not start_databases():
            sys.exit(1)
        if not init_databases():
            sys.exit(1)
        if not run_tests():
            print("测试失败，但继续运行演示")
        if not run_demo():
            sys.exit(1)
        print("\n完整流程执行完成！")

if __name__ == "__main__":
    main()

