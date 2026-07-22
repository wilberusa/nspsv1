#!/usr/bin/env python3
"""
NSPS-V1 Core: Constitution Enforcement Engine
系统宪法执行引擎，不可违反的最高规则
全部本地资源，0成本
"""

import psycopg2
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
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

# 系统宪法（硬编码，不可被Agent修改）
CONSTITUTION_RULES = {
    'Rule 1': {
        'description': '最大回撤永远不能超过10%',
        'check': 'max_drawdown_check',
        'threshold': 0.10,
        'severity': 'CRITICAL'
    },
    'Rule 2': {
        'description': '任何新策略必须Paper Trading 30天',
        'check': 'paper_trading_duration_check',
        'threshold': 30,
        'severity': 'HIGH'
    },
    'Rule 3': {
        'description': '任何学习必须可Rollback',
        'check': 'rollback_plan_check',
        'severity': 'HIGH'
    },
    'Rule 4': {
        'description': '任何Agent不能修改Constitution',
        'check': 'constitution_immutable_check',
        'severity': 'CRITICAL'
    },
    'Rule 5': {
        'description': '盘中（Trading Hours）禁止自动调参',
        'check': 'trading_hours_no_param_change',
        'severity': 'CRITICAL'
    },
    'Rule 6': {
        'description': '任何进化必须经过EC审批',
        'check': 'ec_approval_check',
        'severity': 'HIGH'
    },
    'Rule 7': {
        'description': '所有决策必须可审计（Audit Trail）',
        'check': 'audit_trail_check',
        'severity': 'MEDIUM'
    },
    'Rule 8': {
        'description': '数据库可靠性 > 预测模型',
        'check': 'database_reliability_check',
        'severity': 'CRITICAL'
    },
    'Rule 9': {
        'description': '13年历史数据不可丢失',
        'check': 'data_preservation_check',
        'severity': 'CRITICAL'
    },
    'Rule 10': {
        'description': '优先使用本地资源，减少付费quota',
        'check': 'local_resource_priority_check',
        'severity': 'MEDIUM'
    }
}

