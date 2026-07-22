# NSPS Architecture Specification v1.0

> **NSPS不是一个预测市场的AI，而是一个能够持续提升自身认知能力的市场智能体（Market Intelligence System，MIS）。**

Version: 1.0 | Created: 2026-07-22 | Status: Draft → Pending Hao Approval

---

## 目录

1. [核心设计原则（Principles）](#1-核心设计原则)
2. [Canonical Data Model](#2-canonical-data-model)
3. [Agent 生命周期](#3-agent-生命周期)
4. [Memory Architecture](#4-memory-architecture)
5. [AI Investment Committee (AIIC)](#5-ai-investment-committee)
6. [Learning & Evolution Framework](#6-learning--evolution-framework)
7. [Testing & Deployment Pipeline](#7-testing--deployment-pipeline)
8. [Constitution（不可违反的规则）](#8-constitution)
9. [Roadmap](#9-roadmap)
10. [KPI 与 Success Metrics](#10-kpi-与-success-metrics)

---

## 1. 核心设计原则

### 1.1 最高原则：Controlled Evolution（受控进化）

> **任何能够自动改变系统的能力，都必须比产生这个改变的能力受到更严格的约束。**

- Agent 可以提出建议（自由度：高）
- Meta Brain 可以协调（自由度：中）
- Evolution Council 可以审批（自由度：低）
- Testing Team 可以验证（自由度：低）
- Constitution 可以否决（自由度：零）

### 1.2 系统成长 > LLM成长

不是LLM在成长，是System在成长。

```
Observe → Think → Predict → Execute + FEEDBACK → Measure → Learn → Improve + UPDATE → Observe ...
```

LLM可以换（Hermes → Qwen → GPT-5），但系统的认知能力持续积累。

### 1.3 两个时代的分水岭

旧时代：`LLM → Prompt → Output`
新时代：`Data → Knowledge → Reasoning → Decision → Learning → Evolution`

### 1.4 资源优先级

| 优先级 | 资源 | 用途 | 成本 |
|--------|------|------|------|
| P0 | Python脚本 | 数据处理、统计、回测、参数调整 | 免费 |
| P0 | Hermes 70B（本地） | 分析、诊断、反思、Critic、Coach | 免费 |
| P0 | TimescaleDB | 存储所有状态、KPI、交易记录 | 免费 |
| P1 | Qwen（云端） | 仅当本地模型置信度<70%时 | 付费 |

### 1.5 铁律

1. 多用Python和本地资源，少用付费quota
2. 只有本地模型置信度<70%时才调用云端
3. 每个Agent的反思/诊断/教练 → Hermes 70B（本地）
4. 数据处理/统计/回测/参数调整 → Python脚本（本地）
5. 所有状态存TimescaleDB（不丢）

---

## 2. Canonical Data Model

### 2.1 核心表结构

```sql
-- 1. paper_trades（已存在）
-- 记录每一笔paper trade的入场、出场、盈亏
paper_trades (
    id, trade_date, symbol, name, market,
    entry_price, entry_time, entry_prediction_score,
    exit_price, exit_time, exit_reason,
    pnl, pnl_pct, hold_hours, status,
    actual_peak, actual_low
)

-- 2. agent_states（新建）
-- 每个Agent的实时状态
agent_states (
    id, agent_name, version,
    accuracy, confidence, last_100_accuracy,
    strength_tags, weakness_tags,
    learning_rate, total_predictions, correct_predictions,
    last_updated
)

-- 3. learning_ledger（新建）
-- 所有学习/调参记录，可审计、可回滚
learning_ledger (
    id, time, agent_name, change_type,
    old_value, new_value,
    reason, evidence, backtest_result,
    actual_result, rollback_triggered,
    approved_by, approved_time
)

-- 4. evolution_proposals（新建）
-- Agent提出的进化建议
evolution_proposals (
    id, time, proposer_agent, proposal_type,
    hypothesis, expected_impact, evidence,
    ec_status, ec_votes, ec_reasoning,
    testing_result, deploy_status,
    rollback_plan
)

-- 5. aiic_decisions（新建）
-- AIIC委员会的每次决策记录
aiic_decisions (
    id, time, decision_type,
    bull_reasoning, bear_reasoning, risk_assessment,
    historian_similarity, historian_reference,
    final_decision, confidence,
    critic_review, audit_result
)

-- 6. constitution_violations（新建）
-- 宪法违规记录
constitution_violations (
    id, time, rule_number, violation_description,
    detected_by, severity, action_taken, resolved
)
```

### 2.2 数据流

```
TimescaleDB (prices, prices_cn) → 数据层
    ↓
agent_states → Agent状态层
    ↓
aiic_decisions → 决策层
    ↓
paper_trades → 交易层
    ↓
learning_ledger → 学习层（可审计、可回滚）
    ↓
evolution_proposals → 进化层（受控）
    ↓
constitution_violations → 宪法层（最高约束）
```

---

## 3. Agent 生命周期

### 3.1 Agent定义（从工具到生命体）

旧模式：`Input → Thinking → Output`（工具）

新模式：
```
Input → Thinking → Decision → Evidence → Confidence
    → Result → Reflection → Improve → Output
```

### 3.2 Agent状态模型

```yaml
Agent:
  name: "News Agent"
  version: "2.1.8"
  accuracy: 87%
  confidence: 0.91
  last_100: 88%
  strength: ["AI", "Tech"]
  weakness: ["Macro", "Energy"]
  learning_rate: 0.03
  total_predictions: 1250
  correct_predictions: 1087
  last_updated: "2026-07-22T10:00:00"
```

### 3.3 Agent生命周期阶段

```
Phase 1: PROPOSAL（提案）
  → Agent或人类提出新Agent概念
  → 包含：Hypothesis + Expected Impact + Evidence

Phase 2: EC REVIEW（进化委员会审批）
  → EC评估提案
  → 投票：Approve / Reject / Revise

Phase 3: UT/SIT/RT（单元测试/集成测试/回归测试）
  → 代码质量、逻辑正确性

Phase 4: BACKTEST（回测）
  → 过去1年历史数据
  → Pass条件：胜率>50%，最大回撤<10%

Phase 5: PAPER TRADING（模拟交易）
  → 30天真实市场
  → Pass条件：胜率>55%，盈亏比>1.5

Phase 6: PRODUCTION（生产环境）
  → 小仓位实盘
  → Pass条件：30天正收益

Phase 7: MONITORING（持续监控）
  → 每日KPI评估
  → 连续3次失败 → 触发Coach Agent审查
```

### 3.4 Agent约束

- Agent只有**建议权**，没有**修改权**
- Agent不能修改自己
- Agent不能修改Constitution
- Agent的所有学习必须记录到Learning Ledger
- Agent的所有学习必须可Rollback

---

## 4. Memory Architecture

### 4.1 四层记忆

```
Layer 1: Raw Memory（TimescaleDB）
  → prices, prices_cn, paper_trades
  → 原始数据，不丢失

Layer 2: Structured Memory（TimescaleDB）
  → agent_states, learning_ledger, aiic_decisions
  → 结构化知识，可查询

Layer 3: Knowledge Base（文件系统）
  → ARCHITECTURE_SPECIFICATION.md
  → FEATURE_SPECIFICATION.md
  → 长期知识，版本控制

Layer 4: Working Memory（运行时）
  → 当前session上下文
  → 临时状态，session结束消失
```

### 4.2 记忆保障

- 所有关键数据存TimescaleDB（Master + Standby冗余）
- 架构文档存文件系统（版本控制）
- 每次session启动自动加载Working Memory
- 13年历史数据（1300万行）不可重建 → 最高保护

---

## 5. AI Investment Committee (AIIC)

### 5.1 架构

```
AI Investment Committee (AIIC)
│
├── Bull Team（找上涨理由）
│   → 输入：市场数据、新闻、资金流
│   → 输出：上涨理由 + Confidence
│
├── Bear Team（找反例和风险）
│   → 输入：市场数据、新闻、资金流
│   → 输出：反例 + 风险 + Confidence
│
├── Risk Team（仓位、回撤、极端事件）
│   → 输入：当前持仓、市场波动率
│   → 输出：风险评估 + 仓位建议
│
├── Testing Team（四层测试）
│   → UT/SIT/RT → Backtest → Paper → Production
│
├── Historian（历史学家）
│   → 输入：当前市场状态
│   → 输出：历史相似度 + 历史结果 + Confidence
│
├── Critic Agent（批评者）
│   → 输入：任何Decision
│   → 输出：为什么？最大风险？最大反例？
│
├── Auditor Agent（审计）
│   → 输入：Prediction + Reality
│   → 输出：Difference + Reason + Who Responsible
│
├── Coach Agent（教练）
│   → 输入：每个Agent的KPI
│   → 输出：改进建议（不直接执行）
│
└── Committee Chair (Meta Brain)
    → 综合所有证据
    → 最终决策
```

### 5.2 决策流程

```
1. Meta Brain检测市场状态（Trend/Range/Event/Risk-off）
2. 动态调整Agent权重
3. Bull Team提出上涨理由
4. Bear Team提出反例
5. Risk Team评估风险
6. Historian搜索历史相似场景
7. Critic Agent审查逻辑漏洞
8. Meta Brain综合 → Final Decision
9. Auditor Agent记录决策
10. 结果反馈 → Learning Ledger
```

### 5.3 Peer Review（互相监督）

- Agent之间互相审查
- 检测Conflict → 降低Confidence
- 严重Conflict → 不执行，人工审查

### 5.4 动态权重

| 市场状态 | Bull权重 | Bear权重 | Risk权重 | Historian权重 |
|----------|----------|----------|----------|---------------|
| Trend | 0.4 | 0.2 | 0.2 | 0.2 |
| Range | 0.2 | 0.3 | 0.3 | 0.2 |
| Event | 0.3 | 0.3 | 0.2 | 0.2 |
| Risk-off | 0.1 | 0.2 | 0.5 | 0.2 |

---

## 6. Learning & Evolution Framework

### 6.1 五个Self能力

| 能力 | 功能 | 实现方式 | 成本 |
|------|------|----------|------|
| Self-Monitoring | 系统运行正常吗？ | Python脚本 | 免费 |
| Self-Evaluation | 哪些预测成功/失败？ | Python统计 | 免费 |
| Self-Calibration | Confidence是否校准？ | Python统计 | 免费 |
| Self-Improvement | 自动调整参数 | Python + Hermes | 免费 |
| Self-Evolution | 提出新Agent/策略 | Hermes + EC审批 | 免费/低 |

### 6.2 在线学习 vs 离线学习

```
Trading Hours (盘中)
  → Learning OFF
  → 只执行，不学习

Market Close (收盘后)
  → Learning ON
  → Replay → Backtest → Improve → 第二天验证
```

### 6.3 Learning Ledger（学习账本）

```yaml
Learning:
  time: "2026-07-22T13:00:00"
  agent: "News Agent"
  change_type: "weight_adjustment"
  old_value: 0.32
  new_value: 0.47
  reason: "Macro连续失败3次"
  evidence: "最近10次预测，Macro准确率40%"
  backtest_result: "过去1年数据，新权重胜率+5%"
  actual_result: "pending"
  rollback_triggered: false
  rollback_condition: "如果第二天胜率<45%，自动回滚到0.32"
  approved_by: "Evolution Council"
```

### 6.4 Evolution Council（进化委员会）

```
Agent → Proposal（建议）
  → Evolution Council（审批）
  → Testing（验证）
  → A/B Test（对比）
  → Deploy（上线）
```

- Agent只有建议权，没有修改权
- EC审批必须记录：Who, Why, When
- 任何修改必须有Rollback Plan
- 防止Configuration Drift

### 6.5 科学方法（Scientific Method）

```
Observation → Hypothesis → Testing → Result → Deploy/Reject
```

Hypothesis格式：
```
IF [change]
THEN [expected impact]
BECAUSE [reasoning]
MEASURED BY [metric]
```

---

## 7. Testing & Deployment Pipeline

### 7.1 四层测试

```
Layer 1: UT/SIT/RT（单元测试/集成测试/回归测试）
  → 代码质量、逻辑正确性
  → Pass条件：100%测试通过

Layer 2: Backtest（回测）
  → 过去1年历史数据
  → Pass条件：胜率>50%，最大回撤<10%

Layer 3: Paper Trading（模拟交易）
  → 30天真实市场，不花钱
  → Pass条件：胜率>55%，盈亏比>1.5

Layer 4: Production（生产环境）
  → 小仓位实盘（$100）
  → Pass条件：30天正收益
```

### 7.2 部署流程

```
新Agent/策略
  ↓
UT/SIT/RT → PASS
  ↓
Backtest → PASS
  ↓
Paper Trading (30天) → PASS
  ↓
EC审批 → APPROVED
  ↓
Production (小仓位)
  ↓
持续监控
```

### 7.3 回滚机制

- 任何部署必须有Rollback Plan
- 触发条件：连续3次失败 / 最大回撤>5%
- 自动回滚 + 通知Hao

---

## 8. Constitution（不可违反的规则）

### 8.1 规则列表

```yaml
Constitution:
  Rule1: 最大回撤永远不能超过10%
  Rule2: 任何新策略必须Paper Trading 30天
  Rule3: 任何学习必须可Rollback
  Rule4: 任何Agent不能修改Constitution
  Rule5: 盘中（Trading Hours）禁止自动调参
  Rule6: 任何进化必须经过EC审批
  Rule7: 所有决策必须可审计（Audit Trail）
  Rule8: 数据库可靠性 > 预测模型
  Rule9: 13年历史数据不可丢失
  Rule10: 优先使用本地资源，减少付费quota
```

### 8.2 Constitution修改规则

- 只有Hao可以批准修改
- 修改必须记录：Who, When, Why, What
- 修改后自动通知所有Agent
- 修改历史永久保存

### 8.3 违规检测

- 每次决策自动检查Constitution
- 违规 → 立即阻止 + 记录到constitution_violations表
- 严重违规 → 通知Hao

---

## 9. Roadmap

### Phase 0：基础闭环（HOUR 1-5）
- ✅ Paper Trading接入cron
- ✅ Self-Monitoring
- ✅ 每日盈亏报告
- ✅ Self-Evaluation

### Phase 1：AIIC基础（HOUR 6-10）
- Bull/Bear Team
- Risk Team
- Testing Team
- Meta Brain（基础版）

### Phase 2：学习层（HOUR 11-15）
- Learning Ledger
- Self-Calibration
- Self-Improvement
- Coach Agent

### Phase 3：进化层（HOUR 16-20）
- Evolution Council
- Self-Evolution
- Historian
- Critic + Auditor

### Phase 4：宪法层（HOUR 21-25）
- Constitution引擎
- 违规检测
- 回滚机制
- 完整文档

### Phase 5：全面运行（HOUR 26-30）
- 端到端测试
- 全部接入cron
- 性能优化
- Hao最终审批

---

## 10. KPI 与 Success Metrics

### 10.1 系统级KPI

| KPI | 目标 | 测量方式 |
|-----|------|----------|
| 系统可用性 | >99% | Self-Monitoring |
| 数据完整性 | 100% | validate_data_integrity.py |
| 每日盈亏 | 正收益 | daily_pnl_report.py |
| 胜率 | >55% | paper_trade_engine.py |
| 盈亏比 | >1.5 | paper_trade_engine.py |

### 10.2 Agent级KPI

| KPI | 目标 | 测量方式 |
|-----|------|----------|
| Leader Accuracy Top1 | >50% | self_evaluation.py |
| Leader Accuracy Top5 | >70% | self_evaluation.py |
| Sector Hit Rate | >60% | self_evaluation.py |
| Confidence Calibration | 误差<10% | self_calibration.py |

### 10.3 进化KPI

| KPI | 目标 | 测量方式 |
|-----|------|----------|
| Evolution Proposal通过率 | >30% | evolution_proposals表 |
| Learning Rollback率 | <20% | learning_ledger表 |
| Constitution违规次数 | 0 | constitution_violations表 |

### 10.4 Success Metrics（6个月后）

- Paper trading胜率稳定>55%
- 系统连续30天无Constitution违规
- 至少完成3次Self-Evolution（新Agent上线）
- Learning Ledger记录>100条
- 最大回撤<10%

---

## 附录

### A. 文档清单

| 文档 | 状态 | 说明 |
|------|------|------|
| ARCHITECTURE_SPECIFICATION_V1.md | ✅ Draft | 本文档 |
| FEATURE_SPECIFICATION.md | ⏳ Pending | 每个Agent的功能规格 |
| FUNCTIONALITY_SPECIFICATION.md | ⏳ Pending | 每个功能的具体实现 |
| TESTING_PLAN.md | ⏳ Pending | 四层测试的具体标准 |
| USER_GUIDE.md | ⏳ Pending | Hao如何使用系统 |
| OPERATIONS_MANUAL.md | ⏳ Pending | 运维手册 |
| API_SPECIFICATION.md | ⏳ Pending | Agent间通信接口 |

### B. 术语表

| 术语 | 定义 |
|------|------|
| NGAIQOS | Next Generation AI Quant Operating System |
| NSPS | New SPS（下一代SPS） |
| AIIC | AI Investment Committee |
| EC | Evolution Council |
| CLFA | Closed Loop Full Automation |
| CE | Controlled Evolution |
| SM | Scientific Method |
| SC | System Constitution |

### C. 参考

- Bridgewater：多团队互相挑战
- Two Sigma：数据驱动 + 自动化
- Citadel：严格风控 + 可逆操作

---

*Document Version: 1.0 | Last Updated: 2026-07-22 | Author: Alca | Reviewer: Pending (Hao)*
