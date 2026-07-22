# NSPS API Specification v1.0

> **Agent间通信接口：数据格式、接口定义、约束**

Version: 1.0 | Created: 2026-07-22 | Status: Draft

---

## 1. 设计原则

1. **松耦合**：Agent之间通过TimescaleDB传递数据，不直接调用
2. **可审计**：所有通信记录到aiic_decisions表
3. **标准化**：统一YAML格式输出
4. **幂等性**：相同输入产生相同输出
5. **本地优先**：所有接口优先使用本地资源（Hermes 70B + Python）

---

## 2. 通用数据格式

### 2.1 Agent输出标准格式

```yaml
# 所有Agent输出必须包含以下字段
agent_output:
  agent_name: "Bull Team"          # Agent名称
  version: "1.2.0"                 # Agent版本
  timestamp: "2026-07-22T10:00:00" # ISO 8601
  input_summary:                   # 输入摘要
    stocks_analyzed: 50
    data_sources: ["prices", "sector_flow", "news"]
  output:                          # 具体输出（每个Agent不同）
    ...
  confidence: 0.85                 # 0-1
  evidence:                        # 数据支撑
    - type: "capital_flow"
      value: "+$50M"
    - type: "news_sentiment"
      value: 0.9
  reasoning: "逻辑说明"            # 为什么得出这个结论
  constraints_check:               # Constitution检查
    passed: true
    violations: []
```

### 2.2 错误格式

```yaml
agent_error:
  agent_name: "Bull Team"
  timestamp: "2026-07-22T10:00:00"
  error_type: "DATA_MISSING"       # DATA_MISSING | MODEL_ERROR | DB_ERROR | TIMEOUT
  error_message: "无法获取NVDA资金流数据"
  stack_trace: "..."
  recovery_action: "使用上次缓存数据"
```

---

## 3. Agent间通信接口

### 3.1 Market Regime Detector → All Agents

```yaml
# 接口名: regime_signal
# 发布者: Meta Brain
# 订阅者: Bull Team, Bear Team, Risk Team, Historian
# 频率: 开盘前1次 + 盘中每30分钟

regime_signal:
  timestamp: "2026-07-22T09:30:00"
  regime: "TREND"                  # TREND | RANGE | EVENT | RISK_OFF
  confidence: 0.85
  indicators:
    spy_ma20_direction: "UP"
    vix: 18.5
    up_sectors: 8
    down_sectors: 3
    market_breadth: 0.73
  weight_adjustment:               # 动态权重调整
    bull: 0.4
    bear: 0.2
    risk: 0.2
    historian: 0.2
```

### 3.2 Bull Team → Meta Brain

```yaml
# 接口名: bull_reasoning
# 发布者: Bull Team
# 订阅者: Meta Brain, Critic Agent
# 频率: 每次选股时

bull_reasoning:
  timestamp: "2026-07-22T09:30:00"
  stock: "NVDA"
  market: "us"
  reasons:
    - "AI板块资金流入+15%"
    - "新闻利好，新产品发布"
    - "板块效应强，5只异动"
  evidence:
    capital_flow: 50000000         # 美元
    news_sentiment: 0.9
    sector_strength: 5
    rsi: 65
    volume_ratio: 2.1
  confidence: 0.85
  historian_ref:                   # Historian参考
    similar_date: "2024-03-15"
    similarity: 0.92
    historical_result: "+15%"
```

### 3.3 Bear Team → Meta Brain

```yaml
# 接口名: bear_reasoning
# 发布者: Bear Team
# 订阅者: Meta Brain, Critic Agent
# 频率: 每次选股时

bear_reasoning:
  timestamp: "2026-07-22T09:30:00"
  stock: "NVDA"
  market: "us"
  risks:
    - "RSI=78，超买区域"
    - "接近52周高点"
    - "历史相似场景失败率20%"
  evidence:
    rsi: 78
    price_vs_52w_high: 0.97
    historical_failure_rate: 0.2
    macro_risk: 0.3
  confidence: 0.75
```

### 3.4 Risk Team → Meta Brain

```yaml
# 接口名: risk_assessment
# 发布者: Risk Team
# 订阅者: Meta Brain
# 频率: 盘中每5分钟

risk_assessment:
  timestamp: "2026-07-22T10:00:00"
  portfolio:
    total_value: 100450
    current_drawdown: 0.035        # 3.5%
    max_allowed_drawdown: 0.10     # Constitution Rule 1
    remaining_budget: 0.065
  position_recommendation:
    stock: "NVDA"
    max_position: 2000
    recommended_position: 1500
    reason: "回撤3.5%，还有6.5%预算"
  warnings:
    - level: "INFO"
      message: "VIX=18.5，正常范围"
    - level: "WARNING"
      message: "连续2笔亏损，注意风险"
  constitution_check:
    passed: true
    violations: []
```

### 3.5 Meta Brain → Critic Agent

```yaml
# 接口名: final_decision
# 发布者: Meta Brain
# 订阅者: Critic Agent, Auditor Agent
# 频率: 每次决策

final_decision:
  timestamp: "2026-07-22T09:35:00"
  decision_type: "BUY"             # BUY | SELL | HOLD
  stock: "NVDA"
  market: "us"
  position_size: 1500
  confidence: 0.82
  reasoning: "Trend市场，Bull权重高，历史相似场景成功率80%"
  bull_summary: "资金流入+新闻利好+板块效应"
  bear_summary: "RSI超买+接近高点"
  risk_summary: "回撤3.5%，预算充足"
  historian_summary: "相似度92%，历史+15%"
  weight_used:
    bull: 0.4
    bear: 0.2
    risk: 0.2
    historian: 0.2
```

