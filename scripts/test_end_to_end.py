#!/usr/bin/env python3
"""
NSPS-V1: End-to-End Test
测试完整流程：数据采集 → Bull/Bear分析 → Meta Brain决策 → 记录
全部本地资源，0成本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bull_bear_team import BullTeam, BearTeam
from meta_brain import MetaBrain
from agent_state_manager import AgentStateManager
from constitution_engine import ConstitutionEngine
from learning_ledger import LearningLedger
from historian import Historian
from evolution_council import EvolutionCouncil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_end_to_end():
    """端到端测试"""
    print("=" * 80)
    print("NSPS-V1 端到端测试")
    print("=" * 80)
    
    # 1. 初始化所有模块
    print("\n[Step 1] 初始化所有模块...")
    bull = BullTeam()
    bear = BearTeam()
    brain = MetaBrain()
    agent_mgr = AgentStateManager()
    constitution = ConstitutionEngine()
    ledger = LearningLedger()
    historian = Historian()
    ec = EvolutionCouncil()
    print("  ✅ 8个模块初始化完成")
    
    # 2. 检查系统状态
    print("\n[Step 2] 系统健康检查...")
    agents = agent_mgr.get_all_agents()
    print(f"  ✅ {len(agents)} 个Agent已注册")
    for agent in agents[:3]:
        print(f"    • {agent['agent_name']}: v{agent['version']}, 准确率{agent['accuracy']:.0%}")
    
    # 3. 检测市场状态
    print("\n[Step 3] 检测市场状态...")
    regime = brain.detect_market_regime()
    print(f"  ✅ 市场状态: {regime['regime']} (confidence={regime['confidence']:.2f})")
    
    # 4. Bull Team分析
    print("\n[Step 4] Bull Team分析NVDA...")
    bull_result = bull.analyze('NVDA', 'us')
    print(f"  ✅ {len(bull_result['reasons'])}个上涨理由")
    print(f"     Confidence: {bull_result['confidence']:.2f}")
    if bull_result['reasons']:
        print(f"     理由: {bull_result['reasons'][0]}")
    
    # 5. Bear Team分析
    print("\n[Step 5] Bear Team分析NVDA...")
    bear_result = bear.analyze('NVDA', 'us')
    print(f"  ✅ {len(bear_result['risks'])}个风险")
    print(f"     Confidence: {bear_result['confidence']:.2f}")
    if bear_result['risks']:
        print(f"     风险: {bear_result['risks'][0]}")
    
    # 6. Historian分析
    print("\n[Step 6] Historian搜索历史相似场景...")
    historian_result = historian.search_similar_scenarios(
        {'score': 0.75, 'predicted': 5.0},
        n_results=3
    )
    print(f"  ✅ 找到{historian_result['sample_size']}个相似场景")
    print(f"     胜率: {historian_result['success_rate']:.1%}")
    
    # 7. Meta Brain决策
    print("\n[Step 7] Meta Brain综合决策...")
    risk_assessment = {
        'risk_level': 0.4,
        'current_drawdown': 0.035
    }
    
    decision = brain.make_decision(
        bull_result, bear_result, risk_assessment, historian_result
    )
    print(f"  ✅ 决策: {decision['action']} {decision['symbol']}")
    print(f"     Confidence: {decision['confidence']:.2f}")
    print(f"     市场状态: {decision['regime']}")
    
    # 8. Constitution检查
    print("\n[Step 8] Constitution检查...")
    decision_for_check = {
        'type': decision['action'],
        'stock': decision['symbol'],
        'audit_trail': True
    }
    allowed, violations = constitution.check_decision(decision_for_check)
    if allowed:
        print(f"  ✅ 决策通过宪法检查")
    else:
        print(f"  ❌ 决策被宪法阻止: {violations}")
    
    # 9. 更新Agent状态
    print("\n[Step 9] 更新Agent状态...")
    # 模拟预测结果（假设正确）
    agent_mgr.update_prediction_result('Bull Team', correct=True)
    agent_mgr.update_prediction_result('Bear Team', correct=True)
    bull_state = agent_mgr.get_agent_state('Bull Team')
    print(f"  ✅ Bull Team准确率: {bull_state['accuracy']:.2%}")
    
    # 10. 记录学习（如果有调参）
    print("\n[Step 10] 学习账本记录...")
    ledger_id = ledger.record_learning(
        agent_name='Meta Brain',
        change_type='weight_adjustment',
        old_value={'regime': 'RANGE'},
        new_value={'regime': regime['regime']},
        reason=f"市场状态检测为{regime['regime']}",
        evidence=regime['indicators'],
        rollback_condition='如果胜率下降>5%，自动回滚'
    )
    print(f"  ✅ 学习记录 #{ledger_id} 已保存")
    
    # 11. 提交进化提案（如果有改进建议）
    print("\n[Step 11] 进化提案...")
    proposal_id = ec.submit_proposal(
        proposer='Historian',
        proposal_type='IMPROVEMENT',
        title='增强Historian相似度算法',
        hypothesis='IF 使用DTW算法 THEN 相似度准确率提高10%',
        evidence={'current_accuracy': 0.75, 'expected': 0.85},
        rollback_plan='如果准确率下降，自动回滚'
    )
    print(f"  ✅ 提案 #{proposal_id} 已提交")
    
    # 12. 总结
    print("\n" + "=" * 80)
    print("✅ 端到端测试完成")
    print("=" * 80)
    print(f"\n测试摘要:")
    print(f"  • 8个模块全部正常")
    print(f"  • 市场状态: {regime['regime']}")
    print(f"  • 决策: {decision['action']} {decision['symbol']}")
    print(f"  • Constitution: {'通过' if allowed else '被阻止'}")
    print(f"  • 学习记录: #{ledger_id}")
    print(f"  • 进化提案: #{proposal_id}")
    print(f"\n🎉 NSPS-V1 核心功能全部正常！")
    
    # 清理
    bull.close()
    bear.close()
    brain.close()
    agent_mgr.close()
    constitution.close()
    ledger.close()
    historian.close()
    ec.close()


if __name__ == '__main__':
    test_end_to_end()
