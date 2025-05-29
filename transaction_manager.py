"""
增强的2PC事务管理器
实现完整的二阶段提交协议，包括错误处理、超时机制、日志记录等
"""
import mysql.connector
from mysql.connector import Error
import uuid
import time
import threading
from typing import List, Dict, Optional, Callable, Any
from enum import Enum
from config import TransactionConfig
from logger import (transaction_logger, log_transaction_start,
                   log_transaction_prepare, log_transaction_commit, log_system_error)

class TransactionState(Enum):
    """事务状态枚举"""
    INIT = "INIT"
    ACTIVE = "ACTIVE"
    PREPARING = "PREPARING"
    PREPARED = "PREPARED"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    ABORTING = "ABORTING"
    ABORTED = "ABORTED"

class ParticipantState(Enum):
    """参与者状态枚举"""
    ACTIVE = "ACTIVE"
    PREPARED = "PREPARED"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"
    FAILED = "FAILED"

class TransactionParticipant:
    """事务参与者类"""

    def __init__(self, participant_id: str, connection: mysql.connector.MySQLConnection):
        self.participant_id = participant_id
        self.connection = connection
        self.state = ParticipantState.ACTIVE
        self.xa_id = None
        self.last_operation_time = time.time()

    def set_xa_id(self, xa_id: str):
        """设置XA事务ID"""
        self.xa_id = xa_id

    def update_last_operation(self):
        """更新最后操作时间"""
        self.last_operation_time = time.time()

