#!/usr/bin/env python3
"""
数据库监控脚本
实时监控分布式数据库系统的状态
"""

import time
import datetime
from database_manager import get_db_manager
from logger import database_logger

def check_database_status():
    """检查数据库状态"""
    try:
        db_manager = get_db_manager()
        status = db_manager.get_node_status()
        
        print(f"\n{'='*50}")
        print(f"数据库状态检查 - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*50}")
        
        all_healthy = True
        for node_id, node_status in status.items():
            status_icon = "✅" if node_status['available'] else "❌"
            status_text = "可用" if node_status['available'] else "不可用"
            
            print(f"{status_icon} {node_id}: {status_text}")
            print(f"   地址: {node_status['host']}:{node_status['port']}")
            print(f"   数据库: {node_status['database']}")
            print(f"   最后检查: {node_status['last_check']}")
            
            if not node_status['available']:
                all_healthy = False
        
        if all_healthy:
            print(f"\n🎉 所有数据库节点运行正常")
        else:
            print(f"\n⚠️  有数据库节点不可用")
            
        return all_healthy
        
    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
        return False

def test_database_operations():
    """测试数据库操作"""
    try:
        db_manager = get_db_manager()
        
        print(f"\n{'='*30}")
        print("数据库操作测试")
        print(f"{'='*30}")
        
        # 测试db1查询
        try:
            result = db_manager.execute_query('db1', 'SELECT COUNT(*) as count FROM accounts')
            print(f"✅ db1查询成功: {result[0]['count']} 个账户")
        except Exception as e:
            print(f"❌ db1查询失败: {e}")
        
        # 测试db2查询
        try:
            result = db_manager.execute_query('db2', 'SELECT COUNT(*) as count FROM transactions')
            print(f"✅ db2查询成功: {result[0]['count']} 个事务记录")
        except Exception as e:
            print(f"❌ db2查询失败: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ 操作测试失败: {e}")
        return False

def monitor_continuous(interval=30):
    """连续监控模式"""
    print("🔍 开始连续监控模式...")
    print(f"📊 检查间隔: {interval}秒")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            healthy = check_database_status()
            
            if healthy:
                test_database_operations()
            
            print(f"\n⏰ 下次检查将在 {interval} 秒后进行...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 监控已停止")

def monitor_once():
    """单次检查模式"""
    print("🔍 执行单次状态检查...\n")
    
    healthy = check_database_status()
    
    if healthy:
        test_database_operations()
    
    return healthy

def show_docker_status():
    """显示Docker容器状态"""
    import subprocess
    
    print(f"\n{'='*30}")
    print("Docker容器状态")
    print(f"{'='*30}")
    
    try:
        result = subprocess.run(['docker', 'ps', '-a', '--format', 
                               'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}'], 
                               capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"❌ 无法获取Docker状态: {e}")

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'monitor':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            monitor_continuous(interval)
        elif sys.argv[1] == 'docker':
            show_docker_status()
        elif sys.argv[1] == 'check':
            monitor_once()
        else:
            print("用法:")
            print("  python monitor_database.py check     - 单次检查")
            print("  python monitor_database.py monitor [间隔] - 连续监控")
            print("  python monitor_database.py docker    - 显示Docker状态")
    else:
        # 默认执行单次检查
        monitor_once()

if __name__ == "__main__":
    main()
