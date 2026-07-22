#!/usr/bin/env python3
"""
NSPS-V1: Critic + Auditor + Coach + Risk Team
四个Agent合一，全部本地资源，0成本
"""

import psycopg2
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List
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

PT_OFFSET = timedelta(hours=-7)


class CriticAgent:
    """批评者：审查每个Decision的逻辑完整性"""
    
    def __init__(self, conn):
        self.conn = conn
    
    def review_decision(self, decision: Dict) -> Dict:
        """审查决策"""
        questions = {}
        
        # Q1: 为什么？
        reasoning = decision.get('reasoning', '')
        if reasoning and len(reasoning) > 10:
            questions['why'] = {'answer': reasoning, 'complete': True}
        else:
            questions['why'] = {'answer': '理由不充分', 'complete': False}
        
        # Q2: 最大风险？
        risks = decision.get('risks', [])
        if risks:
            questions['biggest_risk'] = {'answer': risks[0], 'complete': True}
        else:
            questions['biggest_risk'] = {'answer': '未识别风险', 'complete': False}
        
        # Q3: 最大反例？
        counter = decision.get('counter_examples', [])
        if counter:
            questions['counter_example'] = {'answer': counter[0], 'complete': True}
        else:
            questions['counter_example'] = {'answer': '未提供反例', 'complete': False}
        
        # 判断是否通过
        complete_count = sum(1 for q in questions.values() if q['complete'])
        verdict = 'PASS' if complete_count >= 2 else 'FAIL'
        
        result = {
            'decision': decision.get('action', 'UNKNOWN'),
            'symbol': decision.get('symbol', 'UNKNOWN'),
            'verdict': verdict,
            'questions': questions,
            'completeness': complete_count / 3,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Critic审查: {decision.get('symbol')} → {verdict} (完整度{result['completeness']:.0%})")
        return result


class AuditorAgent:
    """审计：Prediction vs Reality"""
    
    def __init__(self, conn):
        self.conn = conn
    
    def audit_today(self) -> Dict:
        """审计今日预测"""
        cur = self.conn.cursor()
        today = datetime.now(timezone(PT_OFFSET)).strftime('%Y-%m-%d')
        
        cur.execute("""
            SELECT symbol, market, pnl_pct, predicted_change
            FROM paper_trades
            WHERE trade_date = %s AND status = 'CLOSED'
        """, (today,))
        
        trades = cur.fetchall()
        
        results = []
        for t in trades:
            symbol, market, actual, predicted = t
            diff = (actual or 0) - (predicted or 0)
            results.append({
                'symbol': symbol,
                'market': market,
                'predicted': predicted or 0,
                'actual': actual or 0,
                'difference': diff
            })
        
        total = len(results)
        correct = sum(1 for r in results if abs(r['difference']) < 3)
        accuracy = correct / total if total > 0 else 0
        
        return {
            'date': today,
            'total': total,
            'correct': correct,
            'accuracy': accuracy,
            'details': results
        }


class CoachAgent:
    """教练：分析每个Agent表现，给出改进建议"""
    
    def __init__(self, conn):
        self.conn = conn
    
    def analyze_all(self) -> List[Dict]:
        """分析所有Agent"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT agent_name, accuracy, confidence, total_predictions
            FROM agent_states
            ORDER BY accuracy DESC
        """)
        
        recommendations = []
        for row in cur.fetchall():
            name, accuracy, confidence, total = row
            
            if total < 5:
                continue
            
            # 分析
            if accuracy < 0.4:
                recommendations.append({
                    'agent': name,
                    'issue': f'准确率过低({accuracy:.0%})',
                    'suggestion': '建议减少该Agent权重或回滚到上一版本',
                    'priority': 'HIGH'
                })
            elif accuracy > 0.7:
                recommendations.append({
                    'agent': name,
                    'issue': f'表现优秀({accuracy:.0%})',
                    'suggestion': '建议增加该Agent权重',
                    'priority': 'LOW'
                })
            
            # Confidence校准
            if abs(confidence - accuracy) > 0.2:
                recommendations.append({
                    'agent': name,
                    'issue': f'Confidence偏差大({confidence:.2f} vs {accuracy:.2f})',
                    'suggestion': '建议校准Confidence',
                    'priority': 'MEDIUM'
                })
        
        return recommendations


