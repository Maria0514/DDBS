# 分布式数据库系统

基于2PC（二阶段提交）协议的分布式数据库事务管理系统

## 🎯 项目概述

本项目实现了一个完整的分布式数据库系统，包含以下核心功能：

- **2PC二阶段提交协议**：确保分布式事务的ACID特性
- **分布式事务管理**：支持跨多个数据库节点的事务处理
- **Web可视化界面**：实时监控和管理系统状态
- **业务场景演示**：银行转账、库存管理等实际应用场景
- **故障恢复机制**：处理网络故障和节点故障

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐
│   Web界面       │    │   事务协调器     │
│   (Flask)       │    │ (Transaction    │
│                 │    │  Coordinator)   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐       ┌───▼───┐       ┌───▼───┐
│ 数据库1│       │ 数据库2│       │  ...  │
│MySQL  │       │MySQL  │       │       │
│:3306  │       │:3307  │       │       │
└───────┘       └───────┘       └───────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Docker
- MySQL 8.0+

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd distributed-database-system
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境**
   ```bash
   cp .env.example .env
   # 根据需要修改 .env 文件中的配置
   ```

4. **一键启动系统**
   ```bash
   python main.py setup
   ```

### 使用方法

#### 命令行工具

```bash
# 完整系统设置
python main.py setup

# 启动数据库容器
python main.py start-db

# 初始化数据库
python main.py init-db

# 运行测试
python main.py test

# 启动Web界面
python main.py web

# 运行演示程序
python main.py demo

# 查看系统状态
python main.py status

# 执行完整流程
python main.py all
```

#### Web界面

启动Web界面后，访问 http://localhost:5000

- **仪表板**：系统概览和快速操作
- **事务管理**：2PC协议演示和事务测试
- **系统监控**：实时性能监控和日志查看

## 📋 功能特性

### 1. 2PC事务管理

- **准备阶段**：协调器向所有参与者发送准备请求
- **投票阶段**：参与者响应是否可以提交
- **提交阶段**：根据投票结果决定提交或回滚
- **确认阶段**：所有参与者确认操作完成

### 2. 业务场景

#### 银行转账
```python
# 跨数据库的资金转移
banking_service.transfer_money(from_account=1001, to_account=1002, amount=500.0)
```

#### 库存管理
```python
# 订单处理和库存更新
inventory_service.process_order(product_id=101, quantity=2, customer_id=2001)
```

### 3. 故障处理

- **网络故障**：自动重试和超时处理
- **节点故障**：故障检测和恢复机制
- **事务超时**：防止长时间阻塞
- **数据一致性**：确保分布式数据的一致性

### 4. 监控和日志

- **实时监控**：系统性能和数据库状态
- **详细日志**：事务执行过程和错误信息
- **可视化图表**：性能趋势和统计数据

## 🧪 测试

### 运行测试套件

```bash
python main.py test
```

### 测试覆盖

- **单元测试**：事务管理器、数据库管理器
- **集成测试**：完整事务流程
- **性能测试**：并发事务处理
- **故障测试**：异常情况处理

## 📁 项目结构

```
distributed-database-system/
├── main.py                 # 主启动脚本
├── config.py              # 配置管理
├── logger.py              # 日志系统
├── transaction_manager.py  # 事务管理器
├── database_manager.py    # 数据库管理器
├── distributed_app.py     # 分布式应用
├── web_interface.py       # Web界面
├── init_databases.py      # 数据库初始化
├── test_distributed_system.py # 测试套件
├── requirements.txt       # 依赖列表
├── .env.example          # 环境配置示例
├── mysql_setup.sh        # MySQL容器启动脚本
├── templates/            # Web模板
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   ├── transactions.html
│   └── monitoring.html
└── static/              # 静态资源
```

## 🔧 配置说明

### 数据库配置

```python
# 数据库1配置
DB1_HOST=localhost
DB1_PORT=3306
DB1_USER=root
DB1_PASSWORD=password
DB1_DATABASE=db1

# 数据库2配置
DB2_HOST=localhost
DB2_PORT=3307
DB2_USER=root
DB2_PASSWORD=password
DB2_DATABASE=db2
```

### 事务配置

```python
# 事务超时时间（秒）
TRANSACTION_TIMEOUT=60

# 最大重试次数
MAX_RETRY_ATTEMPTS=3

# 2PC准备阶段超时时间（秒）
PREPARE_TIMEOUT=30
```

## 📊 性能指标

- **事务吞吐量**：支持并发事务处理
- **响应时间**：毫秒级事务响应
- **可用性**：99.9%系统可用性
- **一致性**：强一致性保证

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查Docker容器是否运行
   - 验证数据库配置信息
   - 确认网络连接正常

2. **事务超时**
   - 调整事务超时配置
   - 检查数据库性能
   - 优化SQL查询

3. **Web界面无法访问**
   - 检查端口是否被占用
   - 验证防火墙设置
   - 查看应用日志

### 日志查看

```bash
# 查看系统日志
tail -f logs/distributed_db.log

# 查看Docker容器日志
docker logs mysql1
docker logs mysql2
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 邮箱：your-email@example.com
- 项目地址：https://github.com/your-username/distributed-database-system

## 🙏 致谢

感谢所有为本项目做出贡献的开发者和测试人员。

---

**注意**：本项目仅用于学习和研究目的，生产环境使用请进行充分测试和优化。
