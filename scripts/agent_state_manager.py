#!/usr/bin/env python3
"""
NSPS-V1 Core: Agent State Manager
管理所有Agent的状态：Accuracy, Confidence, Strength, Weakness, Version
全部本地资源，0成本
"""

import psycopg2
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TimescaleDB连接
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'saps',
    'password': 'saps123',
    'dbname': 'sps'
}

class AgentStateManager:
    """管理所有Agent的状态"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ AgentStateManager连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def create_table(self):
        """创建agent_states表"""
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_states (
                id SERIAL PRIMARY KEY,
                agent_name TEXT NOT NULL UNIQUE,
                version TEXT DEFAULT '1.0.0',
                accuracy REAL DEFAULT 0.5,
                confidence REAL DEFAULT 0.5,
                last_100_accuracy REAL DEFAULT 0.5,
                strength_tags JSONB DEFAULT '[]',
                weakness_tags JSONB DEFAULT '[]',
                learning_rate REAL DEFAULT 0.01,
                total_predictions INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT NOW()
            )
        """)
        self.conn.commit()
        logger.info("✅ agent_states表已创建")
    
    def init_agents(self):
        """初始化所有Agent"""
        agents = [
            ('Bull Team', '1.0.0'),
            ('Bear Team', '1.0.0'),
            ('Risk Team', '1.0.0'),
            ('Historian', '1.0.0'),
            ('Critic Agent', '1.0.0'),
            ('Auditor Agent', '1.0.0'),
            ('Coach Agent', '1.0.0'),
            ('Meta Brain', '1.0.0')
        ]
        
        for agent_name, version in agents:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO agent_states (agent_name, version)
                VALUES (%s, %s)
                ON CONFLICT (agent_name) DO NOTHING
            """, (agent_name, version))
            self.conn.commit()
        
        logger.info(f"✅ 已初始化 {len(agents)} 个Agent")
    
    def update_prediction_result(self, agent_name: str, correct: bool):
        """更新Agent的预测结果"""
        cur = self.conn.cursor()
        
        # 获取当前状态
        cur.execute("""
            SELECT total_predictions, correct_predictions, accuracy
            FROM agent_states
            WHERE agent_name = %s
        """, (agent_name,))
        
        row = cur.fetchone()
        if not row:
            logger.warning(f"⚠️ Agent不存在: {agent_name}")
            return
        
        total, correct_count, old_accuracy = row
        
        # 更新统计
        total += 1
        if correct:
            correct_count += 1
        
        new_accuracy = correct_count / total if total > 0 else 0
        
        # 指数移动平均更新accuracy
        alpha = 0.1  # 学习速率
        smoothed_accuracy = alpha * new_accuracy + (1 - alpha) * old_accuracy
        
        cur.execute("""
            UPDATE agent_states
            SET total_predictions = %s,
                correct_predictions = %s,
                accuracy = %s,
                last_updated = NOW()
            WHERE agent_name = %s
        """, (total, correct_count, smoothed_accuracy, agent_name))
        
        self.conn.commit()
        logger.info(f"✅ {agent_name}: {old_accuracy:.2%} → {smoothed_accuracy:.2%} (total={total})")
    
    def get_agent_state(self, agent_name: str) -> Optional[Dict]:
        """获取Agent状态"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT agent_name, version, accuracy, confidence, 
                   last_100_accuracy, strength_tags, weakness_tags,
                   learning_rate, total_predictions, correct_predictions
            FROM agent_states
            WHERE agent_name = %s
        """, (agent_name,))
        
        row = cur.fetchone()
        if not row:
            return None
        
        return {
            'agent_name': row[0],
            'version': row[1],
            'accuracy': row[2],
            'confidence': row[3],
            'last_100_accuracy': row[4],
            'strength_tags': row[5],
            'weakness_tags': row[6],
            'learning_rate': row[7],
            'total_predictions': row[8],
            'correct_predictions': row[9]
        }
    
    def get_all_agents(self) -> List[Dict]:
        """获取所有Agent状态"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT agent_name, version, accuracy, confidence,
                   total_predictions, correct_predictions
            FROM agent_states
            ORDER BY accuracy DESC
        """)
        
        agents = []
        for row in cur.fetchall():
            agents.append({
                'agent_name': row[0],
                'version': row[1],
                'accuracy': row[2],
                'confidence': row[3],
                'total_predictions': row[4],
                'correct_predictions': row[5]
            })
        
        return agents
    
    def update_confidence(self, agent_name: str, new_confidence: float):
        """更新Agent的Confidence（自我校准）"""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE agent_states
            SET confidence = %s, last_updated = NOW()
            WHERE agent_name = %s
        """, (new_confidence, agent_name))
        self.conn.commit()
        logger.info(f"✅ {agent_name} confidence更新: {new_confidence:.2f}")
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()


def test_agent_state_manager():
    """测试AgentStateManager"""
    print("=" * 80)
    print("测试: AgentStateManager")
    print("=" * 80)
    
    manager = AgentStateManager()
    
    # 测试1: 创建表
    print("\n[测试1] 创建agent_states表...")
    manager.create_table()
    
    # 测试2: 初始化Agent
    print("\n[测试2] 初始化8个Agent...")
    manager.init_agents()
    
    # 测试3: 获取所有Agent
    print("\n[测试3] 获取所有Agent状态...")
    agents = manager.get_all_agents()
    for agent in agents:
        print(f"  {agent['agent_name']:15s} | v{agent['version']} | "
              f"准确率:{agent['accuracy']:.2%} | 预测:{agent['total_predictions']}次")
    
    # 测试4: 更新预测结果
    print("\n[测试4] 模拟Bull Team预测...")
    manager.update_prediction_result('Bull Team', correct=True)
    manager.update_prediction_result('Bull Team', correct=True)
    manager.update_prediction_result('Bull Team', correct=False)
    
    # 测试5: 获取更新后的状态
    print("\n[测试5] 获取Bull Team最新状态...")
    bull_state = manager.get_agent_state('Bull Team')
    print(f"  准确率: {bull_state['accuracy']:.2%}")
    print(f"  总预测: {bull_state['total_predictions']}次")
    print(f"  正确: {bull_state['correct_predictions']}次")
    
    # 测试6: 更新Confidence
    print("\n[测试6] 更新Bull Team Confidence...")
    manager.update_confidence('Bull Team', 0.85)
    bull_state = manager.get_agent_state('Bull Team')
    print(f"  Confidence: {bull_state['confidence']:.2f}")
    
    manager.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_agent_state_manager()
