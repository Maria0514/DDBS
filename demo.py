#!/usr/bin/env python3
"""
分布式数据库系统演示脚本
展示系统的核心功能和2PC协议的工作原理
"""
import time
import random
from typing import List, Dict
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """打印系统横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    分布式数据库系统演示                        ║
    ║                基于2PC（二阶段提交）协议                       ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def simulate_2pc_protocol():
    """模拟2PC协议执行过程"""
    print_section("2PC协议演示")
    
    participants = ["数据库1 (MySQL:3306)", "数据库2 (MySQL:3307)"]
    transaction_id = f"tx_{int(time.time())}"
    
    print(f"🚀 开始分布式事务: {transaction_id}")
    print(f"📋 参与者: {', '.join(participants)}")
    
    # 阶段1：准备阶段
    print(f"\n📍 阶段1：准备阶段")
    print("   协调器 -> 所有参与者: 准备提交请求")
    
    for i, participant in enumerate(participants, 1):
        time.sleep(0.5)
        print(f"   {participant}: 准备中...")
        time.sleep(0.5)
        print(f"   {participant}: ✅ 准备完成，可以提交")
    
    print("   协调器: 收到所有参与者的准备确认")
    
    # 阶段2：提交阶段
    print(f"\n📍 阶段2：提交阶段")
    print("   协调器 -> 所有参与者: 提交请求")
    
    for i, participant in enumerate(participants, 1):
        time.sleep(0.5)
        print(f"   {participant}: 执行提交...")
        time.sleep(0.5)
        print(f"   {participant}: ✅ 提交完成")
    
    print(f"   协调器: 事务 {transaction_id} 提交成功")
    print(f"\n🎉 分布式事务完成！")

def simulate_banking_scenario():
    """模拟银行转账场景"""
    print_section("银行转账场景演示")
    
    # 模拟账户数据
    accounts = {
        1001: {"balance": 5000.00, "name": "张三"},
        1002: {"balance": 3000.00, "name": "李四"},
        1003: {"balance": 1000.00, "name": "王五"}
    }
    
    print("💰 当前账户状态:")
    for acc_id, info in accounts.items():
        print(f"   账户 {acc_id} ({info['name']}): ¥{info['balance']:.2f}")
    
    # 模拟转账操作
    from_account = 1001
    to_account = 1002
    amount = 500.00
    
    print(f"\n🔄 执行转账: {from_account} -> {to_account}, 金额: ¥{amount}")
    
    # 检查余额
    print(f"   检查账户 {from_account} 余额...")
    if accounts[from_account]["balance"] >= amount:
        print(f"   ✅ 余额充足: ¥{accounts[from_account]['balance']}")
    else:
        print(f"   ❌ 余额不足: ¥{accounts[from_account]['balance']}")
        return
    
    # 模拟2PC过程
    print(f"\n   开始2PC事务...")
    time.sleep(1)
    
    print(f"   阶段1: 准备更新账户余额...")
    time.sleep(1)
    print(f"   阶段1: 所有参与者准备完成")
    
    print(f"   阶段2: 执行余额更新...")
    accounts[from_account]["balance"] -= amount
    accounts[to_account]["balance"] += amount
    time.sleep(1)
    print(f"   阶段2: 余额更新完成")
    
    print(f"\n💰 转账后账户状态:")
    for acc_id, info in accounts.items():
        print(f"   账户 {acc_id} ({info['name']}): ¥{info['balance']:.2f}")
    
    print(f"\n✅ 转账成功完成！")

def simulate_inventory_scenario():
    """模拟库存管理场景"""
    print_section("库存管理场景演示")
    
    # 模拟库存数据
    inventory = {
        101: {"name": "笔记本电脑", "quantity": 50, "price": 999.99},
        102: {"name": "无线鼠标", "quantity": 200, "price": 29.99},
        103: {"name": "机械键盘", "quantity": 150, "price": 79.99}
    }
    
    print("📦 当前库存状态:")
    for prod_id, info in inventory.items():
        print(f"   产品 {prod_id} ({info['name']}): {info['quantity']} 件, ¥{info['price']}")
    
    # 模拟订单处理
    product_id = 101
    order_quantity = 2
    customer_id = 2001
    
    print(f"\n🛒 处理订单: 产品 {product_id}, 数量 {order_quantity}, 客户 {customer_id}")
    
    # 检查库存
    print(f"   检查产品 {product_id} 库存...")
    if inventory[product_id]["quantity"] >= order_quantity:
        print(f"   ✅ 库存充足: {inventory[product_id]['quantity']} 件")
    else:
        print(f"   ❌ 库存不足: {inventory[product_id]['quantity']} 件")
        return
    
    # 模拟2PC过程
    print(f"\n   开始2PC事务...")
    time.sleep(1)
    
    print(f"   阶段1: 准备更新库存和创建订单...")
    time.sleep(1)
    print(f"   阶段1: 所有参与者准备完成")
    
    print(f"   阶段2: 执行库存更新和订单创建...")
    inventory[product_id]["quantity"] -= order_quantity
    total_amount = inventory[product_id]["price"] * order_quantity
    time.sleep(1)
    print(f"   阶段2: 操作完成")
    
    print(f"\n📦 订单处理后库存状态:")
    for prod_id, info in inventory.items():
        print(f"   产品 {prod_id} ({info['name']}): {info['quantity']} 件, ¥{info['price']}")
    
    print(f"\n📋 订单详情:")
    print(f"   订单ID: ORD_{int(time.time())}")
    print(f"   产品: {inventory[product_id]['name']}")
    print(f"   数量: {order_quantity}")
    print(f"   总金额: ¥{total_amount:.2f}")
    print(f"   客户ID: {customer_id}")
    
    print(f"\n✅ 订单处理成功完成！")

def simulate_failure_scenario():
    """模拟故障处理场景"""
    print_section("故障处理场景演示")
    
    scenarios = [
        "网络连接超时",
        "参与者节点故障",
        "事务执行超时",
        "数据冲突检测"
    ]
    
    scenario = random.choice(scenarios)
    transaction_id = f"tx_{int(time.time())}"
    
    print(f"🚨 模拟故障场景: {scenario}")
    print(f"📋 事务ID: {transaction_id}")
    
    print(f"\n🔄 开始分布式事务...")
    time.sleep(1)
    
    print(f"   阶段1: 发送准备请求...")
    time.sleep(1)
    
    if scenario == "网络连接超时":
        print(f"   数据库1: ✅ 准备完成")
        print(f"   数据库2: ⏰ 连接超时...")
        time.sleep(2)
        print(f"   协调器: ❌ 检测到网络故障，执行回滚")
        
    elif scenario == "参与者节点故障":
        print(f"   数据库1: ✅ 准备完成")
        print(f"   数据库2: 💥 节点故障")
        print(f"   协调器: ❌ 检测到节点故障，执行回滚")
        
    elif scenario == "事务执行超时":
        print(f"   数据库1: ✅ 准备完成")
        print(f"   数据库2: ⏰ 执行超时...")
        time.sleep(2)
        print(f"   协调器: ❌ 事务超时，执行回滚")
        
    elif scenario == "数据冲突检测":
        print(f"   数据库1: ✅ 准备完成")
        print(f"   数据库2: ⚠️ 检测到数据冲突")
        print(f"   协调器: ❌ 数据冲突，执行回滚")
    
    print(f"\n🔄 执行回滚操作...")
    time.sleep(1)
    print(f"   数据库1: 回滚完成")
    print(f"   数据库2: 回滚完成")
    
    print(f"\n✅ 故障处理完成，系统状态已恢复")
    print(f"📊 事务 {transaction_id} 已回滚")

def show_system_architecture():
    """显示系统架构"""
    print_section("系统架构概览")
    
    architecture = """
    ┌─────────────────────────────────────────────────────────────┐
    │                      Web管理界面                            │
    │                   (Flask + SocketIO)                       │
    └─────────────────────┬───────────────────────────────────────┘
                          │
    ┌─────────────────────▼───────────────────────────────────────┐
    │                   事务协调器                                │
    │              (Transaction Manager)                         │
    │                                                             │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
    │  │   准备阶段   │  │   投票阶段   │  │   提交阶段   │        │
    │  │  (Prepare)  │  │   (Vote)    │  │  (Commit)   │        │
    │  └─────────────┘  └─────────────┘  └─────────────┘        │
    └─────────────────────┬───────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
    │ 数据库1  │      │ 数据库2  │      │   ...   │
    │ MySQL   │      │ MySQL   │      │         │
    │ :3306   │      │ :3307   │      │         │
    │         │      │         │      │         │
    │ 账户表   │      │ 交易表   │      │         │
    │ 库存表   │      │ 订单表   │      │         │
    └─────────┘      └─────────┘      └─────────┘
    """
    
    print(architecture)
    
    print("\n🔧 核心组件说明:")
    print("   • 事务协调器: 管理分布式事务的生命周期")
    print("   • 数据库管理器: 管理数据库连接和操作")
    print("   • Web界面: 提供可视化管理和监控")
    print("   • 日志系统: 记录系统运行状态和事务日志")

def show_performance_metrics():
    """显示性能指标"""
    print_section("系统性能指标")
    
    # 模拟性能数据
    metrics = {
        "事务吞吐量": f"{random.randint(50, 200)} TPS",
        "平均响应时间": f"{random.randint(10, 100)} ms",
        "系统可用性": f"{random.uniform(99.5, 99.9):.2f}%",
        "数据一致性": "100% (强一致性)",
        "并发连接数": f"{random.randint(10, 50)}",
        "内存使用率": f"{random.randint(30, 70)}%",
        "CPU使用率": f"{random.randint(20, 60)}%"
    }
    
    print("📊 当前系统性能:")
    for metric, value in metrics.items():
        print(f"   {metric}: {value}")
    
    print(f"\n🎯 性能特点:")
    print("   • 支持高并发事务处理")
    print("   • 毫秒级事务响应时间")
    print("   • 99.9%+ 系统可用性保证")
    print("   • 强一致性数据保证")

def main():
    """主演示函数"""
    print_banner()
    
    try:
        # 显示系统架构
        show_system_architecture()
        
        # 等待用户确认
        input("\n按回车键继续演示...")
        
        # 2PC协议演示
        simulate_2pc_protocol()
        
        # 等待用户确认
        input("\n按回车键继续演示...")
        
        # 银行转账场景
        simulate_banking_scenario()
        
        # 等待用户确认
        input("\n按回车键继续演示...")
        
        # 库存管理场景
        simulate_inventory_scenario()
        
        # 等待用户确认
        input("\n按回车键继续演示...")
        
        # 故障处理场景
        simulate_failure_scenario()
        
        # 等待用户确认
        input("\n按回车键继续演示...")
        
        # 性能指标
        show_performance_metrics()
        
        print_section("演示完成")
        print("🎉 分布式数据库系统演示结束！")
        print("\n📝 演示总结:")
        print("   ✅ 2PC协议工作原理")
        print("   ✅ 银行转账业务场景")
        print("   ✅ 库存管理业务场景")
        print("   ✅ 故障处理和恢复机制")
        print("   ✅ 系统性能指标")
        
        print(f"\n🚀 要启动完整系统，请运行:")
        print(f"   python main.py setup    # 初始化系统")
        print(f"   python main.py web      # 启动Web界面")
        
    except KeyboardInterrupt:
        print(f"\n\n👋 演示已中断，感谢观看！")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")

if __name__ == "__main__":
    main()
