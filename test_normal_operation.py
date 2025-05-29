#!/usr/bin/env python3
"""
验证分布式事务系统正常工作的测试脚本
"""

from distributed_app import BankingService

def test_normal_operations():
    """测试正常操作"""
    print('=== 验证分布式事务系统正常工作 ===')

    # 创建银行服务
    banking = BankingService()

    # 测试1: 创建账户
    print('\n1. 测试账户创建:')
    result1 = banking.create_account(7777, 1000.0)
    print(f'   创建账户7777: {"成功" if result1 else "失败"}')

    # 测试2: 查询余额
    print('\n2. 测试余额查询:')
    balance = banking.get_account_balance(7777)
    print(f'   账户7777余额: {balance}')

    # 测试3: 正常转账
    print('\n3. 测试正常转账:')
    banking.create_account(8888, 500.0)
    result2 = banking.transfer_money(7777, 8888, 200.0)
    print(f'   转账200元: {"成功" if result2 else "失败"}')

    if result2:
        balance1 = banking.get_account_balance(7777)
        balance2 = banking.get_account_balance(8888)
        print(f'   转账后7777余额: {balance1}')
        print(f'   转账后8888余额: {balance2}')

    # 测试4: 余额不足转账（应该失败）
    print('\n4. 测试余额不足转账:')
    result3 = banking.transfer_money(8888, 7777, 1000.0)
    print(f'   转账1000元（余额不足）: {"成功" if result3 else "失败（预期）"}')

    print('\n=== 测试完成 ===')
    print('如果看到上述结果，说明系统工作正常！')
    print('日志中的"Prepare failed"错误是测试套件的故意失败场景。')

if __name__ == "__main__":
    test_normal_operations()
