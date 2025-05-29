# 分布式数据库系统故障排除指南

## 🚨 常见错误及解决方案

### 1. "Database node db1 is not available" 错误

#### 🔍 **问题描述**
```
Database operation FAILED - SELECT on db1.query: Database node db1 is not available
```

#### 🎯 **可能原因**
1. Docker容器停止或重启
2. 网络连接问题
3. MySQL服务未完全启动
4. 系统资源不足

#### 🛠️ **解决步骤**

##### 步骤1: 检查Docker容器状态
```bash
# 查看容器状态
docker ps -a

# 检查容器日志
docker logs mysql1
docker logs mysql2
```

##### 步骤2: 使用健康检查脚本
```bash
# 执行完整健康检查
python docker_health_check.py check

# 连续监控模式
python docker_health_check.py monitor 30
```

##### 步骤3: 手动重启容器（如果需要）
```bash
# 重启特定容器
docker restart mysql1
docker restart mysql2

# 或重启所有容器
docker-compose restart
```

##### 步骤4: 验证数据库连接
```bash
# 使用数据库监控脚本
python monitor_database.py check

# 测试连接
python -c "
import mysql.connector
conn = mysql.connector.connect(host='localhost', port=3316, user='root', password='password')
print('连接成功')
conn.close()
"
```

### 2. SSL wrap_socket 错误

#### 🔍 **问题描述**
```
module 'ssl' has no attribute 'wrap_socket'
```

#### 🛠️ **解决方案**
已在配置中修复，使用threading模式替代eventlet：
```python
# .env文件中
SOCKETIO_ASYNC_MODE=threading
```

### 3. 事务准备失败

#### 🔍 **问题描述**
```
System error in TransactionManager.prepare: Prepare failed for participant_1: Prepare failed
```

#### 🎯 **说明**
这通常是**正常的测试场景**，不是真实错误。系统故意模拟失败来测试2PC协议的错误处理。

### 4. 端口冲突

#### 🔍 **问题描述**
```
Can't connect to MySQL server on 'localhost:3306'
```

#### 🛠️ **解决方案**
确保使用正确的端口：
- db1: localhost:3316
- db2: localhost:3317

## 📊 监控工具使用

### 数据库状态监控
```bash
# 单次检查
python monitor_database.py check

# 连续监控（30秒间隔）
python monitor_database.py monitor 30

# 显示Docker状态
python monitor_database.py docker
```

### Docker容器监控
```bash
# 健康检查
python docker_health_check.py check

# 连续监控（60秒间隔）
python docker_health_check.py monitor 60

# 显示容器信息
python docker_health_check.py info
```

## 🔧 预防措施

### 1. 定期健康检查
设置定时任务每5分钟检查一次：
```bash
# 添加到crontab
*/5 * * * * cd /path/to/project && python docker_health_check.py check >> health_check.log 2>&1
```

### 2. 资源监控
确保系统有足够资源：
```bash
# 检查内存使用
docker stats

# 检查磁盘空间
df -h
```

### 3. 日志轮转
配置日志轮转防止日志文件过大：
```python
# 在logger.py中已配置
MAX_LOG_SIZE = 10  # MB
BACKUP_COUNT = 5
```

## 🚀 性能优化

### 1. 连接池配置
```python
# 在config.py中调整
CONNECTION_POOL_SIZE = 5
CONNECTION_TIMEOUT = 30
```

### 2. 事务超时设置
```python
TRANSACTION_TIMEOUT = 60
MAX_RETRY_ATTEMPTS = 3
RETRY_INTERVAL = 1
```

## 📞 紧急恢复

### 完全重置系统
```bash
# 1. 停止所有容器
docker-compose down

# 2. 清理数据（谨慎使用）
docker volume prune

# 3. 重新启动
docker-compose up -d

# 4. 重新初始化数据库
python main.py init-db

# 5. 验证系统
python main.py test
```

### 数据备份恢复
```bash
# 备份数据
docker exec mysql1 mysqldump -u root -ppassword db1 > backup_db1.sql
docker exec mysql2 mysqldump -u root -ppassword db2 > backup_db2.sql

# 恢复数据
docker exec -i mysql1 mysql -u root -ppassword db1 < backup_db1.sql
docker exec -i mysql2 mysql -u root -ppassword db2 < backup_db2.sql
```

## 📋 检查清单

### 系统启动检查
- [ ] Docker服务运行正常
- [ ] 容器mysql1和mysql2运行中
- [ ] 端口3316和3317可访问
- [ ] .env配置文件存在且正确
- [ ] 数据库表已创建
- [ ] 测试数据已插入

### 故障排除检查
- [ ] 检查Docker容器状态
- [ ] 验证网络连接
- [ ] 查看应用日志
- [ ] 测试数据库连接
- [ ] 验证事务功能
- [ ] 检查系统资源

## 📞 获取帮助

如果问题仍然存在，请：
1. 运行完整诊断：`python monitor_database.py check`
2. 收集日志：`tail -50 logs/distributed_db.log`
3. 检查Docker状态：`docker ps -a`
4. 提供错误信息的完整上下文