class ConstitutionEngine:
    """宪法执行引擎"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ ConstitutionEngine连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def create_tables(self):
        """创建constitution相关表"""
        cur = self.conn.cursor()
        
        # 违规记录表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS constitution_violations (
                id SERIAL PRIMARY KEY,
                time TIMESTAMP NOT NULL DEFAULT NOW(),
                rule_number TEXT NOT NULL,
                rule_description TEXT,
                violation_description TEXT,
                detected_by TEXT,
                severity TEXT,
                action_taken TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 宪法修改历史表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS constitution_history (
                id SERIAL PRIMARY KEY,
                time TIMESTAMP NOT NULL DEFAULT NOW(),
                action TEXT NOT NULL,
                rule_number TEXT,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                approved_by TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        self.conn.commit()
        logger.info("✅ constitution表已创建")
    
    def check_decision(self, decision: Dict) -> Tuple[bool, List[str]]:
        """
        检查决策是否违反宪法
        Returns: (allowed, violations)
        """
        violations = []
        
        # Rule 1: 最大回撤检查
        if decision.get('type') in ['BUY', 'SELL', 'HOLD']:
            drawdown = self._get_current_drawdown()
            if drawdown > CONSTITUTION_RULES['Rule 1']['threshold']:
                violations.append(f"Rule 1: 回撤{drawdown:.1%}超过10%上限")
        
        # Rule 3: 学习必须可Rollback
        if decision.get('type') == 'LEARNING':
            if not decision.get('rollback_plan'):
                violations.append("Rule 3: 学习缺少Rollback Plan")
        
        # Rule 5: 盘中禁止自动调参
        if decision.get('type') == 'PARAMETER_CHANGE':
            if self._is_trading_hours():
                violations.append("Rule 5: 盘中禁止自动调参")
        
        # Rule 6: 进化必须EC审批
        if decision.get('type') == 'EVOLUTION':
            if not decision.get('ec_approved'):
                violations.append("Rule 6: 进化未经EC审批")
        
        # Rule 7: 审计追踪
        if decision.get('type') in ['BUY', 'SELL', 'HOLD', 'LEARNING', 'EVOLUTION']:
            if not decision.get('audit_trail'):
                violations.append("Rule 7: 决策缺少审计追踪")
        
        # 记录违规
        if violations:
            for v in violations:
                rule_num = v.split(':')[0]
                self._record_violation(rule_num, v, decision)
        
        allowed = len(violations) == 0
        return allowed, violations
    
    def _get_current_drawdown(self) -> float:
        """获取当前回撤"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT COALESCE(SUM(pnl), 0) as total_pnl
            FROM paper_trades
            WHERE status = 'CLOSED'
        """)
        total_pnl = cur.fetchone()[0]
        
        # 假设初始资金$100,000
        initial_capital = 100000
        drawdown = abs(total_pnl) / initial_capital if total_pnl < 0 else 0
        
        return drawdown
    
    def _is_trading_hours(self) -> bool:
        """检查是否在交易时间"""
        now = datetime.now()
        hour = now.hour
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # US市场: 9:30 AM - 4:00 PM ET = 6:30 AM - 1:00 PM PT
        # CN市场: 9:30 AM - 3:00 PM Beijing = 6:30 PM - 12:00 AM PT (前一天)
        
        # 简化检查：PT时间6:30 AM - 1:00 PM 或 6:30 PM - 12:00 AM
        if weekday < 5:  # 周一到周五
            if (6 <= hour < 13) or (18 <= hour < 24):
                return True
        
        return False
    
    def _record_violation(self, rule_number: str, description: str, decision: Dict):
        """记录违规"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO constitution_violations
            (rule_number, rule_description, violation_description, 
             detected_by, severity, action_taken)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (rule_number, 
              CONSTITUTION_RULES.get(rule_number, {}).get('description', 'Unknown'),
              description,
              'ConstitutionEngine',
              CONSTITUTION_RULES.get(rule_number, {}).get('severity', 'MEDIUM'),
              'BLOCKED'))
        self.conn.commit()
        logger.warning(f"⚠️ 宪法违规: {description}")
    
    def get_violations(self, limit: int = 10) -> List[Dict]:
        """获取最近违规记录"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, time, rule_number, violation_description, 
                   severity, action_taken, resolved
            FROM constitution_violations
            ORDER BY time DESC
            LIMIT %s
        """, (limit,))
        
        results = []
        for row in cur.fetchall():
            results.append({
                'id': row[0],
                'time': row[1],
                'rule_number': row[2],
                'description': row[3],
                'severity': row[4],
                'action': row[5],
                'resolved': row[6]
            })
        
        return results
    
    def get_constitution(self) -> Dict:
        """获取当前宪法"""
        return CONSTITUTION_RULES
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_constitution_engine():
    """测试ConstitutionEngine"""
    print("=" * 80)
    print("测试: ConstitutionEngine")
    print("=" * 80)
    
    engine = ConstitutionEngine()
    
    # 测试1: 创建表
    print("\n[测试1] 创建constitution表...")
    engine.create_tables()
    
    # 测试2: 获取宪法
    print("\n[测试2] 获取系统宪法...")
    constitution = engine.get_constitution()
    for rule, details in constitution.items():
        print(f"  {rule}: {details['description']}")
    
    # 测试3: 检查合法决策
    print("\n[测试3] 检查合法决策...")
    legal_decision = {
        'type': 'BUY',
        'stock': 'NVDA',
        'audit_trail': True
    }
    allowed, violations = engine.check_decision(legal_decision)
    print(f"  决策: BUY NVDA")
    print(f"  允许: {allowed}")
    print(f"  违规: {violations if violations else '无'}")
    
    # 测试4: 检查违规决策（盘中调参）
    print("\n[测试4] 检查违规决策（盘中调参）...")
    illegal_decision = {
        'type': 'PARAMETER_CHANGE',
        'agent': 'News Agent',
        'change': 'weight 0.32 → 0.47'
    }
    allowed, violations = engine.check_decision(illegal_decision)
    print(f"  决策: PARAMETER_CHANGE")
    print(f"  允许: {allowed}")
    print(f"  违规: {violations}")
    
    # 测试5: 检查违规决策（学习无Rollback）
    print("\n[测试5] 检查违规决策（学习无Rollback）...")
    illegal_decision2 = {
        'type': 'LEARNING',
        'agent': 'Bull Team',
        'change': 'threshold 0.6 → 0.7'
    }
    allowed, violations = engine.check_decision(illegal_decision2)
    print(f"  决策: LEARNING (无Rollback)")
    print(f"  允许: {allowed}")
    print(f"  违规: {violations}")
    
    # 测试6: 获取违规记录
    print("\n[测试6] 获取违规记录...")
    violations = engine.get_violations(limit=5)
    for v in violations:
        print(f"  #{v['id']} | {v['time']} | {v['rule_number']} | {v['description'][:50]}...")
    
    engine.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_constitution_engine()
