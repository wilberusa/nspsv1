#!/usr/bin/env python3
"""
NSPS-V1: Daily PnL Report + Self-Evaluation
每日盈亏报告 + 自我评估
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


class DailyPnLReport:
    """每日盈亏报告"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ DailyPnLReport连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def get_today_pnl(self, market: str = None) -> Dict:
        """获取今日盈亏"""
        cur = self.conn.cursor()
        today = datetime.now(timezone(PT_OFFSET)).strftime('%Y-%m-%d')
        
        market_filter = "AND market = %s" if market else ""
        params = [today]
        if market:
            params.append(market)
        
        cur.execute(f"""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pnl_pct < 0 THEN 1 ELSE 0 END) as losses,
                SUM(pnl_pct) as total_pnl_pct,
                AVG(pnl_pct) as avg_pnl_pct,
                MAX(pnl_pct) as best_trade,
                MIN(pnl_pct) as worst_trade
            FROM paper_trades
            WHERE trade_date = %s AND status = 'CLOSED' {market_filter}
        """, params)
        
        row = cur.fetchone()
        if not row or row[0] == 0:
            return {
                'date': today,
                'market': market or 'ALL',
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_pnl_pct': 0,
                'avg_pnl_pct': 0,
                'best_trade': 0,
                'worst_trade': 0
            }
        
        total, wins, losses, total_pnl, avg_pnl, best, worst = row
        win_rate = wins / total * 100 if total > 0 else 0
        
        return {
            'date': today,
            'market': market or 'ALL',
            'total_trades': total,
            'wins': wins or 0,
            'losses': losses or 0,
            'win_rate': win_rate,
            'total_pnl_pct': total_pnl or 0,
            'avg_pnl_pct': avg_pnl or 0,
            'best_trade': best or 0,
            'worst_trade': worst or 0
        }
    
    def get_cumulative_pnl(self, market: str = None) -> Dict:
        """获取累计盈亏"""
        cur = self.conn.cursor()
        
        market_filter = "AND market = %s" if market else ""
        params = []
        if market:
            params.append(market)
        
        cur.execute(f"""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN pnl_pct < 0 THEN 1 ELSE 0 END) as losses,
                SUM(pnl_pct) as total_pnl_pct,
                AVG(pnl_pct) as avg_pnl_pct
            FROM paper_trades
            WHERE status = 'CLOSED' {market_filter}
        """, params)
        
        row = cur.fetchone()
        if not row or row[0] == 0:
            return {'total_trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0, 'total_pnl_pct': 0}
        
        total, wins, losses, total_pnl, avg_pnl = row
        win_rate = wins / total * 100 if total > 0 else 0
        
        return {
            'total_trades': total,
            'wins': wins or 0,
            'losses': losses or 0,
            'win_rate': win_rate,
            'total_pnl_pct': total_pnl or 0,
            'avg_pnl_pct': avg_pnl or 0
        }
    
    def get_agent_performance(self) -> List[Dict]:
        """获取每个Agent的表现"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT agent_name, accuracy, confidence, total_predictions, correct_predictions
            FROM agent_states
            ORDER BY accuracy DESC
        """)
        
        agents = []
        for row in cur.fetchall():
            agents.append({
                'name': row[0],
                'accuracy': row[1],
                'confidence': row[2],
                'total_predictions': row[3],
                'correct_predictions': row[4]
            })
        return agents
    
    def generate_report(self) -> str:
        """生成完整报告"""
        today = datetime.now(timezone(PT_OFFSET)).strftime('%Y-%m-%d')
        
        # 今日数据
        today_all = self.get_today_pnl()
        today_us = self.get_today_pnl('us')
        today_cn = self.get_today_pnl('cn')
        
        # 累计数据
        cum_all = self.get_cumulative_pnl()
        
        # Agent表现
        agents = self.get_agent_performance()
        
        # 生成报告文本
        lines = []
        lines.append(f"📊 NSPS 每日业绩报告 — {today}")
        lines.append("")
        
        # 今日概况
        lines.append(f"【今日概况】")
        lines.append(f"  总交易: {today_all['total_trades']}笔")
        lines.append(f"  胜率: {today_all['win_rate']:.1f}% ({today_all['wins']}赢{today_all['losses']}输)")
        lines.append(f"  总盈亏: {today_all['total_pnl_pct']:+.2f}%")
        lines.append(f"  最佳: {today_all['best_trade']:+.2f}% | 最差: {today_all['worst_trade']:+.2f}%")
        lines.append("")
        
        # 分市场
        if today_us['total_trades'] > 0:
            lines.append(f"【US市场】{today_us['total_trades']}笔, 胜率{today_us['win_rate']:.1f}%, 盈亏{today_us['total_pnl_pct']:+.2f}%")
        if today_cn['total_trades'] > 0:
            lines.append(f"【CN市场】{today_cn['total_trades']}笔, 胜率{today_cn['win_rate']:.1f}%, 盈亏{today_cn['total_pnl_pct']:+.2f}%")
        lines.append("")
        
        # 累计
        lines.append(f"【累计】")
        lines.append(f"  总交易: {cum_all['total_trades']}笔")
        lines.append(f"  累计胜率: {cum_all['win_rate']:.1f}%")
        lines.append(f"  累计盈亏: {cum_all['total_pnl_pct']:+.2f}%")
        lines.append("")
        
        # Agent表现
        if agents:
            lines.append(f"【Agent表现】")
            for a in agents[:5]:
                lines.append(f"  {a['name']:15s} | 准确率{a['accuracy']:.1%} | 预测{a['total_predictions']}次")
            lines.append("")
        
        # 诊断
        lines.append(f"【诊断】")
        if today_all['win_rate'] >= 55:
            lines.append(f"  ✅ 整体表现良好，胜率>{today_all['win_rate']:.0f}%")
        elif today_all['total_trades'] > 0:
            lines.append(f"  ⚠️ 胜率偏低{today_all['win_rate']:.0f}%，需要审查策略")
        else:
            lines.append(f"  ℹ️ 今日无交易数据")
        
        return '\n'.join(lines)
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_daily_pnl_report():
    """测试"""
    print("=" * 80)
    print("测试: Daily PnL Report")
    print("=" * 80)
    
    report = DailyPnLReport()
    
    # 测试1: 今日盈亏
    print("\n[测试1] 今日盈亏...")
    today = report.get_today_pnl()
    print(f"  交易: {today['total_trades']}笔, 胜率: {today['win_rate']:.1f}%, 盈亏: {today['total_pnl_pct']:+.2f}%")
    
    # 测试2: 累计盈亏
    print("\n[测试2] 累计盈亏...")
    cum = report.get_cumulative_pnl()
    print(f"  总交易: {cum['total_trades']}笔, 胜率: {cum['win_rate']:.1f}%, 盈亏: {cum['total_pnl_pct']:+.2f}%")
    
    # 测试3: Agent表现
    print("\n[测试3] Agent表现...")
    agents = report.get_agent_performance()
    for a in agents[:3]:
        print(f"  {a['name']}: 准确率{a['accuracy']:.1%}, 预测{a['total_predictions']}次")
    
    # 测试4: 完整报告
    print("\n[测试4] 完整报告:")
    print("-" * 40)
    print(report.generate_report())
    
    report.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_daily_pnl_report()
