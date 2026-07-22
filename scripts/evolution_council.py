#!/usr/bin/env python3
"""
NSPS-V1 Core: Evolution Proposal System
Agent只有建议权，没有修改权。所有进化必须经过EC审批。
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

class EvolutionCouncil:
    """进化委员会：审批Agent提出的进化建议"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ EvolutionCouncil连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def create_table(self):
        """创建evolution_proposals表"""
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evolution_proposals (
                id SERIAL PRIMARY KEY,
                time TIMESTAMP NOT NULL DEFAULT NOW(),
                proposer_agent TEXT NOT NULL,
                proposal_type TEXT NOT NULL,
                title TEXT NOT NULL,
                hypothesis TEXT,
                evidence JSONB,
                expected_impact JSONB,
                implementation_plan JSONB,
                rollback_plan TEXT,
                cost_estimate REAL DEFAULT 0,
                ec_status TEXT DEFAULT 'PENDING',
                ec_votes JSONB DEFAULT '{}',
                ec_reasoning TEXT,
                testing_result JSONB,
                deploy_status TEXT DEFAULT 'NOT_STARTED',
                actual_result JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        self.conn.commit()
        logger.info("✅ evolution_proposals表已创建")
    
    def submit_proposal(self, proposer: str, proposal_type: str,
                        title: str, hypothesis: str,
                        evidence: Dict = None, expected_impact: Dict = None,
                        implementation_plan: List = None,
                        rollback_plan: str = None,
                        cost_estimate: float = 0) -> int:
        """Agent提交进化提案"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO evolution_proposals
            (proposer_agent, proposal_type, title, hypothesis,
             evidence, expected_impact, implementation_plan, rollback_plan, cost_estimate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (proposer, proposal_type, title, hypothesis,
              json.dumps(evidence or {}), json.dumps(expected_impact or {}),
              json.dumps(implementation_plan or []), rollback_plan, cost_estimate))
        
        proposal_id = cur.fetchone()[0]
        self.conn.commit()
        logger.info(f"✅ 提案 #{proposal_id} 已提交: {title} (by {proposer})")
        return proposal_id
    
    def vote(self, proposal_id: int, voter: str, vote: str, reasoning: str = ""):
        """EC成员投票"""
        cur = self.conn.cursor()
        
        # 获取当前投票
        cur.execute("SELECT ec_votes FROM evolution_proposals WHERE id = %s", (proposal_id,))
        row = cur.fetchone()
        if not row:
            logger.error(f"提案 #{proposal_id} 不存在")
            return
        
        votes = row[0] or {}
        votes[voter] = {'vote': vote, 'reasoning': reasoning}
        
        cur.execute("""
            UPDATE evolution_proposals
            SET ec_votes = %s
            WHERE id = %s
        """, (json.dumps(votes), proposal_id))
        self.conn.commit()
        logger.info(f"✅ {voter} 投票: {vote} (提案 #{proposal_id})")
    
    def finalize_decision(self, proposal_id: int) -> str:
        """最终决策：统计投票"""
        cur = self.conn.cursor()
        cur.execute("SELECT ec_votes FROM evolution_proposals WHERE id = %s", (proposal_id,))
        row = cur.fetchone()
        if not row:
            return 'ERROR'
        
        votes = row[0] or {}
        approve = sum(1 for v in votes.values() if v.get('vote') == 'APPROVE')
        reject = sum(1 for v in votes.values() if v.get('vote') == 'REJECT')
        
        # 至少3票赞成才能通过
        if approve >= 3:
            status = 'APPROVED'
        elif reject >= 2:
            status = 'REJECTED'
        else:
            status = 'NEEDS_MORE_VOTES'
        
        cur.execute("""
            UPDATE evolution_proposals
            SET ec_status = %s
            WHERE id = %s
        """, (status, proposal_id))
        self.conn.commit()
        logger.info(f"✅ 提案 #{proposal_id}: {status} (赞成{approve}, 反对{reject})")
        return status
    
    def get_pending_proposals(self) -> List[Dict]:
        """获取待审批的提案"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, time, proposer_agent, proposal_type, title, hypothesis, expected_impact
            FROM evolution_proposals
            WHERE ec_status = 'PENDING'
            ORDER BY time DESC
        """)
        
        results = []
        for row in cur.fetchall():
            results.append({
                'id': row[0],
                'time': row[1],
                'proposer': row[2],
                'type': row[3],
                'title': row[4],
                'hypothesis': row[5],
                'expected_impact': row[6]
            })
        return results
    
    def get_all_proposals(self, limit: int = 20) -> List[Dict]:
        """获取所有提案"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT id, time, proposer_agent, title, ec_status, deploy_status
            FROM evolution_proposals
            ORDER BY time DESC
            LIMIT %s
        """, (limit,))
        
        results = []
        for row in cur.fetchall():
            results.append({
                'id': row[0],
                'time': row[1],
                'proposer': row[2],
                'title': row[3],
                'status': row[4],
                'deploy': row[5]
            })
        return results
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_evolution_council():
    """测试EvolutionCouncil"""
    print("=" * 80)
    print("测试: EvolutionCouncil")
    print("=" * 80)
    
    ec = EvolutionCouncil()
    
    # 测试1: 创建表
    print("\n[测试1] 创建evolution_proposals表...")
    ec.create_table()
    
    # 测试2: 提交提案
    print("\n[测试2] Agent提交进化提案...")
    pid = ec.submit_proposal(
        proposer='News Agent',
        proposal_type='NEW_AGENT',
        title='增加Option Agent',
        hypothesis='IF 增加Option Agent分析Option Flow THEN Leader Accuracy提高5% BECAUSE Option Flow提前反映机构意图 MEASURED BY 过去1年胜率对比',
        evidence={'option_flow_correlation': 0.7, 'top_fund_usage': True},
        expected_impact={'metric': 'Leader Accuracy', 'current': 0.58, 'expected': 0.63},
        implementation_plan=['Layer 1: UT/SIT/RT (1天)', 'Layer 2: Backtest', 'Layer 3: Paper 30天'],
        rollback_plan='如果Paper Trading胜率<50%，自动拒绝',
        cost_estimate=0
    )
    
    # 测试3: EC投票
    print("\n[测试3] EC成员投票...")
    ec.vote(pid, 'Meta Brain', 'APPROVE', '证据充分，相关性0.7')
    ec.vote(pid, 'Historian', 'APPROVE', '历史上有类似成功案例')
    ec.vote(pid, 'Auditor', 'APPROVE', '回测结果可信')
    
    # 测试4: 最终决策
    print("\n[测试4] 最终决策...")
    status = ec.finalize_decision(pid)
    print(f"  结果: {status}")
    
    # 测试5: 查看提案
    print("\n[测试5] 查看所有提案...")
    proposals = ec.get_all_proposals()
    for p in proposals:
        print(f"  #{p['id']} | {p['title']} | {p['status']} | by {p['proposer']}")
    
    ec.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_evolution_council()
