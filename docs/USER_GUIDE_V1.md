# NSPS User Guide v1.0

> **Hao如何使用NSPS系统：查询、审批、监控**

Version: 1.0 | Created: 2026-07-22 | Status: Draft

---

## 目录

1. [每日业绩报告](#1-每日业绩报告)
2. [查询Learning Ledger](#2-查询learning-ledger)
3. [审批Evolution Proposal](#3-审批evolution-proposal)
4. [查看Agent状态](#4-查看agent状态)
5. [查看AIIC决策记录](#5-查看aiic决策记录)
6. [手动触发回滚](#6-手动触发回滚)
7. [修改Constitution](#7-修改constitution)
8. [系统健康检查](#8-系统健康检查)

---

## 1. 每日业绩报告

### 自动推送

**时间：**
- US收盘后：每日1:30 PM PT
- CN收盘后：每日12:30 AM PT

**内容：**
```
📊 NSPS 每日业绩报告 — 2026-07-22

【US市场】
总交易: 5笔
胜率: 60% (3赢2输)
总盈亏: +$450 (+0.45%)
最大单笔盈利: +$200 (NVDA)
最大单笔亏损: -$100 (TSLA)

【CN市场】
总交易: 3笔
胜率: 66.7% (2赢1输)
总盈亏: +¥3,200 (+0.32%)
最大单笔盈利: +¥2,000 (600519)
最大单笔亏损: -¥800 (000858)

【累计】
总交易: 150笔
累计胜率: 58%
累计盈亏: +$12,500 (+12.5%)
最大回撤: 3.2%

【诊断】
✅ 整体表现良好，胜率>55%
⚠️ TSLA连续2次亏损，建议审查Bear Team逻辑
```

### 手动查询

```bash
# 查看今日业绩
python3 projects/ngaiqos/scripts/daily_pnl_report.py --date 2026-07-22

# 查看最近10天业绩
python3 projects/ngaiqos/scripts/daily_pnl_report.py --days 10

# 查看US市场
python3 projects/ngaiqos/scripts/daily_pnl_report.py --market us

# 查看CN市场
python3 projects/ngaiqos/scripts/daily_pnl_report.py --market cn
```

---

## 2. 查询Learning Ledger

### 什么是Learning Ledger？

记录所有自动调参、学习、优化的历史，可审计、可回滚。

### 查询方式

```bash
# 查看最近10条学习记录
python3 projects/ngaiqos/scripts/query_learning_ledger.py --limit 10

# 输出示例：
# ID | 时间 | Agent | 变更类型 | 旧值 → 新值 | 原因 | 结果
# 42 | 2026-07-22 13:00 | News Agent | weight | 0.32 → 0.47 | Macro连续失败 | ✅ 胜率+5%
# 41 | 2026-07-21 13:00 | Bull Team | threshold | 0.6 → 0.7 | 假突破太多 | ✅ 准确率+8%
```

### 按条件查询

```bash
# 查询某个Agent的学习记录
python3 projects/ngaiqos/scripts/query_learning_ledger.py --agent "News Agent"

# 查询某天的学习记录
python3 projects/ngaiqos/scripts/query_learning_ledger.py --date 2026-07-22

# 查询失败的调整（需要回滚）
python3 projects/ngaiqos/scripts/query_learning_ledger.py --status failed
```

### 数据库直接查询

```sql
-- 连接TimescaleDB
docker exec sps-timescaledb-master psql -U saps -d sps

-- 查询最近的学习记录
SELECT * FROM learning_ledger 
ORDER BY time DESC 
LIMIT 10;

-- 查询某个Agent的学习历史
SELECT * FROM learning_ledger 
WHERE agent_name = 'News Agent'
ORDER BY time DESC;

-- 查询需要回滚的记录
SELECT * FROM learning_ledger 
WHERE rollback_triggered = true;
```

---

## 3. 审批Evolution Proposal

### 什么是Evolution Proposal？

Agent提出的系统改进建议（新Agent、新策略、新参数），必须经过你审批。

### 查看待审批的Proposal

```bash
# 查看所有待审批的Proposal
python3 projects/ngaiqos/scripts/query_evolution_proposals.py --status pending

# 输出示例：
# ID | 时间 | 提案Agent | 类型 | 内容 | 预期影响
# 15 | 2026-07-22 | News Agent | 新Agent | 增加Option Agent | 胜率+5%
```

### 审批流程

```bash
# 查看Proposal详情
python3 projects/ngaiqos/scripts/approve_proposal.py --id 15 --action view

# 输出：
# Proposal #15: 增加Option Agent
# 提案者: News Agent
# 假设: Option Flow可能提高Leader Accuracy 5%
# 证据: 过去1年数据，Option Flow与股价相关性0.7
# 回测结果: 胜率58%，盈亏比1.8
# 回滚计划: 如果Paper Trading胜率<50%，自动拒绝

# 审批通过
python3 projects/ngaiqos/scripts/approve_proposal.py --id 15 --action approve --reason "证据充分，回测通过"

# 审批拒绝
python3 projects/ngaiqos/scripts/approve_proposal.py --id 15 --action reject --reason "证据不足，需要更多数据"
```

### 数据库直接查询

```sql
-- 查询待审批的Proposal
SELECT * FROM evolution_proposals 
WHERE ec_status = 'PENDING';

-- 查询已审批的Proposal
SELECT * FROM evolution_proposals 
WHERE ec_status IN ('APPROVED', 'REJECTED');
```

---

## 4. 查看Agent状态

### 查看所有Agent状态

```bash
# 查看所有Agent的实时状态
python3 projects/ngaiqos/scripts/query_agent_states.py

# 输出示例：
# Agent | 版本 | 准确率 | Confidence | 强度 | 弱点 | 学习速率
# Bull Team | 1.2.0 | 62% | 0.85 | Trend市场 | 震荡市场 | 0.02
# Bear Team | 1.1.5 | 58% | 0.78 | 超买信号 | 宏观判断 | 0.03
# Risk Team | 2.0.0 | 85% | 0.92 | 回撤控制 | 极端事件 | 0.01
```

### 查看某个Agent详情

```bash
# 查看Bull Team详情
python3 projects/ngaiqos/scripts/query_agent_states.py --agent "Bull Team"

# 输出：
# Agent: Bull Team
# 版本: 1.2.0
# 总预测: 1250
# 正确预测: 775
# 准确率: 62%
# Confidence: 0.85
# 最近10次: 70%
# 最近100次: 65%
# 强度: ["Trend市场", "AI板块", "科技股"]
# 弱点: ["震荡市场", "能源板块"]
# 学习速率: 0.02
# 最后更新: 2026-07-22 13:00:00
```

### 数据库直接查询

```sql
-- 查询所有Agent状态
SELECT * FROM agent_states 
ORDER BY accuracy DESC;

-- 查询某个Agent的历史表现
SELECT * FROM agent_states 
WHERE agent_name = 'Bull Team'
ORDER BY last_updated DESC;
```

---

## 5. 查看AIIC决策记录

### 什么是AIIC决策记录？

AI Investment Committee的每次决策（买/卖/持有），包括Bull/Bear/Risk的理由。

### 查看今日决策

```bash
# 查看今日AIIC决策
python3 projects/ngaiqos/scripts/query_aiic_decisions.py --date 2026-07-22

# 输出示例：
# 时间 | 股票 | 决策 | Confidence | Bull理由 | Bear理由 | Risk评估
# 09:30 | NVDA | Buy | 0.85 | 资金流入+15% | RSI=78超买 | 回撤3.5%，可参与
# 09:30 | TSLA | Hold | 0.65 | 新闻利好 | 连续2次亏损 | 风险较高
```

### 查看某个股票的决策历史

```bash
# 查看NVDA的决策历史
python3 projects/ngaiqos/scripts/query_aiic_decisions.py --stock NVDA --days 7
```

### 数据库直接查询

```sql
-- 查询今日决策
SELECT * FROM aiic_decisions 
WHERE date = '2026-07-22';

-- 查询某个股票的决策历史
SELECT * FROM aiic_decisions 
WHERE stock = 'NVDA'
ORDER BY time DESC
LIMIT 10;
```

---

## 6. 手动触发回滚

### 什么时候需要回滚？

- 某次自动调参导致胜率下降
- 某个新Agent表现不佳
- Constitution违规

### 回滚流程

```bash
# 查看可回滚的学习记录
python3 projects/ngaiqos/scripts/query_learning_ledger.py --rollbackable true

# 输出：
# ID | 时间 | Agent | 变更 | 旧值 | 新值 | 原因 | 结果
# 42 | 2026-07-22 13:00 | News Agent | weight | 0.32 | 0.47 | Macro失败 | ❌ 胜率-5%

# 手动回滚
python3 projects/ngaiqos/scripts/rollback_learning.py --id 42 --reason "胜率下降，回滚到旧值"

# 输出：
# ✅ 已回滚 Learning Ledger #42
# News Agent weight: 0.47 → 0.32
# 回滚原因: 胜率下降，回滚到旧值
# 回滚时间: 2026-07-22 14:00:00
```

### 自动回滚

系统会自动回滚，如果：
- 调参后胜率下降>5%
- 最大回撤>8%
- Constitution违规

```bash
# 查看自动回滚记录
python3 projects/ngaiqos/scripts/query_learning_ledger.py --auto_rollback true
```

---

## 7. 修改Constitution

### 什么是Constitution？

系统宪法，不可违反的最高规则。只有你可以修改。

### 查看当前Constitution

```bash
# 查看当前Constitution
python3 projects/ngaiqos/scripts/query_constitution.py

# 输出：
# Rule 1: 最大回撤永远不能超过10%
# Rule 2: 任何新策略必须Paper Trading 30天
# Rule 3: 任何学习必须可Rollback
# Rule 4: 任何Agent不能修改Constitution
# Rule 5: 盘中（Trading Hours）禁止自动调参
# Rule 6: 任何进化必须经过EC审批
# Rule 7: 所有决策必须可审计（Audit Trail）
# Rule 8: 数据库可靠性 > 预测模型
# Rule 9: 13年历史数据不可丢失
# Rule 10: 优先使用本地资源，减少付费quota
```

### 修改Constitution

```bash
# 添加新规则
python3 projects/ngaiqos/scripts/update_constitution.py --action add --rule "Rule 11: 每日最大交易次数不超过10笔" --reason "防止过度交易"

# 修改现有规则
python3 projects/ngaiqos/scripts/update_constitution.py --action modify --rule "Rule 1" --new_value "最大回撤永远不能超过8%" --reason "更严格的风控"

# 删除规则
python3 projects/ngaiqos/scripts/update_constitution.py --action delete --rule "Rule 11" --reason "规则过于严格"
```

### 查看修改历史

```bash
# 查看Constitution修改历史
python3 projects/ngaiqos/scripts/query_constitution.py --history

# 输出：
# 时间 | 操作 | 规则 | 旧值 | 新值 | 原因 | 审批人
# 2026-07-22 14:00 | MODIFY | Rule 1 | 10% | 8% | 更严格风控 | Hao
# 2026-07-20 10:00 | ADD | Rule 10 | - | 优先本地资源 | 节省quota | Hao
```

---

## 8. 系统健康检查

### 自动健康检查

系统每小时自动检查：
- TimescaleDB连接
- 数据新鲜度
- Cron job状态
- 系统资源（磁盘、内存）

### 手动健康检查

```bash
# 运行健康检查
python3 projects/ngaiqos/scripts/self_monitoring.py

# 输出：
# 🔍 Self-Monitoring Report — 2026-07-22T14:00:00
# 
# 总体状态: ✅ HEALTHY
# 
# ✅ TimescaleDB: 正常
#    最新数据: 2026-07-22, 近7天: 25000行
#    Paper Trades: 5 OPEN, 145 CLOSED
# 
# ✅ 数据更新: 正常
#    US市场: 4500条 (今日已更新)
#    CN市场: 5530条 (今日已更新)
# 
# ✅ 系统资源: 磁盘1%
# 
# ✅ Cron Jobs:
#    • self_monitoring.log: 0.0h前, 无错误
#    • paper_trade_engine.log: 1.0h前, 无错误
```

### 查看健康检查日志

```bash
# 查看最近的健康检查日志
tail -50 logs/self_monitoring.log

# 查看今天的健康检查报告
cat logs/self_monitoring_report_2026-07-22.log
```

---

## 附录：常用命令速查

```bash
# 每日业绩报告
python3 projects/ngaiqos/scripts/daily_pnl_report.py --date 2026-07-22

# 查询Learning Ledger
python3 projects/ngaiqos/scripts/query_learning_ledger.py --limit 10

# 审批Evolution Proposal
python3 projects/ngaiqos/scripts/approve_proposal.py --id 15 --action approve

# 查看Agent状态
python3 projects/ngaiqos/scripts/query_agent_states.py

# 查看AIIC决策
python3 projects/ngaiqos/scripts/query_aiic_decisions.py --date 2026-07-22

# 手动回滚
python3 projects/ngaiqos/scripts/rollback_learning.py --id 42

# 查看Constitution
python3 projects/ngaiqos/scripts/query_constitution.py

# 系统健康检查
python3 projects/ngaiqos/scripts/self_monitoring.py
```

---

*Document Version: 1.0 | Last Updated: 2026-07-22 | Author: Alca*
