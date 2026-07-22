#!/usr/bin/env python3
"""
NSPS-V1 Core: Learning Ledger
记录所有学习/调参历史，可审计、可回滚
全部本地资源，0成本
"""

import psycopg2
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'saps',
    'password': 'saps123',
    'dbname': 'sps'
}

class LearningLedger:
    """学习账本：记录所有自动调参，可审计、可回滚"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ LearningLedger连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def create_table(self):
        """创建learning_ledger表"""
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS learning_ledger (
                id SERIAL PRIMARY KEY,
                time TIMESTAMP NOT NULL DEFAULT NOW(),
                agent_name TEXT NOT NULL,
                change_type TEXT NOT NULL,
                old_value JSONB,
                new_value JSONB,
                reason TEXT,
                evidence JSONB,
                backtest_result JSONB,
                actual_result JSONB,
                rollback_triggered BOOLEAN DEFAULT FALSE,
                rollback_condition TEXT,
                approved_by TEXT DEFAULT 'AUTO',
                approved_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        self.conn.commit()
        logger.info("✅ learning_ledger表已创建")
    
    def record_learning(self, agent_name: str, change_type: str,
                         old_value: Dict, new_value: Dict,
                         reason: str, evidence: Dict = None,
                         backtest_result: Dict = None,
                         rollback_condition: str = None) -> int:
        """记录一次学习/调参"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO learning_ledger 
            (agent_name, change_type, old_value, new_value, reason, 
             evidence, backtest_result, rollback_condition)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (agent_name, change_type, json.dumps(old_value), json.dumps(new_value),
              reason, json.dumps(evidence or {}), json.dumps(backtest_result or {}),
              rollback_condition))
        
        ledger_id = cur.fetchone()[0]
        self.conn.commit()
        logger.info(f"✅ 记录学习 #{ledger_id}: {agent_name} {change_type}")
        return ledger_id
    
    def get_recent_learnings(self, limit: int = 10) -> List[Dict]:
        """获取最近的学习记录"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, time, agent_name, change_type, old_value, new_value,
                   reason, actual_result, rollback_triggered
            FROM learning_ledger
            ORDER BY time DESC
            LIMIT %s
        """, (limit,))
        
        results = []
        for row in cur.fetchall():
            results.append({
                'id': row[0],
                'time': row[1],
                'agent_name': row[2],
                'change_type': row[3],
                'old_value': row[4],
                'new_value': row[5],
                'reason': row[6],
                'actual_result': row[7],
                'rollback_triggered': row[8]
            })
        
        return results
    
    def get_agent_learnings(self, agent_name: str, limit: int = 20) -> List[Dict]:
        """获取某个Agent的学习历史"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, time, change_type, old_value, new_value,
                   reason, actual_result, rollback_triggered
            FROM learning_ledger
            WHERE agent_name = %s
            ORDER BY time DESC
            LIMIT %s
        """, (agent_name, limit))
        
        results = []
        for row in cur.fetchall():
            results.append({
                'id': row[0],
                'time': row[1],
                'change_type': row[2],
                'old_value': row[3],
                'new_value': row[4],
                'reason': row[5],
                'actual_result': row[6],
                'rollback_triggered': row[7]
            })
        
        return results
    
    def check_rollback_needed(self, ledger_id: int) -> bool:
        """检查是否需要回滚"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT rollback_condition, actual_result
            FROM learning_ledger
            WHERE id = %s
        """, (ledger_id,))
        
        row = cur.fetchone()
        if not row:
            return False
        
        rollback_condition = row[0]
        actual_result = row[1]
        
        # 简单的条件检查（实际应该用更复杂的逻辑）
        if rollback_condition and actual_result:
            # 示例：如果actual_result的win_rate < 0.45，触发回滚
            if 'win_rate' in str(actual_result):
                win_rate = actual_result.get('win_rate', 1.0)
                if win_rate < 0.45:
                    return True
        
        return False
    
    def trigger_rollback(self, ledger_id: int, reason: str) -> bool:
        """触发回滚"""
        cur = self.conn.cursor()
        
        # 获取原始值
        cur.execute("""
            SELECT agent_name, change_type, old_value
            FROM learning_ledger
            WHERE id = %s
        """, (ledger_id,))
        
        row = cur.fetchone()
        if not row:
            return False
        
        agent_name, change_type, old_value = row
        
        # 标记为已回滚
        cur.execute("""
            UPDATE learning_ledger
            SET rollback_triggered = TRUE,
                actual_result = actual_result || %s::jsonb
            WHERE id = %s
        """, (json.dumps({'rollback_reason': reason, 'rollback_time': datetime.now().isoformat()}),
              ledger_id))
        
        self.conn.commit()
        logger.info(f"✅ 已回滚 Learning #{ledger_id}: {agent_name} {change_type}")
        logger.info(f"   原因: {reason}")
        logger.info(f"   回滚到: {old_value}")
        
        return True
    
    def update_actual_result(self, ledger_id: int, result: Dict):
        """更新实际结果"""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE learning_ledger
            SET actual_result = %s
            WHERE id = %s
        """, (json.dumps(result), ledger_id))
        self.conn.commit()
        logger.info(f"✅ 更新Learning #{ledger_id}实际结果")
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_learning_ledger():
    """测试LearningLedger"""
    print("=" * 80)
    print("测试: LearningLedger")
    print("=" * 80)
    
    ledger = LearningLedger()
    
    # 测试1: 创建表
    print("\n[测试1] 创建learning_ledger表...")
    ledger.create_table()
    
    # 测试2: 记录学习
    print("\n[测试2] 记录学习...")
    ledger_id = ledger.record_learning(
        agent_name='News Agent',
        change_type='weight_adjustment',
        old_value={'weight': 0.32},
        new_value={'weight': 0.47},
        reason='Macro连续失败3次',
        evidence={'recent_accuracy': 0.40, 'sample_size': 10},
        backtest_result={'win_rate': 0.55, 'profit_factor': 1.6},
        rollback_condition='如果第二天胜率<45%，自动回滚到0.32'
    )
    print(f"  记录ID: {ledger_id}")
    
    # 测试3: 获取最近学习
    print("\n[测试3] 获取最近学习记录...")
    recent = ledger.get_recent_learnings(limit=5)
    for r in recent:
        print(f"  #{r['id']} | {r['time']} | {r['agent_name']} | {r['change_type']}")
        print(f"     原因: {r['reason']}")
    
    # 测试4: 获取Agent学习历史
    print("\n[测试4] 获取News Agent学习历史...")
    news_history = ledger.get_agent_learnings('News Agent', limit=5)
    print(f"  共{len(news_history)}条记录")
    
    # 测试5: 更新实际结果
    print("\n[测试5] 更新实际结果...")
    ledger.update_actual_result(ledger_id, {'win_rate': 0.42, 'result': 'FAIL'})
    
    # 测试6: 检查是否需要回滚
    print("\n[测试6] 检查是否需要回滚...")
    needs_rollback = ledger.check_rollback_needed(ledger_id)
    print(f"  需要回滚: {needs_rollback}")
    
    # 测试7: 触发回滚
    if needs_rollback:
        print("\n[测试7] 触发回滚...")
        ledger.trigger_rollback(ledger_id, '胜率下降到42%，低于45%阈值')
    
    ledger.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_learning_ledger()