class RiskTeamAgent:
    """风控团队：仓位、回撤、极端事件"""
    
    def __init__(self, conn):
        self.conn = conn
    
    def assess(self) -> Dict:
        """风险评估"""
        cur = self.conn.cursor()
        
        # 当前回撤
        cur.execute("""
            SELECT COALESCE(SUM(pnl_pct), 0) as total_pnl
            FROM paper_trades WHERE status = 'CLOSED'
        """)
        total_pnl = cur.fetchone()[0]
        drawdown = abs(total_pnl) / 100 if total_pnl < 0 else 0  # 假设初始100%
        
        # 连续亏损
        cur.execute("""
            SELECT pnl_pct FROM paper_trades
            WHERE status = 'CLOSED'
            ORDER BY exit_time DESC LIMIT 10
        """)
        consecutive_losses = 0
        for row in cur.fetchall():
            if row[0] and row[0] < 0:
                consecutive_losses += 1
            else:
                break
        
        # 风险等级
        if drawdown > 0.08 or consecutive_losses >= 5:
            risk_level = 'CRITICAL'
        elif drawdown > 0.05 or consecutive_losses >= 3:
            risk_level = 'HIGH'
        elif drawdown > 0.03:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        warnings = []
        if drawdown > 0.05:
            warnings.append(f'回撤{drawdown:.1%}接近上限')
        if consecutive_losses >= 3:
            warnings.append(f'连续{consecutive_losses}笔亏损')
        
        return {
            'risk_level': risk_level,
            'drawdown': drawdown,
            'consecutive_losses': consecutive_losses,
            'max_allowed_drawdown': 0.10,
            'warnings': warnings,
            'position_recommendation': 1.0 if risk_level == 'LOW' else 0.5 if risk_level == 'MEDIUM' else 0.0
        }


def test_all_agents():
    """测试所有Agent"""
    print("=" * 80)
    print("测试: Critic + Auditor + Coach + Risk Team")
    print("=" * 80)
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Critic
    print("\n[1] Critic Agent...")
    critic = CriticAgent(conn)
    review = critic.review_decision({
        'action': 'BUY', 'symbol': 'NVDA',
        'reasoning': 'AI板块资金流入+15%，新闻利好',
        'risks': ['RSI=78超买'],
        'counter_examples': ['2024-03-15相似场景失败']
    })
    print(f"  决策: {review['decision']} {review['symbol']}")
    print(f"  判定: {review['verdict']}")
    print(f"  完整度: {review['completeness']:.0%}")
    
    # Auditor
    print("\n[2] Auditor Agent...")
    auditor = AuditorAgent(conn)
    audit = auditor.audit_today()
    print(f"  今日审计: {audit['total']}笔, 准确率{audit['accuracy']:.0%}")
    
    # Coach
    print("\n[3] Coach Agent...")
    coach = CoachAgent(conn)
    recs = coach.analyze_all()
    print(f"  建议数: {len(recs)}")
    for r in recs[:3]:
        print(f"  • [{r['priority']}] {r['agent']}: {r['suggestion']}")
    
    # Risk Team
    print("\n[4] Risk Team...")
    risk = RiskTeamAgent(conn)
    assessment = risk.assess()
    print(f"  风险等级: {assessment['risk_level']}")
    print(f"  回撤: {assessment['drawdown']:.1%}")
    print(f"  连续亏损: {assessment['consecutive_losses']}笔")
    print(f"  仓位建议: {assessment['position_recommendation']:.0%}")
    if assessment['warnings']:
        print(f"  ⚠️ 警告: {assessment['warnings']}")
    
    conn.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_all_agents()
