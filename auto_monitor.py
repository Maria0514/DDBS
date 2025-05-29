#!/usr/bin/env python3
"""
自动监控和修复服务
持续监控数据库状态，自动修复问题
"""

import time
import threading
import signal
import sys
from datetime import datetime, timedelta
from database_manager import get_db_manager
from quick_fix import quick_fix, test_database_manager

class AutoMonitor:
    def __init__(self, check_interval=30, auto_fix=True):
        self.check_interval = check_interval
        self.auto_fix = auto_fix
        self.running = False
        self.last_check = None
        self.last_fix = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] [{level}] {message}")
    
    def check_system_health(self):
        """检查系统健康状态"""
        try:
            # 测试数据库管理器
            if test_database_manager():
                self.consecutive_failures = 0
                self.log("✅ 系统健康检查通过")
                return True
            else:
                self.consecutive_failures += 1
                self.log(f"❌ 系统健康检查失败 (连续失败: {self.consecutive_failures})", "ERROR")
                return False
                
        except Exception as e:
            self.consecutive_failures += 1
            self.log(f"❌ 健康检查异常: {e} (连续失败: {self.consecutive_failures})", "ERROR")
            return False
    
    def attempt_auto_fix(self):
        """尝试自动修复"""
        if not self.auto_fix:
            self.log("⚠️ 自动修复已禁用", "WARN")
            return False
        
        # 避免频繁修复
        if self.last_fix and datetime.now() - self.last_fix < timedelta(minutes=2):
            self.log("⚠️ 距离上次修复时间太短，跳过自动修复", "WARN")
            return False
        
        self.log("🔧 开始自动修复...")
        self.last_fix = datetime.now()
        
        try:
            if quick_fix():
                self.log("🎉 自动修复成功")
                self.consecutive_failures = 0
                return True
            else:
                self.log("❌ 自动修复失败", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ 自动修复异常: {e}", "ERROR")
            return False
    
    def send_alert(self, message):
        """发送告警（可扩展为邮件、短信等）"""
        self.log(f"🚨 告警: {message}", "ALERT")
        
        # 这里可以添加邮件、短信、Webhook等告警方式
        # 例如：
        # send_email(message)
        # send_webhook(message)
    
    def monitor_loop(self):
        """监控循环"""
        self.log(f"🚀 开始自动监控服务")
        self.log(f"📊 检查间隔: {self.check_interval}秒")
        self.log(f"🔧 自动修复: {'启用' if self.auto_fix else '禁用'}")
        
        while self.running:
            try:
                self.last_check = datetime.now()
                
                # 执行健康检查
                if self.check_system_health():
                    # 系统正常
                    if self.consecutive_failures == 0:
                        self.log("💚 系统运行正常")
                    else:
                        self.log("💚 系统已恢复正常")
                        self.consecutive_failures = 0
                else:
                    # 系统异常
                    if self.consecutive_failures >= self.max_consecutive_failures:
                        # 连续失败次数过多，发送告警
                        self.send_alert(f"系统连续失败 {self.consecutive_failures} 次")
                        
                        # 尝试自动修复
                        if self.attempt_auto_fix():
                            self.send_alert("自动修复成功，系统已恢复")
                        else:
                            self.send_alert("自动修复失败，需要人工干预")
                    else:
                        # 尝试自动修复
                        self.attempt_auto_fix()
                
                # 等待下次检查
                self.log(f"⏰ 下次检查将在 {self.check_interval} 秒后进行")
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.log(f"❌ 监控循环异常: {e}", "ERROR")
                time.sleep(5)  # 异常时短暂等待
    
    def start(self):
        """启动监控服务"""
        if self.running:
            self.log("⚠️ 监控服务已在运行", "WARN")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.log("✅ 监控服务已启动")
    
    def stop(self):
        """停止监控服务"""
        if not self.running:
            self.log("⚠️ 监控服务未运行", "WARN")
            return
        
        self.running = False
        self.log("🛑 正在停止监控服务...")
        
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=5)
        
        self.log("✅ 监控服务已停止")
    
    def status(self):
        """获取监控状态"""
        status_info = {
            'running': self.running,
            'last_check': self.last_check,
            'last_fix': self.last_fix,
            'consecutive_failures': self.consecutive_failures,
            'check_interval': self.check_interval,
            'auto_fix': self.auto_fix
        }
        
        print(f"\n{'='*50}")
        print("监控服务状态")
        print(f"{'='*50}")
        print(f"运行状态: {'运行中' if status_info['running'] else '已停止'}")
        print(f"检查间隔: {status_info['check_interval']}秒")
        print(f"自动修复: {'启用' if status_info['auto_fix'] else '禁用'}")
        print(f"连续失败: {status_info['consecutive_failures']}次")
        
        if status_info['last_check']:
            print(f"最后检查: {status_info['last_check'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        if status_info['last_fix']:
            print(f"最后修复: {status_info['last_fix'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"{'='*50}")
        
        return status_info

# 全局监控实例
monitor = None

def signal_handler(signum, frame):
    """信号处理器"""
    global monitor
    print("\n收到停止信号...")
    if monitor:
        monitor.stop()
    sys.exit(0)

def main():
    """主函数"""
    global monitor
    
    import argparse
    
    parser = argparse.ArgumentParser(description='分布式数据库自动监控服务')
    parser.add_argument('--interval', type=int, default=30, help='检查间隔（秒）')
    parser.add_argument('--no-auto-fix', action='store_true', help='禁用自动修复')
    parser.add_argument('--status', action='store_true', help='显示状态')
    
    args = parser.parse_args()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建监控实例
    monitor = AutoMonitor(
        check_interval=args.interval,
        auto_fix=not args.no_auto_fix
    )
    
    if args.status:
        monitor.status()
        return
    
    try:
        # 启动监控
        monitor.start()
        
        # 保持主线程运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n收到中断信号...")
    finally:
        if monitor:
            monitor.stop()

if __name__ == "__main__":
    main()
