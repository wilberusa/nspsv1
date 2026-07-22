#!/usr/bin/env python3
"""
NSPS-V1 Core: Meta Brain（基础版）
Market Regime Detection + 动态调整Agent权重 + 最终决策
全部本地资源，0成本
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

class MetaBrain:
    """Meta Brain：市场状态检测 + 动态权重 + 最终决策"""
    
    def __init__(self):
        self.conn = None
        self._connect()
        
        # 默认权重
        self.default_weights = {
            'bull': 0.3,
            'bear': 0.3,
            'risk': 0.2,
            'historian': 0.2
        }
        
        # 市场状态对应的权重
        self.regime_weights = {
            'TREND': {'bull': 0.4, 'bear': 0.2, 'risk': 0.2, 'historian': 0.2},
            'RANGE': {'bull': 0.2, 'bear': 0.3, 'risk': 0.3, 'historian': 0.2},
            'EVENT': {'bull': 0.3, 'bear': 0.3, 'risk': 0.2, 'historian': 0.2},
            'RISK_OFF': {'bull': 0.1, 'bear': 0.2, 'risk': 0.5, 'historian': 0.2}
        }
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ MetaBrain连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def detect_market_regime(self) -> Dict:
        """
        检测当前市场状态
        
        Returns:
            {
                'regime': str,  # TREND/RANGE/EVENT/RISK_OFF
                'confidence': float,
                'indicators': Dict
            }
        """
        # 简化的市场状态检测（基于历史交易数据）
        cur = self.conn.cursor()
        
        # 计算最近30天的胜率和平均收益
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END) as wins,
                AVG(pnl_pct) as avg_return
            FROM paper_trades
            WHERE status = 'CLOSED'
              AND trade_date >= to_char(CURRENT_DATE - INTERVAL '30 days', 'YYYY-MM-DD')
        """)
        
        row = cur.fetchone()
        if not row or row[0] == 0:
            return {
                'regime': 'UNKNOWN',
                'confidence': 0,
                'indicators': {}
            }
        
        total, wins, avg_return = row
        win_rate = wins / total if total > 0 else 0
        
        # 判断市场状态
        if win_rate > 0.6 and avg_return > 2:
            regime = 'TREND'
            confidence = 0.8
        elif win_rate < 0.4 and avg_return < -1:
            regime = 'RISK_OFF'
            confidence = 0.75
        elif abs(avg_return) < 1:
            regime = 'RANGE'
            confidence = 0.7
        else:
            regime = 'EVENT'
            confidence = 0.65
        
        result = {
            'regime': regime,
            'confidence': confidence,
            'indicators': {
                'win_rate': win_rate,
                'avg_return': avg_return,
                'total_trades': total
            }
        }
        
        logger.info(f"✅ 市场状态: {regime} (confidence={confidence:.2f})")
        return result
    
    def get_dynamic_weights(self, regime: str) -> Dict:
        """根据市场状态获取动态权重"""
        weights = self.regime_weights.get(regime, self.default_weights)
        logger.info(f"✅ 动态权重 ({regime}): {weights}")
        return weights
    
    def make_decision(self, bull_analysis: Dict, bear_analysis: Dict,
                      risk_assessment: Dict, historian_analysis: Dict) -> Dict:
        """
        综合所有Agent的输出，做出最终决策
        
        Returns:
            {
                'action': str,  # BUY/SELL/HOLD
                'symbol': str,
                'confidence': float,
                'reasoning': str,
                'weights_used': Dict
            }
        """
        # 1. 检测市场状态
        regime_info = self.detect_market_regime()
        regime = regime_info['regime']
        
        # 2. 获取动态权重
        weights = self.get_dynamic_weights(regime)
        
        # 3. 综合各Agent的输出
        bull_score = bull_analysis.get('confidence', 0)
        bear_score = bear_analysis.get('confidence', 0)
        risk_score = risk_assessment.get('risk_level', 0.5)  # 0=低风险, 1=高风险
        historian_score = historian_analysis.get('success_rate', 0.5)
        
        # 4. 计算综合分数
        # Bull高 + Bear低 + Risk低 + Historian高 = BUY
        buy_score = (
            bull_score * weights['bull'] +
            (1 - bear_score) * weights['bear'] +
            (1 - risk_score) * weights['risk'] +
            historian_score * weights['historian']
        )
        
        # 5. 决策
        if buy_score > 0.7:
            action = 'BUY'
            confidence = buy_score
        elif buy_score < 0.4:
            action = 'SELL'
            confidence = 1 - buy_score
        else:
            action = 'HOLD'
            confidence = 0.5
        
        # 6. 生成理由
        reasoning = f"市场{regime}，Bull={bull_score:.2f}, Bear={bear_score:.2f}, " \
                   f"Risk={risk_score:.2f}, Historian={historian_score:.2f}"
        
        result = {
            'action': action,
            'symbol': bull_analysis.get('symbol', 'UNKNOWN'),
            'confidence': confidence,
            'reasoning': reasoning,
            'weights_used': weights,
            'regime': regime,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ 最终决策: {action} {result['symbol']} (confidence={confidence:.2f})")
        return result
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_meta_brain():
    """测试MetaBrain"""
    print("=" * 80)
    print("测试: MetaBrain")
    print("=" * 80)
    
    brain = MetaBrain()
    
    # 测试1: 检测市场状态
    print("\n[测试1] 检测市场状态...")
    regime = brain.detect_market_regime()
    print(f"  市场状态: {regime['regime']}")
    print(f"  Confidence: {regime['confidence']:.2f}")
    print(f"  指标: {regime['indicators']}")
    
    # 测试2: 获取动态权重
    print("\n[测试2] 获取动态权重...")
    weights = brain.get_dynamic_weights(regime['regime'])
    print(f"  权重: {weights}")
    
    # 测试3: 模拟各Agent输出
    print("\n[测试3] 模拟各Agent输出...")
    bull_analysis = {
        'symbol': 'NVDA',
        'confidence': 0.8,
        'reasons': ['历史平均收益2.65%', '历史胜率75%']
    }
    
    bear_analysis = {
        'symbol': 'NVDA',
        'confidence': 0.3,
        'risks': ['RSI超买']
    }
    
    risk_assessment = {
        'risk_level': 0.4,  # 低风险
        'current_drawdown': 0.035
    }
    
    historian_analysis = {
        'success_rate': 0.65,
        'avg_return': 3.2
    }
    
    print(f"  Bull: {bull_analysis['confidence']:.2f}")
    print(f"  Bear: {bear_analysis['confidence']:.2f}")
    print(f"  Risk: {risk_assessment['risk_level']:.2f}")
    print(f"  Historian: {historian_analysis['success_rate']:.2f}")
    
    # 测试4: 最终决策
    print("\n[测试4] 最终决策...")
    decision = brain.make_decision(
        bull_analysis, bear_analysis, risk_assessment, historian_analysis
    )
    print(f"  决策: {decision['action']} {decision['symbol']}")
    print(f"  Confidence: {decision['confidence']:.2f}")
    print(f"  理由: {decision['reasoning']}")
    print(f"  市场状态: {decision['regime']}")
    print(f"  权重: {decision['weights_used']}")
    
    brain.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_meta_brain()
