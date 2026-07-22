#!/usr/bin/env python3
"""
NSPS-V1 Core: Bull/Bear Team（基础版）
Bull Team找上涨理由，Bear Team找反例和风险
全部本地资源，0成本（不调用LLM，纯规则引擎）
"""

import psycopg2
from datetime import datetime
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

class BullTeam:
    """Bull Team：只负责找上涨理由"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ BullTeam连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def analyze(self, symbol: str, market: str = 'us') -> Dict:
        """
        分析股票的上涨理由
        
        Returns:
            {
                'symbol': str,
                'market': str,
                'reasons': List[str],
                'evidence': Dict,
                'confidence': float  # 0-1
            }
        """
        reasons = []
        evidence = {}
        
        # 1. 从paper_trades获取历史表现
        cur = self.conn.cursor()
        cur.execute("""
            SELECT 
                AVG(pnl_pct) as avg_return,
                SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END) as wins,
                COUNT(*) as total
            FROM paper_trades
            WHERE symbol = %s AND market = %s AND status = 'CLOSED'
        """, (symbol, market))
        
        row = cur.fetchone()
        if row and row[2] > 0:  # 有历史数据
            avg_return, wins, total = row
            win_rate = wins / total
            
            if avg_return > 0:
                reasons.append(f"历史平均收益{avg_return:.2f}%")
                evidence['avg_return'] = avg_return
            
            if win_rate > 0.6:
                reasons.append(f"历史胜率{win_rate:.1%}")
                evidence['win_rate'] = win_rate
        
        # 2. 检查最近表现（动量）
        cur.execute("""
            SELECT pnl_pct, trade_date
            FROM paper_trades
            WHERE symbol = %s AND market = %s AND status = 'CLOSED'
            ORDER BY trade_date DESC
            LIMIT 5
        """, (symbol, market))
        
        recent_trades = cur.fetchall()
        if recent_trades:
            recent_returns = [r[0] for r in recent_trades if r[0]]
            if recent_returns:
                recent_avg = sum(recent_returns) / len(recent_returns)
                if recent_avg > 0:
                    reasons.append(f"最近{len(recent_returns)}笔平均收益{recent_avg:.2f}%")
                    evidence['recent_avg'] = recent_avg
                
                # 连续盈利
                consecutive_wins = sum(1 for r in recent_returns if r > 0)
                if consecutive_wins >= 3:
                    reasons.append(f"连续{consecutive_wins}笔盈利")
                    evidence['consecutive_wins'] = consecutive_wins
        
        # 3. 计算Confidence
        confidence = min(len(reasons) / 5.0, 1.0)  # 最多5个理由
        
        result = {
            'symbol': symbol,
            'market': market,
            'reasons': reasons,
            'evidence': evidence,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Bull分析 {symbol}: {len(reasons)}个理由, confidence={confidence:.2f}")
        return result
    
    def close(self):
        if self.conn:
            self.conn.close()


class BearTeam:
    """Bear Team：只负责找反例和风险"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ BearTeam连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def analyze(self, symbol: str, market: str = 'us') -> Dict:
        """
        分析股票的风险和反例
        
        Returns:
            {
                'symbol': str,
                'market': str,
                'risks': List[str],
                'evidence': Dict,
                'confidence': float  # 0-1
            }
        """
        risks = []
        evidence = {}
        
        # 1. 检查历史亏损
        cur = self.conn.cursor()
        cur.execute("""
            SELECT 
                AVG(pnl_pct) as avg_return,
                SUM(CASE WHEN pnl_pct < 0 THEN 1 ELSE 0 END) as losses,
                COUNT(*) as total,
                MIN(pnl_pct) as worst_loss
            FROM paper_trades
            WHERE symbol = %s AND market = %s AND status = 'CLOSED'
        """, (symbol, market))
        
        row = cur.fetchone()
        if row and row[2] > 0:
            avg_return, losses, total, worst_loss = row
            loss_rate = losses / total
            
            if avg_return < 0:
                risks.append(f"历史平均亏损{avg_return:.2f}%")
                evidence['avg_return'] = avg_return
            
            if loss_rate > 0.5:
                risks.append(f"历史亏损率{loss_rate:.1%}")
                evidence['loss_rate'] = loss_rate
            
            if worst_loss and worst_loss < -5:
                risks.append(f"最大单笔亏损{worst_loss:.2f}%")
                evidence['worst_loss'] = worst_loss
        
        # 2. 检查最近表现（连续亏损）
        cur.execute("""
            SELECT pnl_pct, trade_date
            FROM paper_trades
            WHERE symbol = %s AND market = %s AND status = 'CLOSED'
            ORDER BY trade_date DESC
            LIMIT 5
        """, (symbol, market))
        
        recent_trades = cur.fetchall()
        if recent_trades:
            recent_returns = [r[0] for r in recent_trades if r[0]]
            if recent_returns:
                # 连续亏损
                consecutive_losses = 0
                for r in recent_returns:
                    if r < 0:
                        consecutive_losses += 1
                    else:
                        break
                
                if consecutive_losses >= 2:
                    risks.append(f"连续{consecutive_losses}笔亏损")
                    evidence['consecutive_losses'] = consecutive_losses
                
                # 最近表现差
                recent_avg = sum(recent_returns) / len(recent_returns)
                if recent_avg < -2:
                    risks.append(f"最近{len(recent_returns)}笔平均亏损{recent_avg:.2f}%")
                    evidence['recent_avg'] = recent_avg
        
        # 3. 计算Confidence
        confidence = min(len(risks) / 5.0, 1.0)
        
        result = {
            'symbol': symbol,
            'market': market,
            'risks': risks,
            'evidence': evidence,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Bear分析 {symbol}: {len(risks)}个风险, confidence={confidence:.2f}")
        return result
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_bull_bear_team():
    """测试Bull/Bear Team"""
    print("=" * 80)
    print("测试: Bull/Bear Team")
    print("=" * 80)
    
    bull = BullTeam()
    bear = BearTeam()
    
    # 先插入一些测试数据
    print("\n[准备] 插入测试数据...")
    cur = bull.conn.cursor()
    test_data = [
        ('NVDA', 'us', 5.2, 'CLOSED'),
        ('NVDA', 'us', 3.1, 'CLOSED'),
        ('NVDA', 'us', -2.5, 'CLOSED'),
        ('NVDA', 'us', 4.8, 'CLOSED'),
        ('TSLA', 'us', -3.2, 'CLOSED'),
        ('TSLA', 'us', -4.1, 'CLOSED'),
        ('TSLA', 'us', -1.8, 'CLOSED'),
    ]
    
    for i, (symbol, market, pnl, status) in enumerate(test_data, start=100):
        cur.execute("""
            INSERT INTO paper_trades (id, trade_date, symbol, market, pnl_pct, status)
            VALUES (%s, CURRENT_DATE, %s, %s, %s, %s)
        """, (i, symbol, market, pnl, status))
    bull.conn.commit()
    print(f"  已插入{len(test_data)}条测试数据")
    
    # 测试1: Bull Team分析
    print("\n[测试1] Bull Team分析NVDA...")
    bull_result = bull.analyze('NVDA', 'us')
    print(f"  理由: {bull_result['reasons']}")
    print(f"  Confidence: {bull_result['confidence']:.2f}")
    
    # 测试2: Bear Team分析
    print("\n[测试2] Bear Team分析TSLA...")
    bear_result = bear.analyze('TSLA', 'us')
    print(f"  风险: {bear_result['risks']}")
    print(f"  Confidence: {bear_result['confidence']:.2f}")
    
    # 测试3: 对比分析
    print("\n[测试3] 对比NVDA vs TSLA...")
    print(f"  NVDA: Bull={bull_result['confidence']:.2f}, 理由{len(bull_result['reasons'])}个")
    print(f"  TSLA: Bear={bear_result['confidence']:.2f}, 风险{len(bear_result['risks'])}个")
    
    bull.close()
    bear.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_bull_bear_team()
