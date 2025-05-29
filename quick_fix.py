#!/usr/bin/env python3
"""
快速修复脚本 - 自动诊断和修复常见的数据库连接问题
"""

import subprocess
import time
import mysql.connector
from datetime import datetime

def run_command(command):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

def check_and_fix_containers():
    """检查并修复Docker容器问题"""
    print("🔍 检查Docker容器状态...")
    
    containers = ['mysql1', 'mysql2']
    fixed = False
    
    for container in containers:
        success, stdout, stderr = run_command(f"docker ps -q -f name={container}")
        
        if not stdout:  # 容器未运行
            print(f"❌ 容器 {container} 未运行，尝试启动...")
            
            # 检查容器是否存在但已停止
            success, stdout, stderr = run_command(f"docker ps -a -q -f name={container}")
            
            if stdout:  # 容器存在但已停止
                print(f"🔄 启动容器 {container}...")
                success, stdout, stderr = run_command(f"docker start {container}")
                
                if success:
                    print(f"✅ 容器 {container} 启动成功")
                    fixed = True
                else:
                    print(f"❌ 容器 {container} 启动失败: {stderr}")
            else:
                print(f"❌ 容器 {container} 不存在，需要重新创建")
        else:
            print(f"✅ 容器 {container} 正在运行")
    
    return fixed

def wait_for_mysql_ready():
    """等待MySQL完全启动"""
    print("⏳ 等待MySQL服务完全启动...")
    
    databases = [
        {'host': 'localhost', 'port': 3316, 'name': 'db1'},
        {'host': 'localhost', 'port': 3317, 'name': 'db2'}
    ]
    
    max_wait = 60  # 最大等待60秒
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        all_ready = True
        
        for db in databases:
            try:
                conn = mysql.connector.connect(
                    host=db['host'],
                    port=db['port'],
                    user='root',
                    password='password',
                    connection_timeout=5
                )
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                conn.close()
                print(f"✅ {db['name']} 连接正常")
            except Exception as e:
                print(f"⏳ {db['name']} 还未就绪: {e}")
                all_ready = False
                break
        
        if all_ready:
            print("🎉 所有MySQL服务已就绪")
            return True
        
        time.sleep(2)
    
    print("❌ MySQL服务启动超时")
    return False

def test_database_manager():
    """测试数据库管理器"""
    print("🧪 测试数据库管理器...")
    
    try:
        from database_manager import get_db_manager
        
        db_manager = get_db_manager()
        
        # 测试连接
        conn1 = db_manager.get_connection('db1')
        conn1.close()
        print("✅ db1 连接测试成功")
        
        conn2 = db_manager.get_connection('db2')
        conn2.close()
        print("✅ db2 连接测试成功")
        
        # 测试查询
        result = db_manager.execute_query('db1', 'SELECT COUNT(*) as count FROM accounts')
        print(f"✅ db1 查询测试成功: {result[0]['count']} 个账户")
        
        result = db_manager.execute_query('db2', 'SELECT COUNT(*) as count FROM transactions')
        print(f"✅ db2 查询测试成功: {result[0]['count']} 个事务")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库管理器测试失败: {e}")
        return False

def restart_all_containers():
    """重启所有容器"""
    print("🔄 重启所有数据库容器...")
    
    containers = ['mysql1', 'mysql2']
    
    for container in containers:
        print(f"🔄 重启容器 {container}...")
        success, stdout, stderr = run_command(f"docker restart {container}")
        
        if success:
            print(f"✅ 容器 {container} 重启成功")
        else:
            print(f"❌ 容器 {container} 重启失败: {stderr}")
    
    return True

def quick_fix():
    """执行快速修复"""
    print(f"\n{'='*60}")
    print(f"🚀 分布式数据库快速修复工具")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # 步骤1: 检查并修复容器
    containers_fixed = check_and_fix_containers()
    
    if containers_fixed:
        # 步骤2: 等待MySQL就绪
        if wait_for_mysql_ready():
            # 步骤3: 测试数据库管理器
            if test_database_manager():
                print(f"\n🎉 快速修复成功！系统已恢复正常")
                return True
            else:
                print(f"\n⚠️ 数据库管理器仍有问题，尝试重启容器...")
                restart_all_containers()
                if wait_for_mysql_ready():
                    if test_database_manager():
                        print(f"\n🎉 重启后修复成功！")
                        return True
        else:
            print(f"\n⚠️ MySQL启动超时，尝试重启容器...")
            restart_all_containers()
            if wait_for_mysql_ready():
                if test_database_manager():
                    print(f"\n🎉 重启后修复成功！")
                    return True
    else:
        # 直接测试数据库管理器
        if test_database_manager():
            print(f"\n🎉 系统正常，无需修复")
            return True
        else:
            print(f"\n⚠️ 检测到问题，尝试重启容器...")
            restart_all_containers()
            if wait_for_mysql_ready():
                if test_database_manager():
                    print(f"\n🎉 重启后修复成功！")
                    return True
    
    print(f"\n❌ 快速修复失败，请检查系统配置")
    print("建议:")
    print("1. 检查Docker服务是否正常")
    print("2. 检查系统资源是否充足")
    print("3. 查看容器日志: docker logs mysql1 && docker logs mysql2")
    print("4. 尝试完全重建: docker-compose down && docker-compose up -d")
    
    return False

def show_system_info():
    """显示系统信息"""
    print(f"\n{'='*40}")
    print("系统信息")
    print(f"{'='*40}")
    
    # Docker版本
    success, stdout, stderr = run_command("docker --version")
    if success:
        print(f"Docker: {stdout}")
    
    # 容器状态
    success, stdout, stderr = run_command("docker ps -a --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'")
    if success:
        print(f"\n容器状态:")
        print(stdout)
    
    # 系统资源
    success, stdout, stderr = run_command("docker stats --no-stream --format 'table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}'")
    if success:
        print(f"\n资源使用:")
        print(stdout)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'info':
        show_system_info()
    else:
        quick_fix()
