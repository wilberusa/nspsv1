# NSPS Testing Plan v1.0

> **四层测试标准：UT/SIT/RT → Backtest → Paper Trading → Production**

Version: 1.0 | Created: 2026-07-22 | Status: Draft

---

## 1. 测试总览

```
Layer 1: UT/SIT/RT → 代码质量
Layer 2: Backtest → 历史验证
Layer 3: Paper Trading → 模拟实战（30天）
Layer 4: Production → 小仓位实盘（30天）
```

**铁律：任何新Agent/策略必须通过全部四层才能上线。**

---

## 2. Layer 1: UT/SIT/RT

### 2.1 Unit Test（单元测试）

| 测试项 | 方法 | Pass条件 |
|--------|------|----------|
| 数据加载 | 验证TimescaleDB连接、数据完整性 | 连接成功，数据>0行 |
| 指标计算 | RSI/MACD/Volume Ratio对比已知答案 | 误差<0.1% |
| 信号生成 | 给定输入，验证输出格式 | YAML格式正确，字段完整 |
| Confidence计算 | 给定输入，验证Confidence范围 | 0≤Confidence≤1 |
| 边界条件 | 空数据、极端价格、NaN值 | 不崩溃，返回合理默认值 |

### 2.2 System Integration Test（集成测试）

| 测试项 | 方法 | Pass条件 |
|--------|------|----------|
| Agent间通信 | Bull→Bear→Risk→Meta Brain全链路 | 数据正确传递 |
| 数据库读写 | 写入paper_trades→读取→验证 | 数据一致 |
| Cron触发 | 模拟cron触发→验证执行 | 脚本正常运行 |
| Telegram推送 | 生成报告→发送→验证message_id | 送达确认 |
| Constitution检查 | 故意触发违规→验证阻止 | 违规被阻止并记录 |

### 2.3 Regression Test（回归测试）

| 测试项 | 方法 | Pass条件 |
|--------|------|----------|
| 历史场景复现 | 用过去10个已知场景重新运行 | 结果与历史一致 |
| 参数变更影响 | 修改参数后对比基线 | 不会导致已有功能退化 |
| 数据一致性 | SQLite vs TimescaleDB对比 | 差异=0 |

### 2.4 执行方式

```bash
# 运行全部UT/SIT/RT
cd projects/ngaiqos
pytest tests/ -v --tb=short

# 预期输出
# ====== 100 passed in 30s ======
```

### 2.5 Pass标准
- 测试覆盖率 > 90%
- 0 failed tests
- 执行时间 < 5分钟

---

## 3. Layer 2: Backtest（回测）

### 3.1 数据集

| 数据集 | 时间范围 | 用途 |
|--------|----------|------|
| US全量 | 2012-2026（13年） | 主回测 |
| CN全量 | 2012-2026（13年） | 主回测 |
| 牛市场景 | 2020-03~2021-12 | 牛市表现 |
| 熊市场景 | 2022-01~2022-12 | 熊市表现 |
| 震荡场景 | 2023-01~2023-06 | 震荡表现 |

### 3.2 回测指标

| 指标 | Pass条件 | 说明 |
|------|----------|------|
| 胜率 | > 50% | 盈利交易/总交易 |
| 盈亏比 | > 1.5 | 平均盈利/平均亏损 |
| 最大回撤 | < 10% | Constitution Rule 1 |
| 夏普比率 | > 1.0 | 风险调整后收益 |
| 交易次数 | > 100 | 统计显著性 |
| p-value | < 0.05 | 结果不是随机 |

### 3.3 执行方式

```bash
# 回测脚本
python3 projects/ngaiqos/scripts/backtest_engine.py \
  --strategy new_strategy \
  --market us \
  --start 2012-01-01 \
  --end 2026-07-22 \
  --initial-capital 100000

# 输出
# Win Rate: 58.3% ✅
# Profit Factor: 1.8 ✅
# Max Drawdown: 7.2% ✅
# Sharpe Ratio: 1.5 ✅
# Total Trades: 342 ✅
# p-value: 0.003 ✅
# RESULT: PASS
```

