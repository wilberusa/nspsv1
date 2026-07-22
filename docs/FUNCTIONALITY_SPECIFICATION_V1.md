# NSPS Functionality Specification v1.0

> **每个功能的具体实现逻辑：数据、算法、流程**

Version: 1.0 | Created: 2026-07-22 | Status: Draft

---

## 目录

1. [Market Regime Detection](#1-market-regime-detection)
2. [Bull/Bear Reasoning Engine](#2-bullbear-reasoning-engine)
3. [Risk Assessment Engine](#3-risk-assessment-engine)
4. [Historian Similarity Engine](#4-historian-similarity-engine)
5. [Critic Logic Checker](#5-critic-logic-checker)
6. [Auditor Reconciliation](#6-auditor-reconciliation)
7. [Coach Performance Analyzer](#7-coach-performance-analyzer)
8. [Learning Engine (Offline)](#8-learning-engine-offline)
9. [Evolution Proposal Generator](#9-evolution-proposal-generator)
10. [Constitution Enforcement Engine](#10-constitution-enforcement-engine)

---

## 1. Market Regime Detection

### 功能
判断当前市场属于哪种状态：Trend / Range / Event / Risk-off

### 输入数据
- SPY/QQQ 20日均线方向（TimescaleDB: prices表）
- VIX指数（yfinance实时获取）
- 板块涨跌分布（TimescaleDB: sector_flow表）
- 市场宽度（上涨股票数/下跌股票数）

### 算法（纯Python，不花钱）
```python
def detect_regime():
    # 1. 趋势判断
    spy_ma20_direction = calc_ma_direction('SPY', 20)  # 上升/下降/平坦
    qqq_ma20_direction = calc_ma_direction('QQQ', 20)
    
    # 2. 波动率判断
    vix = get_vix()  # yfinance
    
    # 3. 板块分布
    up_sectors = count_up_sectors()
    down_sectors = count_down_sectors()
    
    # 4. 规则引擎
    if vix > 30:
        return 'RISK_OFF'
    elif spy_ma20_direction == 'UP' and up_sectors > down_sectors * 2:
        return 'TREND'
    elif abs(spy_ma20_direction) < 0.5:  # 平坦
        return 'RANGE'
    elif has_major_news_event():  # FOMC, CPI, etc.
        return 'EVENT'
    else:
        return 'RANGE'  # default
```

### 输出
```yaml
regime: "TREND"
confidence: 0.85
indicators:
  spy_ma20: "UP"
  vix: 18.5
  up_sectors: 8
  down_sectors: 3
```

### 执行频率
- 每个交易日开盘前1次
- 盘中每30分钟更新1次

---

## 2. Bull/Bear Reasoning Engine

### 功能
Bull Team找上涨理由，Bear Team找反例和风险

### 输入数据
- 目标股票的价格、成交量、资金流（TimescaleDB）
- 板块效应数据（sector_flow表）
- 新闻（MX-Search API）
- 技术指标（RSI, MACD, Volume Ratio）

### 算法

#### Bull Team
```python
def bull_reasoning(stock):
    reasons = []
    evidence = {}
    
    # 1. 资金流
    capital_flow = get_capital_flow(stock)
    if capital_flow > 0:
        reasons.append(f"主力资金流入{capital_flow}万")
        evidence['capital_flow'] = capital_flow
    
    # 2. 板块效应
    sector_strength = get_sector_strength(stock)
    if sector_strength > 3:  # 3只以上异动
        reasons.append(f"板块效应强，{sector_strength}只异动")
        evidence['sector_strength'] = sector_strength
    
    # 3. 新闻情绪
    news = mx_search(stock)
    sentiment = analyze_sentiment(news)  # Hermes 70B本地
    if sentiment > 0.7:
        reasons.append(f"新闻利好，情绪{sentiment:.2f}")
        evidence['news_sentiment'] = sentiment
    
    # 4. 技术面
    rsi = get_rsi(stock)
    volume_ratio = get_volume_ratio(stock)
    if rsi < 70 and volume_ratio > 1.5:
        reasons.append(f"技术面健康，RSI={rsi}, 量比={volume_ratio}")
        evidence['rsi'] = rsi
        evidence['volume_ratio'] = volume_ratio
    
    # 5. 历史相似场景
    historian = search_similar(stock)
    if historian['success_rate'] > 0.6:
        reasons.append(f"历史相似场景胜率{historian['success_rate']:.0%}")
        evidence['historian'] = historian
    
    # 6. Confidence计算
    confidence = len(reasons) / 5  # 5个维度
    confidence = min(confidence, 1.0)
    
    return {'reasons': reasons, 'evidence': evidence, 'confidence': confidence}
```

#### Bear Team
```python
def bear_reasoning(stock):
    risks = []
    evidence = {}
    
    # 1. 超买信号
    rsi = get_rsi(stock)
    if rsi > 75:
        risks.append(f"RSI={rsi}，超买区域")
        evidence['rsi'] = rsi
    
    # 2. 资金流出
    capital_flow = get_capital_flow(stock)
    if capital_flow < 0:
        risks.append(f"主力资金流出{abs(capital_flow)}万")
        evidence['capital_flow'] = capital_flow
    
    # 3. 高位风险
    price = get_price(stock)
    high_52w = get_52w_high(stock)
    if price > high_52w * 0.95:
        risks.append(f"接近52周高点，回调风险大")
        evidence['price_vs_high'] = price / high_52w
    
    # 4. 历史失败场景
    historian = search_similar(stock)
    if historian['failure_rate'] > 0.4:
        risks.append(f"历史相似场景失败率{historian['failure_rate']:.0%}")
        evidence['historian_failure'] = historian
    
    # 5. 宏观风险
    macro_risk = check_macro_risk()  # VIX, 利率, 地缘
    if macro_risk > 0.6:
        risks.append(f"宏观风险高，VIX={get_vix()}")
        evidence['macro_risk'] = macro_risk
    
    confidence = len(risks) / 5
    confidence = min(confidence, 1.0)
    
    return {'risks': risks, 'evidence': evidence, 'confidence': confidence}
```

### 实现方式
- 数据处理：Python（免费）
- 新闻情绪分析：Hermes 70B本地（免费）
- 历史相似搜索：Python + TimescaleDB（免费）

---

## 3. Risk Assessment Engine

### 功能
实时评估风险，控制仓位和回撤

### 输入数据
- 当前持仓（paper_trades表）
- 账户总值（固定$100,000虚拟）
- 市场波动率（VIX）
- Constitution Rule 1（最大回撤10%）

### 算法
```python
def assess_risk():
    # 1. 当前回撤
    total_pnl = get_total_pnl()  # 从paper_trades计算
    current_drawdown = total_pnl / 100000  # 假设初始$100K
    
    # 2. 风险预算
    max_drawdown = 0.10  # Constitution Rule 1
    remaining_budget = max_drawdown - abs(current_drawdown)
    
    # 3. 仓位计算
    if remaining_budget <= 0:
        return {'action': 'STOP_TRADING', 'reason': '回撤已达上限'}
    
    # Kelly Criterion简化版
    win_rate = get_win_rate()
    avg_win = get_avg_win_pct()
    avg_loss = get_avg_loss_pct()
    kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
    position_size = min(kelly * 0.5, remaining_budget * 10000)  # 半Kelly
    
    # 4. 极端事件检测
    vix = get_vix()
    warnings = []
    if vix > 30:
        warnings.append('VIX>30，建议减仓')
    if get_consecutive_losses() >= 3:
        warnings.append('连续3笔亏损，建议暂停')
    
    return {
        'current_drawdown': current_drawdown,
        'remaining_budget': remaining_budget,
        'position_size': position_size,
        'warnings': warnings
    }
```

### 执行频率
- 盘中每5分钟更新1次
- 每次开仓前必须检查

---

## 4. Historian Similarity Engine

### 功能
搜索历史相似场景，提供历史结果参考

### 输入数据
- 当前市场状态：板块、涨幅、Volume Ratio、RVOL、RSI
- 历史数据：TimescaleDB（10年+，1300万行）

### 算法
```python
def search_similar(stock, n_results=5):
    current = get_current_features(stock)
    
    # 1. 从数据库查询历史数据
    historical = query_timescaledb("""
        SELECT date, change_pct, volume_ratio, rvol, rsi, sector, return_1d, return_5d
        FROM prices
        WHERE ticker = %s
        ORDER BY date DESC
    """, (stock,))
    
    # 2. 多维度相似度计算（欧氏距离，免费）
    similarities = []
    for h in historical:
        dist = euclidean_distance(
            [current['change_pct'], current['volume_ratio'], current['rvol'], current['rsi']],
            [h['change_pct'], h['volume_ratio'], h['rvol'], h['rsi']]
        )
        similarity = 1 / (1 + dist)  # 转换为0-1
        similarities.append({
            'date': h['date'],
            'similarity': similarity,
            'return_1d': h['return_1d'],
            'return_5d': h['return_5d'],
            'success': h['return_1d'] > 0
        })
    
    # 3. 排序取Top N
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    top_n = similarities[:n_results]
    
    # 4. 统计
    success_rate = sum(1 for s in top_n if s['success']) / len(top_n)
    avg_return = sum(s['return_1d'] for s in top_n) / len(top_n)
    
    return {
        'scenarios': top_n,
        'success_rate': success_rate,
        'avg_return': avg_return,
        'confidence': max(s['similarity'] for s in top_n)
    }
```

### 性能
- 1300万行数据，向量化计算 < 1秒
- 不需要GPU，CPU足够

---

## 5. Critic Logic Checker

### 功能
审查每个Decision的逻辑完整性

### 输入
- Bull/Bear Team的输出
- Meta Brain的Final Decision

### 算法（Hermes 70B本地，免费）
```python
def critic_review(decision):
    prompt = f"""
    你是一个严格的批评者。审查以下投资决策：
    
    决策：{decision['action']} {decision['stock']}
    理由：{decision['reasoning']}
    信心：{decision['confidence']}
    
    必须回答三个问题：
    1. 为什么？（决策的逻辑是什么？）
    2. 最大的风险？（最可能错的地方？）
    3. 最大的反例？（有没有相反的证据？）
    
    如果逻辑不完整，返回FAIL。
    如果逻辑完整，返回PASS。
    
    格式：
    verdict: PASS/FAIL
    why: ...
    biggest_risk: ...
    biggest_counter_example: ...
    """
    
    response = hermes_70b(prompt)  # 本地，免费
    return parse_critic_response(response)
```

### 约束
- 每次Decision必须经过Critic审查
- FAIL → Decision不通过
- 审查结果记录到aiic_decisions表

---

## 6. Auditor Reconciliation

### 功能
每日收盘后自动审计：Prediction vs Reality

### 输入
- aiic_decisions表（今日预测）
- paper_trades表（实际结果）

### 算法（纯Python，免费）
```python
def daily_audit():
    today = get_today()
    
    # 1. 获取今日预测
    predictions = query_db("""
        SELECT * FROM aiic_decisions WHERE date = %s
    """, (today,))
    
    # 2. 获取实际结果
    actuals = query_db("""
        SELECT * FROM paper_trades WHERE trade_date = %s AND status = 'CLOSED'
    """, (today,))
    
    # 3. 对比
    audit_results = []
    for pred in predictions:
        actual = find_matching_actual(pred, actuals)
        if actual:
            diff = actual['pnl_pct'] - pred['expected_return']
            audit_results.append({
                'stock': pred['stock'],
                'predicted': pred['expected_return'],
                'actual': actual['pnl_pct'],
                'difference': diff,
                'reason': analyze_reason(pred, actual),  # Hermes本地
                'responsible': identify_responsible(pred, actual)
            })
    
    # 4. 统计
    accuracy = sum(1 for r in audit_results if r['difference'] < 5) / len(audit_results)
    
    # 5. 记录到learning_ledger
    for r in audit_results:
        insert_learning_ledger(r)
    
    return {'results': audit_results, 'accuracy': accuracy}
```

### 执行频率
- 每日收盘后自动执行（US: 1:30 PM PT, CN: 12:30 AM PT）

---

## 7. Coach Performance Analyzer

### 功能
分析每个Agent的表现，给出改进建议

### 输入
- agent_states表（每个Agent的KPI）
- learning_ledger表（历史学习记录）

### 算法
```python
def coach_analysis():
    agents = get_all_agent_states()
    recommendations = []
    
    for agent in agents:
        # 1. 趋势分析
        recent_10 = get_recent_accuracy(agent['name'], 10)
        recent_100 = get_recent_accuracy(agent['name'], 100)
        
        # 2. 问题检测
        if recent_10 < recent_100 * 0.8:  # 下降20%
            issue = f"最近10次准确率{recent_10:.0%}，低于100次平均{recent_100:.0%}"
            
            # 3. 分析原因（Hermes本地）
            reason = hermes_analyze(agent['name'], recent_10)
            
            # 4. 生成建议
            recommendation = {
                'agent': agent['name'],
                'issue': issue,
                'reason': reason,
                'suggestion': generate_suggestion(agent, reason),
                'priority': 'HIGH' if recent_10 < 0.5 else 'MEDIUM'
            }
            recommendations.append(recommendation)
    
    return recommendations
```

### 执行频率
- 每日收盘后执行1次

---

## 8. Learning Engine (Offline)

### 功能
收盘后离线学习，生成改进提案

### 约束
- **盘中禁止学习**（Constitution Rule 5）
- 只在收盘后执行

### 算法
```python
def offline_learning():
    # 1. Replay今日交易
    today_trades = get_today_trades()
    
    # 2. 诊断
    diagnosis = diagnose(today_trades)  # Hermes本地
    
    # 3. 生成假设
    hypotheses = generate_hypotheses(diagnosis)  # Hermes本地
    
    # 4. 回测验证
    for h in hypotheses:
        backtest_result = backtest(h)  # Python，免费
        
        if backtest_result['win_rate'] > 0.55:
            # 5. 生成提案
            proposal = {
                'hypothesis': h,
                'expected_impact': backtest_result,
                'evidence': diagnosis,
                'rollback_plan': generate_rollback(h)
            }
            
            # 6. 提交EC审批
            submit_to_ec(proposal)
    
    # 7. 记录到learning_ledger
    record_learning(diagnosis, hypotheses)
```

### 执行频率
- US收盘后：1:30 PM PT
- CN收盘后：12:30 AM PT

---

## 9. Evolution Proposal Generator

### 功能
自动发现模式，提出新Agent/策略建议

### 算法
```python
def generate_evolution_proposals():
    # 1. 分析各Agent的价值贡献
    agent_contributions = analyze_contributions()
    
    # 2. 发现模式
    patterns = discover_patterns(agent_contributions)
    # 例如："Option Flow相关Agent价值越来越大"
    
    # 3. 生成提案（Hermes本地）
    for pattern in patterns:
        if pattern['confidence'] > 0.8:
            proposal = hermes_generate_proposal(pattern)
            
            # 4. 提交EC
            submit_to_ec(proposal)
```

### 执行频率
- 每周执行1次（周末）

---

## 10. Constitution Enforcement Engine

### 功能
实时检查所有决策是否违反Constitution

### 算法（纯Python，免费）
```python
def check_constitution(decision):
    violations = []
    
    # Rule 1: 最大回撤10%
    if get_current_drawdown() > 0.10:
        violations.append('Rule 1: 回撤超过10%')
    
    # Rule 3: 学习必须可Rollback
    if decision['type'] == 'learning' and not decision.get('rollback_plan'):
        violations.append('Rule 3: 学习缺少Rollback Plan')
    
    # Rule 5: 盘中禁止自动调参
    if is_trading_hours() and decision['type'] == 'parameter_change':
        violations.append('Rule 5: 盘中禁止调参')
    
    # Rule 6: 进化必须EC审批
    if decision['type'] == 'evolution' and not decision.get('ec_approved'):
        violations.append('Rule 6: 进化未经EC审批')
    
    if violations:
        # 记录违规
        record_violation(violations)
        return {'allowed': False, 'violations': violations}
    
    return {'allowed': True, 'violations': []}
```

### 执行频率
- 每次决策前自动检查

---

## 附录：资源使用总结

| 功能 | 实现方式 | 成本 |
|------|----------|------|
| Market Regime Detection | Python + yfinance | 免费 |
| Bull/Bear Reasoning | Python + Hermes 70B | 免费 |
| Risk Assessment | Python | 免费 |
| Historian Similarity | Python + TimescaleDB | 免费 |
| Critic Logic Checker | Hermes 70B | 免费 |
| Auditor Reconciliation | Python + Hermes 70B | 免费 |
| Coach Performance | Python + Hermes 70B | 免费 |
| Learning Engine | Python + Hermes 70B | 免费 |
| Evolution Proposal | Hermes 70B | 免费 |
| Constitution Enforcement | Python | 免费 |

**总计：10个核心功能，全部免费（本地资源）**

---

*Document Version: 1.0 | Last Updated: 2026-07-22 | Author: Alca | Reviewer: Pending (Hao)*
