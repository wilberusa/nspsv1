# NGAIQOS — Next Generation AI Quant Operating System

> **NSPS不是一个预测市场的AI，而是一个能够持续提升自身认知能力的市场智能体（Market Intelligence System，MIS）。**

Created: 2026-07-22 | Status: Active Development

---

## 核心原则

**不是LLM在成长，是System在成长。**

LLM可以换（Hermes → Qwen → GPT-5），但系统的认知能力持续积累。

---

## 13点架构

### 1. 系统成长 > LLM成长
```
Observe → Think → Predict → Execute + FEEDBACK → Measure → Learn → Improve + UPDATE → Observe ...
```

### 2. Agent = 生命体（不是工具）
```
Input → Thinking → Decision → Evidence → Confidence → Result → Reflection → Improve → Output
```
每个Agent有状态：Accuracy, Confidence, Strength, Weakness, Learning Rate, Version

### 3. Agent必须有KPI
- Leader Accuracy: Top1/Top5/Top10
- Sector Hit Rate
- Sentiment Correct Rate

### 4. Agent之间不固定关系（动态权重）
- Trend市场 → Pattern权重高
- 震荡市场 → Flow权重高
- 事件驱动 → News权重高

### 5. Peer Review（互相监督）
- Agent之间互相审查
- 检测Conflict → Meta Brain仲裁

### 6. Critic Agent（批评者）
- 每次Decision后自动问：为什么？最大风险？最大反例？
- 回答不了 → Decision不通过

### 7. Auditor Agent（审计）
- Prediction → Reality → Difference → Reason → Who Responsible

### 8. Coach Agent（教练）
- 每天分析每个Agent表现
- 给出改进建议（不直接执行）

### 9. Meta Brain（升级）
- Market Regime Detection
- 动态调整整个Pipeline

### 10. 九环闭环
```
Observe → Collect Data → Understand Market → Generate Features → Make Prediction
→ Execute Strategy → Compare Reality → Learn & Reflect → Improve Whole System → Observe Again
```

### 11. 五个Self能力
| 能力 | 功能 | 优先级 |
|------|------|--------|
| Self-Monitoring | 系统运行正常吗？哪些Agent异常？ | ⭐️⭐️⭐️⭐️⭐️ |
| Self-Evaluation | 今天哪些预测成功/失败？ | ⭐️⭐️⭐️⭐️⭐️ |
| Self-Calibration | Confidence是否过高/过低？ | ⭐️⭐️⭐️⭐️⭐️ |
| Self-Improvement | 自动调整Prompt、权重、参数 | ⭐️⭐️⭐️⭐️ |
| Self-Evolution | 自动提出新Agent/策略，沙盒验证后上线 | ⭐️⭐️⭐️⭐️⭐️ |

### 12. AI Investment Committee (AIIC)
```
AIIC
├── Bull Team（找上涨理由）
├── Bear Team（找反例和风险）
├── Risk Team（仓位、回撤、极端事件）
├── Testing Team（测试、检验、确保质量）
└── Committee Chair (Meta Brain) → Final Decision
```

### 13. Self-Evolution = 核心创新
系统发现Option Flow价值越来越大 → 自己提出"建议增加Option Agent"
→ 沙盒验证 → 自动上线

---

## 实施计划（按HOUR推进）

| HOUR | 内容 | 状态 |
|------|------|------|
| 1 | Paper Trading接入 + Self-Monitoring | ✅ 完成 |
| 2 | 每日盈亏报告 + Self-Evaluation | ⏳ 待做 |
| 3 | Bull/Bear Team + Self-Calibration | ⏳ 待做 |
| 4 | Risk Team + Testing Team | ⏳ 待做 |
| 5 | Meta Brain + Agent状态管理 | ⏳ 待做 |
| 6 | Critic Agent + Auditor Agent | ⏳ 待做 |
| 7 | Coach Agent + Peer Review | ⏳ 待做 |
| 8 | Self-Improvement（自动调参） | ⏳ 待做 |
| 9 | Self-Evolution（AI提出新Agent/策略） | ⏳ 待做 |
| 10 | 完整测试 + 接入cron + 文档 | ⏳ 待做 |

---

## 铁律

1. **多用Python和本地资源（Hermes 70B），少用付费quota**
2. **只有本地模型置信度<70%时才调用云端**
3. **每个Agent的反思/诊断/教练 → Hermes 70B（本地）**
4. **数据处理/统计/回测/参数调整 → Python脚本（本地）**
5. **所有状态存TimescaleDB（不丢）**

---

## 关键文件

- 架构文档：`projects/ngaiqos/ARCHITECTURE.md`（本文件）
- Paper Trading Engine：`projects/sps-v3/scripts/paper_trade_engine.py`
- Self-Monitoring：`projects/sps-v3/scripts/self_monitoring.py`
- 每日笔记：`memory/2026-07-22.md`
- 长期记忆：`MEMORY.md`
