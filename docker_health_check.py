#!/usr/bin/env python3
"""
Docker容器健康检查和自动重启脚本
"""

import subprocess
import time
import datetime
import sys

def run_command(command):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_container_status(container_name):
    """检查容器状态"""
    success, stdout, stderr = run_command(f"docker ps -q -f name={container_name}")
    
    if success and stdout.strip():
        return "running"
    
    # 检查是否存在但未运行
    success, stdout, stderr = run_command(f"docker ps -a -q -f name={container_name}")
    if success and stdout.strip():
        return "stopped"
    
    return "not_found"

def get_container_uptime(container_name):
    """获取容器运行时间"""
    success, stdout, stderr = run_command(f"docker ps --format '{{{{.Status}}}}' -f name={container_name}")
    
    if success and stdout.strip():
        return stdout.strip()
    return "Unknown"

def restart_container(container_name):
    """重启容器"""
    print(f"🔄 正在重启容器 {container_name}...")
    
    success, stdout, stderr = run_command(f"docker restart {container_name}")
    
    if success:
        print(f"✅ 容器 {container_name} 重启成功")
        return True
    else:
        print(f"❌ 容器 {container_name} 重启失败: {stderr}")
        return False

def start_container(container_name):
    """启动容器"""
    print(f"🚀 正在启动容器 {container_name}...")
    
    success, stdout, stderr = run_command(f"docker start {container_name}")
    
    if success:
        print(f"✅ 容器 {container_name} 启动成功")
        return True
    else:
        print(f"❌ 容器 {container_name} 启动失败: {stderr}")
        return False

def check_mysql_connectivity(host, port, max_retries=3):
    """检查MySQL连接性"""
    import mysql.connector
    
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user='root',
                password='password',
                connection_timeout=5
            )
            conn.close()
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print(f"❌ MySQL连接失败 {host}:{port} - {e}")
    
    return False

def health_check():
    """执行健康检查"""
    print(f"\n{'='*60}")
    print(f"Docker容器健康检查 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    containers = [
        {'name': 'mysql1', 'host': 'localhost', 'port': 3316},
        {'name': 'mysql2', 'host': 'localhost', 'port': 3317}
    ]
    
    all_healthy = True
    
    for container in containers:
        name = container['name']
        host = container['host']
        port = container['port']
        
        print(f"\n🔍 检查容器: {name}")
        
        # 检查容器状态
        status = check_container_status(name)
        
        if status == "running":
            uptime = get_container_uptime(name)
            print(f"✅ 容器状态: 运行中 ({uptime})")
            
            # 检查MySQL连接
            if check_mysql_connectivity(host, port):
                print(f"✅ MySQL连接: 正常 ({host}:{port})")
            else:
                print(f"❌ MySQL连接: 失败 ({host}:{port})")
                print(f"🔄 尝试重启容器...")
                if restart_container(name):
                    time.sleep(10)  # 等待容器完全启动
                    if check_mysql_connectivity(host, port):
                        print(f"✅ 重启后MySQL连接恢复正常")
                    else:
                        print(f"❌ 重启后MySQL连接仍然失败")
                        all_healthy = False
                else:
                    all_healthy = False
                    
        elif status == "stopped":
            print(f"❌ 容器状态: 已停止")
            if start_container(name):
                time.sleep(10)  # 等待容器完全启动
                if check_mysql_connectivity(host, port):
                    print(f"✅ 启动后MySQL连接正常")
                else:
                    print(f"❌ 启动后MySQL连接失败")
                    all_healthy = False
            else:
                all_healthy = False
                
        else:
            print(f"❌ 容器状态: 未找到")
            all_healthy = False
    
    print(f"\n{'='*60}")
    if all_healthy:
        print("🎉 所有容器健康检查通过")
    else:
        print("⚠️  发现容器健康问题")
    print(f"{'='*60}")
    
    return all_healthy

def continuous_monitoring(interval=60):
    """连续监控模式"""
    print(f"🔍 开始连续监控模式...")
    print(f"📊 检查间隔: {interval}秒")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            health_check()
            print(f"\n⏰ 下次检查将在 {interval} 秒后进行...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 监控已停止")

def show_docker_info():
    """显示Docker信息"""
    print(f"\n{'='*40}")
    print("Docker容器信息")
    print(f"{'='*40}")
    
    success, stdout, stderr = run_command("docker ps -a --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'")
    if success:
        print(stdout)
    else:
        print(f"❌ 获取Docker信息失败: {stderr}")

def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'monitor':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            continuous_monitoring(interval)
        elif sys.argv[1] == 'info':
            show_docker_info()
        elif sys.argv[1] == 'check':
            health_check()
        else:
            print("用法:")
            print("  python docker_health_check.py check           - 单次健康检查")
            print("  python docker_health_check.py monitor [间隔]  - 连续监控")
            print("  python docker_health_check.py info            - 显示Docker信息")
    else:
        # 默认执行单次检查
        health_check()

if __name__ == "__main__":
    main()