### 3.6 Critic Agent → Meta Brain

```yaml
# 接口名: critic_review
# 发布者: Critic Agent
# 订阅者: Meta Brain, Auditor Agent
# 频率: 每次Decision后

critic_review:
  timestamp: "2026-07-22T09:36:00"
  decision_ref: "final_decision_20260722_093500"
  verdict: "PASS"                  # PASS | FAIL
  questions:
    why: "AI板块资金流入+15%，新闻利好，板块效应强"
    biggest_risk: "RSI=78超买，接近52周高点"
    biggest_counter_example: "2024-03-15相似场景后回调8%"
  logic_completeness: 0.9          # 逻辑完整度
  missing_factors: []              # 遗漏因素
  recommendation: "逻辑完整，风险已识别，建议执行"
```

### 3.7 Auditor Agent → Learning Ledger

```yaml
# 接口名: audit_result
# 发布者: Auditor Agent
# 订阅者: Learning Ledger, Coach Agent
# 频率: 每日收盘后

audit_result:
  timestamp: "2026-07-22T14:00:00"
  date: "2026-07-22"
  predictions:
    - stock: "NVDA"
      predicted_return: 5.0
      actual_return: 3.2
      difference: -1.8
      reason: "大盘尾盘下跌拖累"
      responsible_agent: "Risk Team"
      lesson: "应增加尾盘风险预警"
    - stock: "TSLA"
      predicted_return: 4.0
      actual_return: -2.5
      difference: -6.5
      reason: "财报不及预期"
      responsible_agent: "Bear Team"
      lesson: "Bear Team应更早识别财报风险"
  summary:
    total_predictions: 5
    correct: 3
    incorrect: 2
    accuracy: 60%
    avg_error: 3.2%
  recommendations:
    - "Risk Team应增加尾盘风险预警"
    - "Bear Team应关注财报日历"
```

### 3.8 Coach Agent → Evolution Council

```yaml
# 接口名: coach_recommendation
# 发布者: Coach Agent
# 订阅者: Evolution Council
# 频率: 每日收盘后

coach_recommendation:
  timestamp: "2026-07-22T14:30:00"
  agent: "News Agent"
  current_version: "2.1.8"
  performance:
    accuracy_10: 0.70
    accuracy_100: 0.88
    trend: "DECLINING"
  issue: "最近10次准确率下降到70%，低于100次平均88%"
  root_cause: "Macro类预测连续失败"
  recommendation:
    action: "REDUCE_MACRO_WEIGHT"
    from: 0.32
    to: 0.20
    evidence: "Macro最近10次准确率40%"
    expected_improvement: "+5%准确率"
    rollback_condition: "如果调整后胜率<50%，自动回滚"
  priority: "HIGH"
```

### 3.9 Evolution Proposal

```yaml
# 接口名: evolution_proposal
# 发布者: 任何Agent 或 Coach Agent
# 订阅者: Evolution Council
# 频率: 按需

evolution_proposal:
  timestamp: "2026-07-22T15:00:00"
  proposer: "News Agent"
  proposal_type: "NEW_AGENT"       # NEW_AGENT | NEW_STRATEGY | PARAM_CHANGE
  title: "增加Option Agent"
  hypothesis: |
    IF 增加Option Agent分析Option Flow
    THEN Leader Accuracy提高5%
    BECAUSE Option Flow提前反映机构意图
    MEASURED BY 过去1年胜率对比
  evidence:
    - "Option Flow与股价相关性0.7"
    - "顶级基金（Citadel）大量使用Option数据"
  expected_impact:
    metric: "Leader Accuracy"
    current: 58%
    expected: 63%
    improvement: "+5%"
  implementation_plan:
    - "Layer 1: UT/SIT/RT (1天)"
    - "Layer 2: Backtest 1年 (2天)"
    - "Layer 3: Paper Trading 30天"
    - "Layer 4: Production 小仓位"
  rollback_plan: "如果Paper Trading胜率<50%，自动拒绝"
  cost: 0                          # 本地资源，免费
  ec_status: "PENDING"
```

---

## 4. 数据库接口

### 4.1 写入接口

```python
# 所有写入必须通过统一接口
def write_to_db(table: str, data: dict) -> int:
    """
    写入数据到TimescaleDB
    - 自动检查Constitution
    - 自动记录审计日志
    - 返回record_id
    """
    # 1. Constitution检查
    check = check_constitution(data)
    if not check['allowed']:
        record_violation(check['violations'])
        raise ConstitutionViolation(check['violations'])
    
    # 2. 写入数据
    record_id = insert(table, data)
    
    # 3. 记录审计日志
    insert('audit_log', {
        'table': table,
        'record_id': record_id,
        'action': 'INSERT',
        'timestamp': now()
    })
    
    return record_id
```

### 4.2 读取接口

```python
# 所有读取必须通过统一接口
def read_from_db(table: str, filters: dict = None) -> list:
    """
    读取数据从TimescaleDB
    - 自动缓存常用数据
    - 自动记录访问日志
    """
    # 1. 检查缓存
    cache_key = f"{table}_{hash_filters(filters)}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    # 2. 查询数据库
    results = query(table, filters)
    
    # 3. 更新缓存
    set_cache(cache_key, results, ttl=300)
    
    return results
```

---

## 5. 约束

1. 所有Agent输出必须包含`confidence`字段
2. 所有Agent输出必须包含`evidence`字段
3. 所有写入必须通过Constitution检查
4. 所有通信必须记录到audit_log
5. Agent之间不直接调用，通过数据库传递
6. 所有接口优先使用本地资源

---

*Document Version: 1.0 | Last Updated: 2026-07-22 | Author: Alca*
