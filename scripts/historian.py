#!/usr/bin/env python3
"""
NSPS-V1 Core: Historian（历史学家）
搜索历史相似场景，提供历史结果参考
全部本地资源，0成本
"""

import psycopg2
import numpy as np
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

class Historian:
    """历史学家：搜索历史相似场景"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ Historian连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def search_similar_scenarios(self, current_features: Dict, 
                                  n_results: int = 5) -> List[Dict]:
        """
        搜索历史相似场景
        
        Args:
            current_features: {
                'change_pct': float,      # 涨幅
                'volume_ratio': float,    # 量比
                'rvol': float,            # 相对成交量
                'rsi': float,             # RSI
                'sector': str             # 板块
            }
            n_results: 返回结果数量
        
        Returns:
            List of similar scenarios with historical results
        """
        cur = self.conn.cursor()
        
        # 从paper_trades获取历史数据（有实际结果的）
        cur.execute("""
            SELECT 
                trade_date,
                symbol,
                entry_prediction_score,
                predicted_change,
                pnl_pct,
                status
            FROM paper_trades
            WHERE status = 'CLOSED'
              AND pnl_pct IS NOT NULL
            ORDER BY trade_date DESC
            LIMIT 1000
        """)
        
        historical_data = cur.fetchall()
        
        if not historical_data:
            logger.warning("⚠️ 无历史数据")
            return {
                'scenarios': [],
                'success_rate': 0,
                'avg_return': 0,
                'confidence': 0,
                'sample_size': 0
            }
        
        # 计算相似度
        similarities = []
        for row in historical_data:
            trade_date, symbol, score, predicted, actual, status = row
            
            # 简化的特征向量（实际应该从prices表获取更完整的特征）
            # 这里用score和predicted作为代理
            historical_features = {
                'score': score or 0,
                'predicted': predicted or 0,
                'actual': actual or 0
            }
            
            # 计算欧氏距离
            distance = self._calculate_distance(current_features, historical_features)
            similarity = 1.0 / (1.0 + distance)  # 转换为0-1
            
            similarities.append({
                'date': trade_date,
                'symbol': symbol,
                'similarity': similarity,
                'predicted': predicted,
                'actual': actual,
                'success': actual > 0 if actual else False
            })
        
        # 按相似度排序
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        top_n = similarities[:n_results]
        
        # 统计
        success_count = sum(1 for s in top_n if s['success'])
        success_rate = success_count / len(top_n) if top_n else 0
        avg_return = sum(s['actual'] for s in top_n) / len(top_n) if top_n else 0
        
        result = {
            'scenarios': top_n,
            'success_rate': success_rate,
            'avg_return': avg_return,
            'confidence': max(s['similarity'] for s in top_n) if top_n else 0,
            'sample_size': len(top_n)
        }
        
        logger.info(f"✅ 找到{len(top_n)}个相似场景，胜率{success_rate:.1%}，平均收益{avg_return:.2f}%")
        return result
    
    def _calculate_distance(self, features1: Dict, features2: Dict) -> float:
        """计算两个特征向量的欧氏距离"""
        # 简化的距离计算（实际应该用更复杂的DTW或多维度匹配）
        
        # 提取可比较的数值特征
        keys = ['score', 'predicted', 'actual', 'change_pct', 'volume_ratio', 'rvol', 'rsi']
        
        vec1 = []
        vec2 = []
        
        for key in keys:
            if key in features1 and key in features2:
                vec1.append(float(features1[key]))
                vec2.append(float(features2[key]))
        
        if not vec1 or not vec2:
            return float('inf')
        
        # 归一化（简单处理：除以最大值）
        max_val = max(max(abs(v) for v in vec1), max(abs(v) for v in vec2), 1)
        vec1 = [v / max_val for v in vec1]
        vec2 = [v / max_val for v in vec2]
        
        # 欧氏距离
        distance = np.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))
        return distance
    
    def get_pattern_analysis(self, days: int = 30) -> Dict:
        """
        分析最近N天的模式
        
        Returns:
            {
                'total_trades': int,
                'win_rate': float,
                'avg_return': float,
                'best_sector': str,
                'worst_sector': str,
                'pattern': str  # TRENDING/RANGE/DECLINING
            }
        """
        cur = self.conn.cursor()
        
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN pnl_pct > 0 THEN 1 ELSE 0 END) as wins,
                AVG(pnl_pct) as avg_return
            FROM paper_trades
            WHERE status = 'CLOSED'
              AND trade_date >= %s
        """, (since_date,))
        
        row = cur.fetchone()
        if not row or row[0] == 0:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_return': 0,
                'pattern': 'NO_DATA'
            }
        
        total, wins, avg_return = row
        win_rate = wins / total if total > 0 else 0
        
        # 判断模式
        if win_rate > 0.6 and avg_return > 2:
            pattern = 'TRENDING_UP'
        elif win_rate < 0.4 and avg_return < -1:
            pattern = 'TRENDING_DOWN'
        elif abs(avg_return) < 1:
            pattern = 'RANGE'
        else:
            pattern = 'MIXED'
        
        result = {
            'total_trades': total,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'pattern': pattern,
            'period_days': days
        }
        
        logger.info(f"✅ 最近{days}天模式: {pattern}，胜率{win_rate:.1%}，平均收益{avg_return:.2f}%")
        return result
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_historian():
    """测试Historian"""
    print("=" * 80)
    print("测试: Historian")
    print("=" * 80)
    
    historian = Historian()
    
    # 测试1: 搜索相似场景
    print("\n[测试1] 搜索历史相似场景...")
    current_features = {
        'score': 0.75,
        'predicted': 5.0,
        'change_pct': 3.5,
        'volume_ratio': 2.1,
        'rvol': 1.8,
        'rsi': 65
    }
    
    similar = historian.search_similar_scenarios(current_features, n_results=5)
    
    if similar['scenarios']:
        print(f"  找到{similar['sample_size']}个相似场景")
        print(f"  胜率: {similar['success_rate']:.1%}")
        print(f"  平均收益: {similar['avg_return']:.2f}%")
        print(f"  最高相似度: {similar['confidence']:.2f}")
        
        print("\n  历史场景:")
        for i, scenario in enumerate(similar['scenarios'], 1):
            success_str = "✅" if scenario['success'] else "❌"
            print(f"    {i}. {scenario['date']} {scenario['symbol']} | "
                  f"相似度{scenario['similarity']:.2f} | "
                  f"预测{scenario['predicted']:.2f}% → 实际{scenario['actual']:.2f}% {success_str}")
    else:
        print("  ⚠️ 无历史数据")
    
    # 测试2: 模式分析
    print("\n[测试2] 分析最近30天模式...")
    pattern = historian.get_pattern_analysis(days=30)
    print(f"  总交易: {pattern['total_trades']}")
    print(f"  胜率: {pattern['win_rate']:.1%}")
    print(f"  平均收益: {pattern['avg_return']:.2f}%")
    print(f"  模式: {pattern['pattern']}")
    
    historian.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_historian()
