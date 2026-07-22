#!/usr/bin/env python3
"""
NSPS-V1: Self-Evaluation Agent
自我评估：今天哪些预测成功？哪些失败？为什么？
全部本地资源，0成本
"""

import psycopg2
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


class SelfEvaluation:
    """自我评估Agent"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ SelfEvaluation连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def evaluate_today(self) -> Dict:
        """评估今日表现"""
        cur = self.conn.cursor()
        today = datetime.now(timezone(PT_OFFSET)).strftime('%Y-%m-%d')
        
        # 获取今日交易
        cur.execute("""
            SELECT symbol, market, pnl_pct, entry_prediction_score, 
                   predicted_change, exit_reason
            FROM paper_trades
            WHERE trade_date = %s AND status = 'CLOSED'
            ORDER BY pnl_pct DESC
        """, (today,))
        
        trades = cur.fetchall()
        
        if not trades:
            return {
                'date': today,
                'total': 0,
                'correct': 0,
                'incorrect': 0,
                'accuracy': 0,
                'wins': [],
                'losses': [],
                'lessons': []
            }
        
        wins = []
        losses = []
        
        for t in trades:
            symbol, market, pnl, score, predicted, reason = t
            trade_info = {
                'symbol': symbol,
                'market': market,
                'pnl_pct': pnl or 0,
                'predicted': predicted,
                'reason': reason
            }
            
            if pnl and pnl > 0:
                wins.append(trade_info)
            else:
                losses.append(trade_info)
        
        total = len(trades)
        correct = len(wins)
        accuracy = correct / total * 100 if total > 0 else 0
        
        # 生成教训
        lessons = self._generate_lessons(wins, losses)
        
        return {
            'date': today,
            'total': total,
            'correct': correct,
            'incorrect': len(losses),
            'accuracy': accuracy,
            'wins': wins,
            'losses': losses,
            'lessons': lessons
        }
    
    def _generate_lessons(self, wins: List, losses: List) -> List[str]:
        """生成教训"""
        lessons = []
        
        if not losses:
            lessons.append("今日全部盈利，策略表现良好")
            return lessons
        
        # 分析亏损模式
        avg_loss = sum(l['pnl_pct'] for l in losses) / len(losses)
        avg_win = sum(w['pnl_pct'] for w in wins) / len(wins) if wins else 0
        
        if avg_loss < -3:
            lessons.append(f"⚠️ 平均亏损{avg_loss:.1f}%，止损可能不够及时")
        
        if len(losses) > len(wins):
            lessons.append(f"⚠️ 亏损笔数({len(losses)})>盈利({len(wins)})，需要提高胜率")
        
        # 检查是否集中在某个市场
        us_losses = sum(1 for l in losses if l['market'] == 'us')
        cn_losses = sum(1 for l in losses if l['market'] == 'cn')
        
        if us_losses > cn_losses * 2:
            lessons.append("⚠️ US市场亏损集中，建议审查US策略")
        elif cn_losses > us_losses * 2:
            lessons.append("⚠️ CN市场亏损集中，建议审查CN策略")
        
        # 盈亏比
        if avg_win > 0 and avg_loss < 0:
            profit_factor = abs(avg_win / avg_loss)
            if profit_factor < 1.5:
                lessons.append(f"⚠️ 盈亏比{profit_factor:.1f}偏低，需要>1.5")
            else:
                lessons.append(f"✅ 盈亏比{profit_factor:.1f}良好")
        
        return lessons
    
    def check_consecutive_losses(self, threshold: int = 3) -> Dict:
        """检查连续亏损"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT pnl_pct, symbol, market, trade_date
            FROM paper_trades
            WHERE status = 'CLOSED'
            ORDER BY exit_time DESC
            LIMIT 20
        """)
        
        trades = cur.fetchall()
        
        consecutive = 0
        consecutive_trades = []
        
        for t in trades:
            pnl, symbol, market, date = t
            if pnl and pnl < 0:
                consecutive += 1
                consecutive_trades.append({'symbol': symbol, 'market': market, 'date': date, 'pnl': pnl})
            else:
                break
        
        should_alert = consecutive >= threshold
        
        return {
            'consecutive_losses': consecutive,
            'threshold': threshold,
            'should_alert': should_alert,
            'trades': consecutive_trades
        }
    
    def generate_report(self) -> str:
        """生成自我评估报告"""
        eval_result = self.evaluate_today()
        consec = self.check_consecutive_losses()
        
        lines = []
        lines.append(f"🔍 Self-Evaluation Report — {eval_result['date']}")
        lines.append("")
        
        if eval_result['total'] == 0:
            lines.append("今日无交易数据")
            return '\n'.join(lines)
        
        lines.append(f"【今日表现】")
        lines.append(f"  总交易: {eval_result['total']}笔")
        lines.append(f"  正确: {eval_result['correct']}笔")
        lines.append(f"  错误: {eval_result['incorrect']}笔")
        lines.append(f"  准确率: {eval_result['accuracy']:.1f}%")
        lines.append("")
        
        if eval_result['wins']:
            lines.append(f"【盈利交易】")
            for w in eval_result['wins'][:3]:
                lines.append(f"  ✅ {w['symbol']}({w['market']}) {w['pnl_pct']:+.2f}%")
            lines.append("")
        
        if eval_result['losses']:
            lines.append(f"【亏损交易】")
            for l in eval_result['losses'][:3]:
                lines.append(f"  ❌ {l['symbol']}({l['market']}) {l['pnl_pct']:+.2f}%")
            lines.append("")
        
        if eval_result['lessons']:
            lines.append(f"【教训】")
            for lesson in eval_result['lessons']:
                lines.append(f"  {lesson}")
            lines.append("")
        
        if consec['should_alert']:
            lines.append(f"⚠️ 连续亏损警告: {consec['consecutive_losses']}笔")
            lines.append(f"  建议: 暂停交易，审查策略")
        
        return '\n'.join(lines)
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_self_evaluation():
    """测试"""
    print("=" * 80)
    print("测试: Self-Evaluation")
    print("=" * 80)
    
    se = SelfEvaluation()
    
    # 测试1: 评估今日
    print("\n[测试1] 评估今日表现...")
    result = se.evaluate_today()
    print(f"  总交易: {result['total']}笔")
    print(f"  准确率: {result['accuracy']:.1f}%")
    print(f"  教训: {len(result['lessons'])}条")
    
    # 测试2: 连续亏损检查
    print("\n[测试2] 连续亏损检查...")
    consec = se.check_consecutive_losses(threshold=3)
    print(f"  连续亏损: {consec['consecutive_losses']}笔")
    print(f"  需要告警: {consec['should_alert']}")
    
    # 测试3: 完整报告
    print("\n[测试3] 完整报告:")
    print("-" * 40)
    print(se.generate_report())
    
    se.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_self_evaluation()