### 3.4 Pass标准
- 全部6个指标达标 → PASS
- 任何一个不达标 → FAIL，回到Layer 1修改

---

## 4. Layer 3: Paper Trading（模拟交易）

### 4.1 规则

| 项目 | 规则 |
|------|------|
| 时长 | 30个自然日 |
| 虚拟资金 | $100,000 |
| 每笔上限 | $2,000 |
| 记录方式 | paper_trades表（TimescaleDB） |
| 评估频率 | 每日收盘后 |

### 4.2 Pass条件

| 指标 | Pass条件 | 说明 |
|------|----------|------|
| 胜率 | > 55% | 比回测更严格 |
| 盈亏比 | > 1.5 | 与回测一致 |
| 最大回撤 | < 8% | 比回测更严格（留buffer） |
| 交易天数 | ≥ 25天 | 不能中途停止 |
| Constitution违规 | 0次 | 零容忍 |

### 4.3 自动监控

```python
# 每日收盘后自动检查
def paper_trading_monitor():
    trades = get_paper_trades(days=30)
    
    # 检查胜率
    win_rate = calc_win_rate(trades)
    if win_rate < 0.45 and len(trades) > 10:
        alert("Paper Trading胜率过低，建议提前终止")
    
    # 检查回撤
    drawdown = calc_drawdown(trades)
    if drawdown > 0.08:
        alert("Paper Trading回撤超过8%，自动终止")
        return 'TERMINATED'
    
    # 检查Constitution
    violations = check_constitution_violations()
    if violations > 0:
        alert("Constitution违规，自动终止")
        return 'TERMINATED'
    
    # 30天后评估
    if days_completed >= 30:
        if all_conditions_met():
            return 'PASS → 进入Layer 4'
        else:
            return 'FAIL → 回到Layer 1'
```

### 4.4 提前终止条件
- 最大回撤 > 8%
- 连续5笔亏损
- Constitution违规

---

## 5. Layer 4: Production（生产环境）

### 5.1 规则

| 项目 | 规则 |
|------|------|
| 时长 | 30个自然日 |
| 初始仓位 | $100（最小仓位） |
| 逐步加仓 | 通过审核后每周翻倍 |
| 最大仓位 | $2,000 |
| 止损 | 3%硬止损 |

### 5.2 Pass条件

| 指标 | Pass条件 |
|------|----------|
| 收益 | > 0%（正收益） |
| 最大回撤 | < 5% |
| Constitution违规 | 0次 |
| 系统可用性 | > 99% |

### 5.3 逐步加仓

```
Week 1: $100 → 如果正收益
Week 2: $200 → 如果正收益
Week 3: $500 → 如果正收益
Week 4: $1,000 → 如果正收益
Week 5+: $2,000 → 正式上线
```

### 5.4 自动回滚

```python
def production_monitor():
    if drawdown > 0.05:
        rollback()
        alert("Production回撤>5%，自动回滚")
    
    if consecutive_losses >= 3:
        reduce_position()
        alert("连续3笔亏损，减仓50%")
    
    if constitution_violation():
        stop_trading()
        alert("Constitution违规，停止交易")
```

---

## 6. 测试记录

所有测试结果记录到TimescaleDB：

```sql
CREATE TABLE testing_results (
    id SERIAL PRIMARY KEY,
    test_time TIMESTAMP,
    agent_name TEXT,
    strategy_name TEXT,
    layer INTEGER,  -- 1=UT/SIT/RT, 2=Backtest, 3=Paper, 4=Production
    status TEXT,    -- PASS, FAIL, IN_PROGRESS
    metrics JSONB,  -- 具体指标
    details TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 7. 测试自动化

```bash
# 完整测试流水线
python3 projects/ngaiqos/scripts/test_pipeline.py \
  --agent new_agent \
  --strategy new_strategy

# 输出
# Layer 1: UT/SIT/RT ............ PASS (45s)
# Layer 2: Backtest ............. PASS (120s)
# Layer 3: Paper Trading ........ IN PROGRESS (Day 15/30)
# Layer 4: Production ........... PENDING
```

---

*Document Version: 1.0 | Last Updated: 2026-07-22 | Author: Alca*
