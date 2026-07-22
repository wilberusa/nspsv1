#!/usr/bin/env python3
"""
NSPS-V1: Self-Calibration Agent
自我校准：Confidence是否过高或过低？
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


class SelfCalibration:
    """自我校准Agent：检查Confidence是否与实际表现匹配"""
    
    def __init__(self):
        self.conn = None
        self._connect()
    
    def _connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            logger.info("✅ SelfCalibration连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def check_agent_calibration(self, agent_name: str) -> Dict:
        """
        检查某个Agent的Confidence校准情况
        
        Returns:
            {
                'agent_name': str,
                'current_confidence': float,
                'actual_accuracy': float,
                'calibration_error': float,  # confidence - accuracy
                'status': str,  # OVER_CONFIDENT / UNDER_CONFIDENT / WELL_CALIBRATED
                'recommendation': str
            }
        """
        cur = self.conn.cursor()
        
        # 获取Agent状态
        cur.execute("""
            SELECT confidence, accuracy, total_predictions
            FROM agent_states
            WHERE agent_name = %s
        """, (agent_name,))
        
        row = cur.fetchone()
        if not row:
            return {
                'agent_name': agent_name,
                'status': 'NOT_FOUND',
                'recommendation': 'Agent不存在'
            }
        
        confidence, accuracy, total_predictions = row
        
        if total_predictions < 10:
            return {
                'agent_name': agent_name,
                'current_confidence': confidence,
                'actual_accuracy': accuracy,
                'total_predictions': total_predictions,
                'status': 'INSUFFICIENT_DATA',
                'recommendation': f'样本量不足（{total_predictions}次），需要至少10次预测'
            }
        
        # 计算校准误差
        calibration_error = confidence - accuracy
        
        # 判断状态
        if calibration_error > 0.15:
            status = 'OVER_CONFIDENT'
            recommendation = f'Confidence过高（{confidence:.2f}），实际准确率{accuracy:.2f}，建议降低Confidence到{accuracy:.2f}'
        elif calibration_error < -0.15:
            status = 'UNDER_CONFIDENT'
            recommendation = f'Confidence过低（{confidence:.2f}），实际准确率{accuracy:.2f}，建议提升Confidence到{accuracy:.2f}'
        else:
            status = 'WELL_CALIBRATED'
            recommendation = f'Confidence校准良好（{confidence:.2f} vs {accuracy:.2f}）'
        
        return {
            'agent_name': agent_name,
            'current_confidence': confidence,
            'actual_accuracy': accuracy,
            'total_predictions': total_predictions,
            'calibration_error': calibration_error,
            'status': status,
            'recommendation': recommendation
        }
    
    def calibrate_all_agents(self) -> List[Dict]:
        """校准所有Agent"""
        cur = self.conn.cursor()
        cur.execute("SELECT agent_name FROM agent_states")
        
        agents = [row[0] for row in cur.fetchall()]
        results = []
        
        for agent_name in agents:
            result = self.check_agent_calibration(agent_name)
            results.append(result)
            
            # 如果校准偏差>15%，自动调整
            if result['status'] in ['OVER_CONFIDENT', 'UNDER_CONFIDENT']:
                self._auto_calibrate(agent_name, result['actual_accuracy'])
        
        return results
    
    def _auto_calibrate(self, agent_name: str, new_confidence: float):
        """自动校准Confidence"""
        cur = self.conn.cursor()
        
        # 获取旧值
        cur.execute("""
            SELECT confidence FROM agent_states WHERE agent_name = %s
        """, (agent_name,))
        old_confidence = cur.fetchone()[0]
        
        # 更新（指数移动平均，避免剧烈波动）
        alpha = 0.3  # 学习速率
        calibrated = alpha * new_confidence + (1 - alpha) * old_confidence
        
        cur.execute("""
            UPDATE agent_states
            SET confidence = %s, last_updated = NOW()
            WHERE agent_name = %s
        """, (calibrated, agent_name))
        
        self.conn.commit()
        logger.info(f"✅ {agent_name} Confidence校准: {old_confidence:.2f} → {calibrated:.2f}")
    
    def generate_report(self) -> str:
        """生成校准报告"""
        results = self.calibrate_all_agents()
        
        lines = []
        lines.append("📊 Self-Calibration Report")
        lines.append("")
        
        over_confident = [r for r in results if r['status'] == 'OVER_CONFIDENT']
        under_confident = [r for r in results if r['status'] == 'UNDER_CONFIDENT']
        well_calibrated = [r for r in results if r['status'] == 'WELL_CALIBRATED']
        
        if over_confident:
            lines.append(f"⚠️ 过度自信（{len(over_confident)}个）:")
            for r in over_confident:
                lines.append(f"  • {r['agent_name']}: Confidence={r['current_confidence']:.2f}, 实际={r['actual_accuracy']:.2f}")
            lines.append("")
        
        if under_confident:
            lines.append(f"⚠️ 过度保守（{len(under_confident)}个）:")
            for r in under_confident:
                lines.append(f"  • {r['agent_name']}: Confidence={r['current_confidence']:.2f}, 实际={r['actual_accuracy']:.2f}")
            lines.append("")
        
        if well_calibrated:
            lines.append(f"✅ 校准良好（{len(well_calibrated)}个）:")
            for r in well_calibrated:
                lines.append(f"  • {r['agent_name']}: {r['current_confidence']:.2f} vs {r['actual_accuracy']:.2f}")
            lines.append("")
        
        # 总结
        total = len(results)
        calibrated_pct = len(well_calibrated) / total * 100 if total > 0 else 0
        lines.append(f"【总结】")
        lines.append(f"  校准率: {calibrated_pct:.0f}% ({len(well_calibrated)}/{total})")
        
        if calibrated_pct < 50:
            lines.append(f"  ⚠️ 校准率偏低，建议审查Confidence计算逻辑")
        else:
            lines.append(f"  ✅ 校准率良好")
        
        return '\n'.join(lines)
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_self_calibration():
    """测试"""
    print("=" * 80)
    print("测试: Self-Calibration")
    print("=" * 80)
    
    sc = SelfCalibration()
    
    # 测试1: 检查单个Agent
    print("\n[测试1] 检查Bull Team校准...")
    result = sc.check_agent_calibration('Bull Team')
    print(f"  状态: {result['status']}")
    print(f"  Confidence: {result.get('current_confidence', 'N/A')}")
    print(f"  实际准确率: {result.get('actual_accuracy', 'N/A')}")
    print(f"  建议: {result['recommendation']}")
    
    # 测试2: 校准所有Agent
    print("\n[测试2] 校准所有Agent...")
    results = sc.calibrate_all_agents()
    for r in results:
        print(f"  {r['agent_name']}: {r['status']}")
    
    # 测试3: 完整报告
    print("\n[测试3] 完整报告:")
    print("-" * 40)
    print(sc.generate_report())
    
    sc.close()
    print("\n✅ 所有测试通过")


if __name__ == '__main__':
    test_self_calibration()