class EnhancedTransactionManager:
    """增强的分布式事务管理器"""

    def __init__(self, connections: List[mysql.connector.MySQLConnection]):
        self.transaction_id = str(uuid.uuid4())
        self.participants: Dict[str, TransactionParticipant] = {}
        self.state = TransactionState.INIT
        self.start_time = time.time()
        self.timeout = TransactionConfig.TRANSACTION_TIMEOUT
        self.prepare_timeout = TransactionConfig.PREPARE_TIMEOUT
        self._lock = threading.Lock()
        self.operations: List[Dict] = []  # 记录所有操作

        # 初始化参与者
        for i, conn in enumerate(connections):
            participant_id = f"participant_{i+1}"
            self.participants[participant_id] = TransactionParticipant(participant_id, conn)

        log_transaction_start(self.transaction_id, list(self.participants.keys()))

    def _check_timeout(self) -> bool:
        """检查事务是否超时"""
        return time.time() - self.start_time > self.timeout

    def _generate_xa_id(self, participant_id: str) -> str:
        """生成XA事务ID"""
        return f"{self.transaction_id}_{participant_id}"

    def begin_transaction(self) -> bool:
        """开始分布式事务"""
        with self._lock:
            if self.state != TransactionState.INIT:
                raise Exception(f"Transaction {self.transaction_id} is not in INIT state")

            if self._check_timeout():
                raise Exception(f"Transaction {self.transaction_id} timed out before starting")

            try:
                for participant_id, participant in self.participants.items():
                    xa_id = self._generate_xa_id(participant_id)
                    participant.set_xa_id(xa_id)

                    cursor = participant.connection.cursor()
                    cursor.execute(f"XA START '{xa_id}'")
                    cursor.close()

                    participant.update_last_operation()
                    transaction_logger.debug(f"Started XA transaction {xa_id} for {participant_id}")

                self.state = TransactionState.ACTIVE
                transaction_logger.info(f"Transaction {self.transaction_id} started successfully")
                return True

            except Exception as e:
                self.state = TransactionState.ABORTED
                log_system_error("TransactionManager.begin_transaction", str(e))
                raise Exception(f"Failed to start transaction {self.transaction_id}: {e}")

    def execute_operation(self, participant_id: str, operation: Callable, *args, **kwargs) -> Any:
        """在指定参与者上执行操作"""
        with self._lock:
            if self.state != TransactionState.ACTIVE:
                raise Exception(f"Transaction {self.transaction_id} is not active")

            if self._check_timeout():
                raise Exception(f"Transaction {self.transaction_id} timed out")

            if participant_id not in self.participants:
                raise ValueError(f"Unknown participant: {participant_id}")

            participant = self.participants[participant_id]

            try:
                # 记录操作
                operation_record = {
                    'participant_id': participant_id,
                    'operation': operation.__name__ if hasattr(operation, '__name__') else str(operation),
                    'args': args,
                    'kwargs': kwargs,
                    'timestamp': time.time()
                }
                self.operations.append(operation_record)

                # 执行操作
                result = operation(participant.connection, *args, **kwargs)
                participant.update_last_operation()

                transaction_logger.debug(f"Executed operation on {participant_id}: {operation_record['operation']}")
                return result

            except Exception as e:
                participant.state = ParticipantState.FAILED
                log_system_error(f"TransactionManager.execute_operation.{participant_id}", str(e))
                raise Exception(f"Operation failed on {participant_id}: {e}")

    def prepare(self) -> bool:
        """第一阶段：准备提交"""
        with self._lock:
            if self.state != TransactionState.ACTIVE:
                raise Exception(f"Transaction {self.transaction_id} is not active")

            if self._check_timeout():
                raise Exception(f"Transaction {self.transaction_id} timed out")

            self.state = TransactionState.PREPARING
            prepare_start_time = time.time()

            try:
                # 对所有参与者执行准备操作
                for participant_id, participant in self.participants.items():
                    if time.time() - prepare_start_time > self.prepare_timeout:
                        raise Exception(f"Prepare phase timed out for transaction {self.transaction_id}")

                    try:
                        cursor = participant.connection.cursor()
                        cursor.execute(f"XA END '{participant.xa_id}'")
                        cursor.execute(f"XA PREPARE '{participant.xa_id}'")
                        cursor.close()

                        participant.state = ParticipantState.PREPARED
                        participant.update_last_operation()
                        log_transaction_prepare(self.transaction_id, participant_id, True)

                    except Exception as e:
                        participant.state = ParticipantState.FAILED
                        log_transaction_prepare(self.transaction_id, participant_id, False)
                        raise Exception(f"Prepare failed for {participant_id}: {e}")

                self.state = TransactionState.PREPARED
                transaction_logger.info(f"Transaction {self.transaction_id} prepared successfully")
                return True

            except Exception as e:
                self.state = TransactionState.ABORTING
                log_system_error("TransactionManager.prepare", str(e))
                # 自动回滚
                self._rollback_internal()
                raise Exception(f"Prepare phase failed for transaction {self.transaction_id}: {e}")

    def commit(self) -> bool:
        """第二阶段：提交事务"""
        with self._lock:
            if self.state != TransactionState.PREPARED:
                raise Exception(f"Transaction {self.transaction_id} is not prepared")

            self.state = TransactionState.COMMITTING

            try:
                # 对所有参与者执行提交操作
                for participant_id, participant in self.participants.items():
                    try:
                        cursor = participant.connection.cursor()
                        cursor.execute(f"XA COMMIT '{participant.xa_id}'")
                        cursor.close()

                        participant.state = ParticipantState.COMMITTED
                        participant.update_last_operation()

                    except Exception as e:
                        # 提交阶段的错误比较严重，但不应该阻止其他参与者提交
                        participant.state = ParticipantState.FAILED
                        transaction_logger.error(f"Commit failed for {participant_id}: {e}")

                self.state = TransactionState.COMMITTED
                log_transaction_commit(self.transaction_id, True)
                transaction_logger.info(f"Transaction {self.transaction_id} committed successfully")
                return True

            except Exception as e:
                log_system_error("TransactionManager.commit", str(e))
                log_transaction_commit(self.transaction_id, False)
                raise Exception(f"Commit phase failed for transaction {self.transaction_id}: {e}")

    def rollback(self) -> bool:
        """回滚事务"""
        with self._lock:
            return self._rollback_internal()

    def _rollback_internal(self) -> bool:
        """内部回滚实现"""
        if self.state in [TransactionState.COMMITTED, TransactionState.ABORTED]:
            return True

        self.state = TransactionState.ABORTING

        try:
            # 对所有参与者执行回滚操作
            for participant_id, participant in self.participants.items():
                try:
                    cursor = participant.connection.cursor()

                    # 根据参与者状态选择合适的回滚命令
                    if participant.state == ParticipantState.PREPARED:
                        cursor.execute(f"XA ROLLBACK '{participant.xa_id}'")
                    elif participant.state == ParticipantState.ACTIVE:
                        cursor.execute(f"XA END '{participant.xa_id}'")
                        cursor.execute(f"XA ROLLBACK '{participant.xa_id}'")

                    cursor.close()
                    participant.state = ParticipantState.ABORTED
                    participant.update_last_operation()

                except Exception as e:
                    transaction_logger.error(f"Rollback failed for {participant_id}: {e}")

            self.state = TransactionState.ABORTED
            log_transaction_commit(self.transaction_id, False)
            transaction_logger.info(f"Transaction {self.transaction_id} rolled back successfully")
            return True

        except Exception as e:
            log_system_error("TransactionManager.rollback", str(e))
            raise Exception(f"Rollback failed for transaction {self.transaction_id}: {e}")

    def get_transaction_info(self) -> Dict:
        """获取事务信息"""
        with self._lock:
            participant_info = {}
            for pid, participant in self.participants.items():
                participant_info[pid] = {
                    'state': participant.state.value,
                    'xa_id': participant.xa_id,
                    'last_operation_time': participant.last_operation_time
                }

            return {
                'transaction_id': self.transaction_id,
                'state': self.state.value,
                'start_time': self.start_time,
                'timeout': self.timeout,
                'participants': participant_info,
                'operations_count': len(self.operations),
                'elapsed_time': time.time() - self.start_time
            }

    def cleanup(self):
        """清理资源"""
        try:
            if self.state not in [TransactionState.COMMITTED, TransactionState.ABORTED]:
                self.rollback()
        except:
            pass

        # 关闭所有连接
        for participant in self.participants.values():
            try:
                participant.connection.close()
            except:
                pass

# 保持向后兼容性的别名
TransactionManager = EnhancedTransactionManager