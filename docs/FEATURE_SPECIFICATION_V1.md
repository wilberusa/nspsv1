# NSPS Feature Specification v1.0

> **每个Agent的功能规格：输入、输出、KPI、约束**

Version: 1.0 | Created: 2026-07-22 | Status: Draft

---

## 目录

1. [Bull Team](#1-bull-team)
2. [Bear Team](#2-bear-team)
3. [Risk Team](#3-risk-team)
4. [Testing Team](#4-testing-team)
5. [Historian](#5-historian)
6. [Critic Agent](#6-critic-agent)
7. [Auditor Agent](#7-auditor-agent)
8. [Coach Agent](#8-coach-agent)
9. [Meta Brain](#9-meta-brain)
10. [Evolution Council](#10-evolution-council)

---

## 1. Bull Team

### 功能
只负责找上涨理由。

### 输入
- 市场数据（价格、成交量、资金流）
- 新闻（MX-Search API）
- 板块效应（sector_effect.py）

### 输出
```yaml
bull_reasoning:
  stock: "NVDA"
  reasons:
    - "AI板块资金流入+15%"
    - "新闻：新产品发布，预期+10%"
    - "板块效应：5只股票异动"
  confidence: 0.85
  evidence:
    - capital_flow: "+$50M"
    - news_sentiment: 0.9
    - sector_strength: "strong"
```

### KPI
- 准确率：预测上涨的股票中，实际上涨的比例
- 目标：>60%

### 约束
- 只找上涨理由，不找反例
- 必须提供Evidence（数据支撑）
- Confidence必须基于历史准确率校准

### 实现方式
- Hermes 70B（本地） → 不花钱
- Python脚本 → 数据处理

---

## 2. Bear Team

### 功能
只负责找反例和风险。

### 输入
- 市场数据（价格、成交量、资金流）
- 新闻（MX-Search API）
- 历史失败案例（TimescaleDB）

### 输出
```yaml
bear_reasoning:
  stock: "NVDA"
  risks:
    - "RSI=78，超买"
    - "主力资金流出-$20M"
    - "历史相似场景：2024-03-15，失败率80%"
  confidence: 0.75
  evidence:
    - rsi: 78
    - capital_flow: "-$20M"
    - historical_similarity: 0.92
```

### KPI
- 准确率：预测下跌的股票中，实际下跌的比例
- 目标：>60%

### 约束
- 只找反例和风险，不找上涨理由
- 必须提供Evidence（数据支撑）
- Confidence必须基于历史准确率校准

### 实现方式
- Hermes 70B（本地） → 不花钱
- Python脚本 → 数据处理

---

## 3. Risk Team

### 功能
负责仓位、回撤、极端事件。

### 输入
- 当前持仓（paper_trades表）
- 市场波动率（VIX）
- 最大回撤限制（Constitution Rule 1: 10%）

### 输出
```yaml
risk_assessment:
  current_drawdown: 3.5%
  max_allowed_drawdown: 10%
  remaining_risk_budget: 6.5%
  position_size_recommendation:
    stock: "NVDA"
    recommended_size: "$2000"
    reason: "当前回撤3.5%，还有6.5%预算"
  extreme_event_warning:
    - "VIX>30，建议减仓"
    - "连续3天亏损，建议暂停交易"
```

### KPI
- 回撤控制：实际回撤 < 10%
- 极端事件预警准确率：>80%

### 约束
- 永远不能超过Constitution Rule 1（最大回撤10%）
- 必须实时监控，盘中每5分钟更新

### 实现方式
- Python脚本 → 实时计算
- TimescaleDB → 存储历史回撤数据

---

## 4. Testing Team

### 功能
四层测试：UT/SIT/RT → Backtest → Paper Trading → Production

### 输入
- 新Agent/策略代码
- 历史数据（TimescaleDB）
- 测试用例

### 输出
```yaml
testing_result:
  layer_1_ut_sit_rt:
    status: "PASS"
    test_coverage: 95%
    failed_tests: 0
  layer_2_backtest:
    status: "PASS"
    win_rate: 58%
    max_drawdown: 7.2%
    sharpe_ratio: 1.5
  layer_3_paper_trading:
    status: "IN_PROGRESS"
    days_completed: 15
    current_win_rate: 60%
  layer_4_production:
    status: "PENDING"
```

### KPI
- 测试覆盖率：>90%
- 回测胜率：>50%
- Paper Trading胜率：>55%

### 约束
- 任何新Agent必须通过四层测试
- 任何一层Fail → 回到上一层修改
- 所有测试结果记录到Testing Ledger

### 实现方式
- pytest → UT/SIT/RT
- Python脚本 → Backtest
- paper_trade_engine.py → Paper Trading
- TimescaleDB → 存储测试结果

---

## 5. Historian

### 功能
搜索历史相似场景，提供历史结果参考。

### 输入
- 当前市场状态（板块、涨幅、Volume、RVOL）
- 历史数据（TimescaleDB，10年+）

### 输出
```yaml
historian_analysis:
  current_scenario:
    sector: "AI"
    change_pct: 5.2
    volume_ratio: 2.1
    rvol: 1.8
  similar_historical_scenarios:
    - date: "2024-03-15"
      similarity: 0.92
      result: "+15%"
      success: true
    - date: "2022-07-20"
      similarity: 0.87
      result: "-8%"
      success: false
  analysis:
    success_rate: 50%
    average_return: 3.5%
    confidence: 0.75
    recommendation: "更接近成功场景，建议参与"
```

### KPI
- 相似度计算准确率：>85%
- 历史预测准确率：>60%

### 约束
- 必须提供相似度算法（DTW + 多维度匹配）
- 必须提供历史证据（Prediction Journal）
- 不能替代当前分析，只能作为参考

### 实现方式
- Python脚本 → DTW算法
- TimescaleDB → 历史数据查询
- pandas → 相似度计算

---

## 6. Critic Agent

### 功能
每次Decision后自动审查：为什么？最大风险？最大反例？

### 输入
- 任何Decision（Bull/Bear/Risk的输出）

### 输出
```yaml
critic_review:
  decision: "Buy NVDA"
  questions:
    why: "AI板块资金流入+15%，新闻利好"
    biggest_risk: "RSI=78，超买"
    biggest_counter_example: "2024-03-15相似场景失败"
  verdict: "PASS"  # or "FAIL"
  reasoning: "逻辑完整，风险已识别，反例已考虑"
```

### KPI
- 审查覆盖率：100%（每个Decision都要审查）
- 发现问题率：>20%（至少20%的Decision有问题）

### 约束
- 必须问三个问题：为什么？最大风险？最大反例？
- 如果回答不了 → Decision不通过
- 审查结果记录到aiic_decisions表

### 实现方式
- Hermes 70B（本地） → 不花钱
- Python脚本 → 逻辑检查

---

## 7. Auditor Agent

### 功能
每日审计：Prediction → Reality → Difference → Reason → Who Responsible

### 输入
- 每日预测（aiic_decisions表）
- 每日实际结果（paper_trades表）

### 输出
```yaml
audit_report:
  date: "2026-07-22"
  predictions:
    - stock: "NVDA"
      predicted: "+5%"
      actual: "+3%"
      difference: "-2%"
      reason: "大盘下跌拖累"
      responsible: "Risk Team（未预警大盘风险）"
  summary:
    total_predictions: 5
    correct: 3
    incorrect: 2
    accuracy: 60%
  recommendations:
    - "Risk Team应增加大盘风险预警"
    - "Bear Team应更关注宏观因素"
```

### KPI
- 审计覆盖率：100%
- 问题识别率：>90%

### 约束
- 每日收盘后自动执行
- 审计结果记录到learning_ledger表
- 严重问题立即通知Hao

### 实现方式
- Python脚本 → 对比分析
- TimescaleDB → 查询预测和实际结果

---

## 8. Coach Agent

### 功能
每天分析每个Agent表现，给出改进建议（不直接执行）。

### 输入
- 每个Agent的KPI（agent_states表）
- 历史表现（learning_ledger表）

### 输出
```yaml
coach_recommendations:
  agent: "News Agent"
  current_accuracy: 87%
  recent_performance:
    last_10: 70%
    last_100: 88%
  issue: "最近10次预测准确率下降到70%"
  recommendation:
    - "减少Macro类预测权重"
    - "增加AI/Tech类预测权重"
    - "建议回滚到version 2.1.5"
  priority: "HIGH"
```

### KPI
- 建议采纳率：>50%
- 建议有效性：采纳后准确率提升>5%

### 约束
- 只给建议，不直接执行
- 建议必须基于数据（不是猜测）
- 建议记录到evolution_proposals表

### 实现方式
- Hermes 70B（本地） → 不花钱
- Python脚本 → 数据分析

---

## 9. Meta Brain

### 功能
Market Regime Detection + 动态调整Agent权重 + 最终决策

### 输入
- 市场数据（价格、成交量、波动率）
- 每个Agent的输出（Bull/Bear/Risk/Historian）

### 输出
```yaml
meta_brain_decision:
  market_regime: "Trend"  # Trend/Range/Event/Risk-off
  agent_weights:
    bull: 0.4
    bear: 0.2
    risk: 0.2
    historian: 0.2
  final_decision:
    action: "Buy"
    stock: "NVDA"
    position_size: "$2000"
    confidence: 0.85
    reasoning: "Trend市场，Bull Team权重高，历史相似场景成功率80%"
```

### KPI
- 市场状态识别准确率：>75%
- 最终决策准确率：>55%

### 约束
- 必须遵守Constitution（特别是Rule 1: 最大回撤10%）
- 必须记录决策到aiic_decisions表
- 必须经过Critic Agent审查

### 实现方式
- Python脚本 → Market Regime Detection
- Hermes 70B（本地） → 综合决策
- TimescaleDB → 存储决策

---

## 10. Evolution Council (EC)

### 功能
审批Agent提出的进化建议（Proposal）

### 输入
- evolution_proposals表（Agent提出的建议）
- 历史数据（TimescaleDB）
- 每个Agent的KPI（agent_states表）

### 输出
```yaml
ec_decision:
  proposal_id: 42
  proposal: "增加Option Agent"
  proposer: "News Agent"
  hypothesis: "Option Flow可能提高Leader Accuracy 5%"
  ec_votes:
    meta_brain: "APPROVE"
    historian: "APPROVE"
    auditor: "APPROVE"
  ec_reasoning: "历史数据显示Option Flow与股价相关性0.7，建议测试"
  testing_requirement:
    - "Layer 1: UT/SIT/RT"
    - "Layer 2: Backtest 1年"
    - "Layer 3: Paper Trading 30天"
  rollback_plan: "如果Paper Trading胜率<50%，自动拒绝"
```

### KPI
- 审批通过率：>30%（不能太低，也不能太高）
- 审批后成功率：>60%（通过的Proposal最终成功上线）

### 约束
- 必须有至少3票赞成才能通过
- 必须提供Rollback Plan
- 必须记录到evolution_proposals表
- Hao有最终否决权

### 实现方式
- Hermes 70B（本地） → 评估Proposal
- Python脚本 → 投票逻辑
- TimescaleDB → 存储决策

---

## 附录：Agent间通信接口

### 数据格式
所有Agent输出必须是YAML格式，包含：
- `confidence`: 0-1
- `evidence`: 数据支撑
- `reasoning`: 逻辑说明

### 通信方式
- Agent之间通过TimescaleDB传递数据
- 不直接调用，避免耦合
- 每个Agent独立运行，独立记录

### 约束
- 所有通信必须记录到aiic_decisions表
- 所有通信必须可审计
- 所有通信必须遵守Constitution

---

*Document Version: 1.0 | Last Updated: 2026-07-22 | Author: Alca | Reviewer: Pending (Hao)*
