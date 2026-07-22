# NSPS-V1: Next Generation AI Quant Operating System

> **NSPS不是一个预测市场的AI，而是一个能够持续提升自身认知能力的市场智能体（Market Intelligence System，MIS）。**

## 核心原则

**Controlled Evolution（受控进化）**
> 任何能够自动改变系统的能力，都必须比产生这个改变的能力受到更严格的约束。

- Agent只有建议权，没有修改权
- 所有学习必须可回滚（Learning Ledger）
- 盘中禁止自动调参（Constitution Rule 5）
- 所有进化必须经过EC审批

## 架构

```
AI Investment Committee (AIIC)
├── Bull Team（找上涨理由）
├── Bear Team（找反例和风险）
├── Risk Team（仓位、回撤、极端事件）
├── Historian（历史相似场景搜索）
├── Critic Agent（批评者）
├── Auditor Agent（审计）
├── Coach Agent（教练）
└── Meta Brain（综合决策 + 市场状态检测）
    ↑
Evolution Council（进化委员会）
    ↑
Constitution（系统宪法，10条不可违反的规则）
```

## 核心模块

| 模块 | 文件 | 功能 | 状态 |
|------|------|------|------|
| Agent状态管理 | `agent_state_manager.py` | 8个Agent状态、KPI、版本 | ✅ |
| 学习账本 | `learning_ledger.py` | 所有调参记录，可审计、可回滚 | ✅ |
| 宪法引擎 | `constitution_engine.py` | 10条宪法 + 违规检测 | ✅ |
| 进化委员会 | `evolution_council.py` | 提案 + 投票 + 审批 | ✅ |
| 历史学家 | `historian.py` | 历史相似场景搜索 | ✅ |
| Bull/Bear Team | `bull_bear_team.py` | 纯规则引擎分析 | ✅ |
| Meta Brain | `meta_brain.py` | 市场状态检测 + 动态权重 + 最终决策 | ✅ |
| Self-Monitoring | `self_monitoring.py` | 系统健康检查 | ✅ |

## 铁律

1. **本地资源优先**：Python + Hermes 70B + TimescaleDB，0 quota
2. **每写必测**：每个模块写完立即测试
3. **闭环全自动（CLFA）**：做完报告，不等批准

## 快速开始

```bash
# 测试所有模块
cd projects/ngaiqos
python3 scripts/agent_state_manager.py
python3 scripts/learning_ledger.py
python3 scripts/constitution_engine.py
python3 scripts/evolution_council.py
python3 scripts/historian.py
python3 scripts/bull_bear_team.py
python3 scripts/meta_brain.py
python3 scripts/self_monitoring.py
```

## 文档

- `docs/ARCHITECTURE_SPECIFICATION_V1.md` — 架构规范（10章节）
- `docs/FEATURE_SPECIFICATION_V1.md` — 功能规格（10个Agent）
- `docs/FUNCTIONALITY_SPECIFICATION_V1.md` — 实现逻辑（10个功能）
- `docs/TESTING_PLAN_V1.md` — 四层测试标准
- `docs/USER_GUIDE_V1.md` — 用户手册
- `docs/OPERATIONS_MANUAL_V1.md` — 运维手册
- `docs/API_SPECIFICATION_V1.md` — 接口定义

## 10条宪法

1. 最大回撤永远不能超过10%
2. 任何新策略必须Paper Trading 30天
3. 任何学习必须可Rollback
4. 任何Agent不能修改Constitution
5. 盘中禁止自动调参
6. 任何进化必须经过EC审批
7. 所有决策必须可审计
8. 数据库可靠性 > 预测模型
9. 13年历史数据不可丢失
10. 优先使用本地资源，减少付费quota

---

*Created: 2026-07-22 | Status: Active Development | Quota Used: 0*
