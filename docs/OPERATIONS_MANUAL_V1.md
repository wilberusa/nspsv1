# NSPS Operations Manual v1.0

> **运维手册：数据库、Cron、故障排查、备份恢复**

Version: 1.0 | Created: 2026-07-22 | Status: Draft

---

## 目录

1. [系统架构概览](#1-系统架构概览)
2. [数据库运维](#2-数据库运维)
3. [Cron Job管理](#3-cron-job管理)
4. [日志管理](#4-日志管理)
5. [故障排查](#5-故障排查)
6. [备份与恢复](#6-备份与恢复)
7. [性能优化](#7-性能优化)
8. [安全运维](#8-安全运维)

---

## 1. 系统架构概览

```
Mac Studio (OC-1)
├── TimescaleDB Master (port 5432)
│   ├── prices (US, 700万行)
│   ├── prices_cn (CN, 650万行)
│   ├── paper_trades
│   ├── agent_states
│   ├── learning_ledger
│   ├── evolution_proposals
│   ├── aiic_decisions
│   └── constitution_violations
│
├── NGAIQOS Scripts
│   ├── self_monitoring.py (每小时)
│   ├── daily_pnl_report.py (每日收盘后)
│   ├── paper_trade_engine.py (盘前/收盘)
│   ├── bull_team.py (盘前)
│   ├── bear_team.py (盘前)
│   ├── risk_team.py (盘中每5分钟)
│   ├── meta_brain.py (盘前+盘中每30分钟)
│   ├── critic_agent.py (每次决策后)
│   ├── auditor_agent.py (每日收盘后)
│   ├── coach_agent.py (每日收盘后)
│   ├── self_improvement.py (每周)
│   └── self_evolution.py (每周)
│
└── NAS Standby (port 15432)
    └── 实时复制Master数据
```

---

## 2. 数据库运维

### 2.1 连接命令

```bash
# Master
docker exec sps-timescaledb-master psql -U saps -d sps

# Standby (NAS)
sshpass -f ~/.sp_nas_pw ssh hansusa@dxp4800plushans \
  "docker exec sps-timescaledb psql -U saps -d sps"
```

### 2.2 常用查询

```sql
-- 检查数据量
SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;

-- 检查复制状态
SELECT * FROM pg_stat_replication;

-- 检查WAL日志大小
SELECT pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0'));

-- 检查磁盘使用
SELECT pg_size_pretty(pg_database_size('sps'));

-- 检查表大小
SELECT relname, pg_size_pretty(pg_total_relation_size(oid)) 
FROM pg_class 
WHERE relkind = 'r' 
ORDER BY pg_total_relation_size(oid) DESC 
LIMIT 10;
```

### 2.3 数据更新Cron

```bash
# CN数据更新 (每日00:30 PT = 北京时间15:30)
30 0 * * 2-6 update_cn_prices.py

# US数据更新 (每日01:00 PT)
0 1 * * 2-6 update_us_prices.py

# 同步到TimescaleDB (每日00:50 PT)
50 0 * * 2-6 sync_to_timescale.py
```

### 2.4 数据验证

```bash
# 验证数据完整性
python3 projects/sps-v3/scripts/validate_data_integrity.py

# 检查今日数据
docker exec sps-timescaledb-master psql -U saps -d sps -c \
  "SELECT COUNT(*) FROM prices WHERE date = CURRENT_DATE;"
```

---

## 3. Cron Job管理

### 3.1 查看所有Cron Jobs

```bash
crontab -l
```

### 3.2 NGAIQOS相关Cron Jobs

```bash
# Self-Monitoring (每小时)
0 * * * * self_monitoring.py

# US盘前扫描 (6:00 AM PT, 周一到周五)
0 6 * * 1-5 us_premarket_scanner_v2.py

# CN盘前报告 (6:30 PM PT, 周日到周四)
30 18 * * 0-4 cn_premarket_report.py

# 每日盈亏报告 (US收盘后1:30 PM PT)
30 13 * * 1-5 daily_pnl_report.py --market us

# 每日盈亏报告 (CN收盘后12:30 AM PT)
30 0 * * 2-6 daily_pnl_report.py --market cn

# Auditor Agent (每日收盘后2:00 PM PT)
0 14 * * 1-5 auditor_agent.py

# Coach Agent (每日收盘后2:30 PM PT)
30 14 * * 1-5 coach_agent.py

# Self-Improvement (每周日10:00 AM PT)
0 10 * * 0 self_improvement.py

# Self-Evolution (每周日11:00 AM PT)
0 11 * * 0 self_evolution.py
```

### 3.3 Cron Job故障排查

```bash
# 查看日志
tail -100 logs/self_monitoring.log

# 检查最近执行状态
grep "ERROR" logs/*.log | tail -20

# 手动触发测试
python3 projects/ngaiqos/scripts/self_monitoring.py

# 检查Cron是否运行
ps aux | grep cron
```

---

## 4. 日志管理

### 4.1 日志文件位置

```
logs/
├── self_monitoring.log          # 每小时系统检查
├── self_monitoring_cron.log     # Cron触发的检查
├── paper_trade_engine.log       # Paper Trading记录
├── daily_pnl_report.log         # 每日盈亏报告
├── bull_team.log                # Bull Team分析
├── bear_team.log                # Bear Team分析
├── risk_team.log                # Risk Team评估
├── meta_brain.log               # Meta Brain决策
├── critic_agent.log             # Critic审查
├── auditor_agent.log            # Auditor审计
├── coach_agent.log              # Coach建议
├── self_improvement.log         # 自动调参
├── self_evolution.log           # 进化提案
└── self_monitoring_report_YYYY-MM-DD.log  # 每日报告
```

### 4.2 日志清理

```bash
# 清理30天前的日志
find logs/ -name "*.log" -mtime +30 -delete

# 压缩7天前的日志
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
```

### 4.3 日志搜索

```bash
# 搜索错误
grep -r "ERROR" logs/ | tail -20

# 搜索特定Agent
grep "Bull Team" logs/bull_team.log | tail -10

# 搜索特定日期
grep "2026-07-22" logs/*.log
```

---

## 5. 故障排查

### 5.1 数据库连接失败

```bash
# 检查Docker容器
docker ps | grep timescaledb

# 重启容器
docker restart sps-timescaledb-master

# 检查端口
lsof -i :5432
```

### 5.2 数据未更新

```bash
# 检查最新数据日期
docker exec sps-timescaledb-master psql -U saps -d sps -c \
  "SELECT MAX(date) FROM prices;"

# 检查Cron日志
tail -50 logs/cn-price-update.log

# 手动更新
python3 projects/sps-v3/scripts/update_cn_prices.py
```

### 5.3 Paper Trading未记录

```bash
# 检查paper_trades表
docker exec sps-timescaledb-master psql -U saps -d sps -c \
  "SELECT * FROM paper_trades WHERE trade_date = CURRENT_DATE;"

# 检查日志
tail -50 logs/paper_trade_engine.log

# 手动测试
python3 projects/sps-v3/scripts/paper_trade_engine.py \
  --action entry --market us --symbol TEST --price 100
```

### 5.4 Telegram未收到报告

```bash
# 检查报告是否生成
tail -20 logs/daily_pnl_report.log

# 检查Telegram连接
openclaw logs --lines 50 | grep telegram

# 手动发送
python3 projects/ngaiqos/scripts/daily_pnl_report.py --send-telegram
```

### 5.5 Constitution违规

```bash
# 查看违规记录
docker exec sps-timescaledb-master psql -U saps -d sps -c \
  "SELECT * FROM constitution_violations ORDER BY time DESC LIMIT 10;"

# 检查违规原因
# 通常是：回撤超限、盘中调参、未经EC审批
```

---

## 6. 备份与恢复

### 6.1 自动备份

```bash
# Master → Standby 实时复制（已配置）
# WAL日志自动归档

# 每日逻辑备份（凌晨2:00 AM PT）
0 2 * * * pg_dump -U saps -h localhost sps > backups/sps_$(date +%Y%m%d).sql
```

### 6.2 手动备份

```bash
# 完整备份
pg_dump -U saps -h localhost -p 5432 sps > backups/sps_full_$(date +%Y%m%d).sql

# 单表备份
pg_dump -U saps -h localhost -p 5432 -t paper_trades sps > backups/paper_trades.sql

# 压缩备份
pg_dump -U saps -h localhost -p 5432 -Fc sps > backups/sps_full_$(date +%Y%m%d).dump
```

### 6.3 恢复

```bash
# 从逻辑备份恢复
psql -U saps -h localhost -p 5432 sps < backups/sps_20260722.sql

# 从压缩备份恢复
pg_restore -U saps -h localhost -p 5432 -d sps backups/sps_full_20260722.dump

# 从Standby恢复（如果Master挂了）
# 1. 停止Master
docker stop sps-timescaledb-master

# 2. 提升Standby为Master
ssh hansusa@dxp4800plushans \
  "docker exec sps-timescaledb psql -U saps -d sps -c 'SELECT pg_promote();'"

# 3. 更新连接配置
```

---

## 7. 性能优化

### 7.1 数据库优化

```sql
-- 分析慢查询
EXPLAIN ANALYZE SELECT * FROM prices WHERE date = '2026-07-22';

-- 重建索引
REINDEX TABLE prices;
REINDEX TABLE prices_cn;

-- 清理死元组
VACUUM ANALYZE prices;
VACUUM ANALYZE prices_cn;

-- 检查索引使用
SELECT indexrelname, idx_scan FROM pg_stat_user_indexes ORDER BY idx_scan;
```

### 7.2 脚本优化

```bash
# 使用多进程（已实现）
# update_cn_prices.py: ThreadPoolExecutor, 60 workers
# us_premarket_scanner_v2.py: ThreadPoolExecutor, 10 workers

# 使用向量化计算（已实现）
# pandas向量化 > 逐行循环

# 避免重复查询
# 缓存常用数据到内存
```

### 7.3 磁盘清理

```bash
# 检查磁盘使用
df -h /

# 清理旧备份
find backups/ -name "*.sql" -mtime +30 -delete

# 清理旧日志
find logs/ -name "*.log" -mtime +30 -delete

# 清理Docker
docker system prune -f
```

---

## 8. 安全运维

### 8.1 密码管理

```bash
# TimescaleDB密码
# 存储在: ~/.pgpass 或环境变量

# NAS密码
# 存储在: ~/.sp_nas_pw

# API密钥
# 存储在: ~/.zshrc (MX_APIKEY, etc.)
```

### 8.2 访问控制

```bash
# 检查数据库用户
docker exec sps-timescaledb-master psql -U saps -d sps -c "\du"

# 检查活跃连接
docker exec sps-timescaledb-master psql -U saps -d sps -c \
  "SELECT usename, application_name, state FROM pg_stat_activity;"
```

### 8.3 审计日志

```sql
-- 查看Constitution违规
SELECT * FROM constitution_violations ORDER BY time DESC;

-- 查看学习记录
SELECT * FROM learning_ledger ORDER BY time DESC LIMIT 20;

-- 查看进化提案
SELECT * FROM evolution_proposals ORDER BY time DESC;
```

---

## 附录：常用命令速查

```bash
# 数据库连接
docker exec sps-timescaledb-master psql -U saps -d sps

# 系统健康检查
python3 projects/ngaiqos/scripts/self_monitoring.py

# 数据验证
python3 projects/sps-v3/scripts/validate_data_integrity.py

# 查看Cron
crontab -l

# 查看日志
tail -50 logs/self_monitoring.log

# 搜索错误
grep -r "ERROR" logs/ | tail -20

# 手动更新数据
python3 projects/sps-v3/scripts/update_cn_prices.py
python3 projects/sps-v3/scripts/update_us_prices.py

# 备份
pg_dump -U saps -h localhost sps > backups/sps_$(date +%Y%m%d).sql
```

---

*Document Version: 1.0 | Last Updated: 2026-07-22 | Author: Alca*
