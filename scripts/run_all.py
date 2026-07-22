#!/usr/bin/env python3
"""
NSPS-V1: Run All — 一键运行所有模块
全部本地资源，0成本
"""

import subprocess
import sys
import os
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

MODULES = [
    ('self_monitoring.py', '系统健康检查'),
    ('agent_state_manager.py', 'Agent状态管理'),
    ('constitution_engine.py', '宪法检查'),
    ('bull_bear_team.py', 'Bull/Bear分析'),
    ('historian.py', '历史相似搜索'),
    ('meta_brain.py', 'Meta Brain决策'),
    ('self_evaluation.py', '自我评估'),
    ('self_calibration.py', 'Confidence校准'),
    ('self_improvement.py', '自我优化'),
    ('agents_suite.py', 'Critic+Auditor+Coach+Risk'),
    ('daily_pnl_report.py', '每日盈亏报告'),
]


def run_all():
    print("=" * 80)
    print(f"NSPS-V1 全模块运行 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S PT')}")
    print("=" * 80)
    
    results = []
    
    for script, desc in MODULES:
        path = os.path.join(SCRIPTS_DIR, script)
        if not os.path.exists(path):
            print(f"\n❌ {desc}: {script} 不存在")
            results.append((script, desc, 'MISSING'))
            continue
        
        print(f"\n▶ {desc} ({script})...")
        try:
            result = subprocess.run(
                [sys.executable, path],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                print(f"  ✅ 通过")
                results.append((script, desc, 'PASS'))
            else:
                print(f"  ❌ 失败: {result.stderr[:200]}")
                results.append((script, desc, 'FAIL'))
        except subprocess.TimeoutExpired:
            print(f"  ⏰ 超时")
            results.append((script, desc, 'TIMEOUT'))
        except Exception as e:
            print(f"  ❌ 异常: {e}")
            results.append((script, desc, 'ERROR'))
    
    # 汇总
    print("\n" + "=" * 80)
    print("汇总")
    print("=" * 80)
    
    passed = sum(1 for _, _, s in results if s == 'PASS')
    total = len(results)
    
    for script, desc, status in results:
        icon = '✅' if status == 'PASS' else '❌'
        print(f"  {icon} {desc:20s} | {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 NSPS-V1 全部模块运行正常！")
    else:
        print(f"\n⚠️ {total - passed}个模块失败，请检查日志")
    
    return passed == total


if __name__ == '__main__':
    success = run_all()
    sys.exit(0 if success else 1)
