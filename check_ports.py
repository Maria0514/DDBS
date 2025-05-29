"""
端口检查脚本
检查MySQL相关端口的占用情况
"""
import socket
import subprocess
import sys

def check_port(host, port):
    """检查端口是否被占用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def get_port_process(port):
    """获取占用端口的进程信息"""
    try:
        result = subprocess.run(['netstat', '-ano'], 
                              capture_output=True, text=True)
        lines = result.stdout.split('\n')
        for line in lines:
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    # 获取进程名
                    try:
                        tasklist_result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                                       capture_output=True, text=True)
                        tasklist_lines = tasklist_result.stdout.split('\n')
                        for tasklist_line in tasklist_lines:
                            if pid in tasklist_line:
                                process_name = tasklist_line.split()[0]
                                return f"PID {pid} ({process_name})"
                    except:
                        return f"PID {pid}"
        return "Unknown"
    except:
        return "Unknown"

def main():
    """主函数"""
    print("🔍 检查MySQL相关端口占用情况")
    print("=" * 50)
    
    ports_to_check = [3306, 3307, 3316, 3317]
    
    for port in ports_to_check:
        is_occupied = check_port('localhost', port)
        if is_occupied:
            process_info = get_port_process(port)
            print(f"❌ 端口 {port}: 被占用 - {process_info}")
        else:
            print(f"✅ 端口 {port}: 可用")
    
    print("\n📋 建议:")
    
    # 检查3306端口
    if check_port('localhost', 3306):
        print("• 端口3306被占用（通常是本地MySQL）")
        print("  - 选项1: 停止本地MySQL服务")
        print("  - 选项2: 使用不同端口（3316, 3317）")
        print("  - 选项3: 使用本地MySQL而不是Docker")
    
    # 检查Docker容器端口
    if check_port('localhost', 3316) or check_port('localhost', 3317):
        print("• Docker端口被占用")
        print("  - 可能有Docker容器正在运行")
        print("  - 运行: docker ps 查看运行的容器")
    
    print("\n🚀 推荐的解决方案:")
    if check_port('localhost', 3306):
        print("1. 使用修改后的端口配置（3316, 3317）")
        print("   运行: python main.py start-db")
        print("2. 或者使用本地MySQL设置")
        print("   运行: python setup_local_mysql.py")
    else:
        print("1. 所有端口可用，可以正常使用Docker")
        print("   运行: python main.py start-db")

if __name__ == "__main__":
    main()
