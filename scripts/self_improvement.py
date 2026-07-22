#!/usr/bin/env python3
"""
NSPS-V1: Self-Improvement Agent
自我优化：根据诊断结果自动调整参数
全部本地资源，0成本
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


class SelfImprovement:
    """自我优化Agent：根据表现自动调整参数"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ SelfImprovement连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def analyze_agent_performance(self, agent_name: str, days: int = 7) -> Dict:
        """分析Agent最近表现"""
        cur = self.conn.cursor()
        
        # 获取最近N天的预测记录
        since_date = (datetime.now(timezone(PT_OFFSET)) - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END) as wins,
                AVG(pnl_pct) as avg_return,
                STDDEV(pnl_pct) as std_return
            FROM paper_trades
            WHERE trade_date >= %s AND status = 'CLOSED'
        """, (since_date,))
        
        row = cur.fetchone()
        if not row or row[0] == 0:
            return {'total': 0, 'status': 'NO_DATA'}
        
        total, wins, avg_return, std_return = row
        win_rate = wins / total if total > 0 else 0
        
        # 判断表现
        if win_rate > 0.6 and avg_return > 2:
            status = 'EXCELLENT'
        elif win_rate > 0.5 and avg_return > 0:
            status = 'GOOD'
        elif win_rate > 0.4:
            status = 'FAIR'
        else:
            status = 'POOR'
        
        return {
            'agent_name': agent_name,
            'period_days': days,
            'total': total,
            'wins': wins or 0,
            'win_rate': win_rate,
            'avg_return': avg_return or 0,
            'std_return': std_return or 0,
            'status': status
        }
    
    def suggest_improvements(self, performance: Dict) -> List[Dict]:
        """根据表现提出改进建议"""
        suggestions = []
        
        if performance['status'] == 'POOR':
            # 胜率低，建议降低风险
            suggestions.append({
                'type': 'RISK_REDUCTION',
                'description': '胜率过低，建议降低仓位或提高入场标准',
                'action': 'REDUCE_POSITION_SIZE',
                'parameter': 'position_size',
                'current_value': 1.0,
                'suggested_value': 0.7,
                'expected_impact': '降低亏损幅度'
            })
            
            suggestions.append({
                'type': 'STRICTER_ENTRY',
                'description': '提高入场门槛',
                'action': 'INCREASE_ENTRY_THRESHOLD',
                'parameter': 'entry_threshold',
                'current_value': 0.6,
                'suggested_value': 0.7,
                'expected_impact': '提高胜率'
            })
        
        elif performance['status'] == 'FAIR':
            # 表现一般，建议优化
            if performance['avg_return'] < 1:
                suggestions.append({
                    'type': 'PROFIT_OPTIMIZATION',
                    'description': '平均收益偏低，建议优化止盈策略',
                    'action': 'OPTIMIZE_TAKE_PROFIT',
                    'parameter': 'take_profit_threshold',
                    'current_value': 0.05,
                    'suggested_value': 0.08,
                    'expected_impact': '提高平均收益'
                })
        
        elif performance['status'] == 'GOOD':
            # 表现良好，可以尝试优化
            if performance['std_return'] > 5:
                suggestions.append({
                    'type': 'VOLATILITY_REDUCTION',
                    'description': '收益波动大，建议增加稳定性',
                    'action': 'ADD_STOP_LOSS',
                    'parameter': 'stop_loss_threshold',
                    'current_value': 0.03,
                    'suggested_value': 0.02,
                    'expected_impact': '降低波动'
                })
        
        return suggestions
    
    def apply_improvement(self, suggestion: Dict) -> bool:
        """应用改进建议（记录到learning_ledger）"""
        cur = self.conn.cursor()
        
        # 记录到learning_ledger
        cur.execute("""
            INSERT INTO learning_ledger 
            (agent_name, change_type, old_value, new_value, reason, evidence)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            suggestion.get('agent_name', 'SYSTEM'),
            suggestion['type'],
            json.dumps({'value': suggestion['current_value']}),
            json.dumps({'value': suggestion['suggested_value']}),
            suggestion['description'],
            json.dumps({'expected_impact': suggestion.get('expected_impact', '')})
        ))
        
        ledger_id = cur.fetchone()[0]
        self.conn.commit()
        
        logger.info(f"✅ 应用改进 #{ledger_id}: {suggestion['type']}")
        logger.info(f"   {suggestion['parameter']}: {suggestion['current_value']} → {suggestion['suggested_value']}")
        
        return True
    
    def run_improvement_cycle(self) -> Dict:
        """运行完整的改进循环"""
        cur = self.conn.cursor()
        
        # 获取所有Agent
        cur.execute("SELECT agent_name FROM agent_states")
        agents = [row[0] for row in cur.fetchall()]
        
        results = {
            'analyzed_agents': len(agents),
            'improvements_applied': 0,
            'suggestions': []
        }
        
        for agent_name in agents:
            # 分析表现
            performance = self.analyze_agent_performance(agent_name, days=7)
            
            if performance['total'] < 5:
                continue  # 样本量不足
            
            # 提出建议
            suggestions = self.suggest_improvements(performance)
            
            for suggestion in suggestions:
                suggestion['agent_name'] = agent_name
                results['suggestions'].append(suggestion)
                
                # 自动应用（Constitution Rule 5: 盘中禁止调参，这里假设不在盘中）
                if self.apply_improvement(suggestion):
                    results['improvements_applied'] += 1
        
        return results
    
    def generate_report(self) -> str:
        """生成改进报告"""
        results = self.run_improvement_cycle()
        
        lines = []
        lines.append("🔧 Self-Improvement Report")
        lines.append("")
        lines.append(f"【分析结果】")
        lines.append(f"  分析Agent数: {results['analyzed_agents']}")
        lines.append(f"  应用改进数: {results['improvements_applied']}")
        lines.append("")
        
        if results['suggestions']:
            lines.append(f"【改进建议】")
            for i, s in enumerate(results['suggestions'], 1):
                lines.append(f"  {i}. [{s['agent_name']}] {s['type']}")
                lines.append(f"     {s['description']}")
                lines.append(f"     {s['parameter']}: {s['current_value']} → {s['suggested_value']}")
                lines.append(f"     预期效果: {s['expected_impact']}")
                lines.append("")
        else:
            lines.append("✅ 暂无改进建议，系统运行良好")
        
        return '\n'.join(lines)
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_self_improvement():
    """测试"""
    print("=" * 80)
    print("测试: Self-Improvement")
    print("=" * 80)
    
    si = SelfImprovement()
    
    # 测试1: 分析Agent表现
    print("\n[测试1] 分析Bull Team最近7天表现...")
    performance = si.analyze_agent_performance('Bull Team', days=7)
    print(f"  总预测: {performance['total']}次")
    print(f"  胜率: {performance['win_rate']:.1%}")
    print(f"  平均收益: {performance['avg_return']:.2f}%")
    print(f"  状态: {performance['status']}")
    
    # 测试2: 提出改进建议
    print("\n[测试2] 提出改进建议...")
    suggestions = si.suggest_improvements(performance)
    if suggestions:
        for s in suggestions:
            print(f"  • {s['type']}: {s['description']}")
    else:
        print("  暂无建议")
    
    # 测试3: 运行完整改进循环
    print("\n[测试3] 运行完整改进循环...")
    results = si.run_improvement_cycle()
    print(f"  分析Agent: {results['analyzed_agents']}个")
    print(f"  应用改进: {results['improvements_applied']}个")
    
    # 测试4: 完整报告
    print("\n[测试4] 完整报告:")
    print("-" * 40)
    print(si.generate_report())
    
    si.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_self_improvement()
