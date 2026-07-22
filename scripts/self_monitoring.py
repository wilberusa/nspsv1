#!/usr/bin/env python3
"""
Self-Monitoring Agent — NGAIQOS Phase 1
检查系统运行状态：哪些Agent正常？哪些异常？

检查项：
1. 数据库连接（TimescaleDB）
2. 最近cron job执行状态
3. Paper trading engine状态
4. 数据更新状态（今日是否有新数据）
5. 系统资源（磁盘、内存）
"""

import psycopg2
import sqlite3
import subprocess
import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/Users/hansusa/.openclaw/workspace/logs/self_monitoring.log')
    ]
)
logger = logging.getLogger(__name__)

# TimescaleDB连接
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'saps',
    'password': 'saps123',
    'dbname': 'sps'
}

PT_OFFSET = timedelta(hours=-7)
LOG_DIR = Path('/Users/hansusa/.openclaw/workspace/logs')


def check_timescaledb():
    """检查TimescaleDB连接和数据状态"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 检查prices表最新数据
        cur.execute("""
            SELECT MAX(date) as latest_date, COUNT(*) as total_rows
            FROM prices
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        row = cur.fetchone()
        latest_date = row[0]
        total_rows = row[1]
        
        # 检查paper_trades表
        cur.execute("""
            SELECT COUNT(*) as open_trades, 
                   COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_trades
            FROM paper_trades
            WHERE trade_date >= to_char(CURRENT_DATE - INTERVAL '7 days', 'YYYY-MM-DD')
        """)
        pt_row = cur.fetchone()
        
        conn.close()
        
        return {
            'status': 'OK',
            'latest_date': str(latest_date),
            'recent_rows': total_rows,
            'open_trades': pt_row[0],
            'closed_trades': pt_row[1]
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e)
        }


def check_cron_jobs():
    """检查最近cron job执行状态"""
    try:
        # 检查最近的日志文件
        log_files = [
            'sps-us-r1.log',
            'sps-us-r2.log', 
            'cn-premarket.log',
            'paper_trade_engine.log',
            'self_monitoring.log'
        ]
        
        results = {}
        for log_file in log_files:
            log_path = LOG_DIR / log_file
            if log_path.exists():
                # 检查最后修改时间
                mtime = os.path.getmtime(log_path)
                age_hours = (datetime.now().timestamp() - mtime) / 3600
                
                # 检查最后几行是否有错误
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    last_lines = lines[-10:] if len(lines) >= 10 else lines
                    has_error = any('ERROR' in line or 'Exception' in line for line in last_lines)
                
                results[log_file] = {
                    'age_hours': round(age_hours, 2),
                    'has_error': has_error,
                    'status': 'OK' if age_hours < 24 and not has_error else 'WARNING'
                }
            else:
                results[log_file] = {
                    'status': 'MISSING'
                }
        
        return {
            'status': 'OK',
            'jobs': results
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e)
        }


def check_data_freshness():
    """检查数据更新状态"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        today = datetime.now(timezone(PT_OFFSET)).strftime('%Y-%m-%d')
        
        # 检查US市场数据
        cur.execute("""
            SELECT COUNT(*) FROM prices WHERE date = %s
        """, (today,))
        us_count = cur.fetchone()[0]
        
        # 检查CN市场数据
        cur.execute("""
            SELECT COUNT(*) FROM prices_cn WHERE date = %s
        """, (today,))
        cn_count = cur.fetchone()[0]
        
        conn.close()
        
        return {
            'status': 'OK',
            'us_data_today': us_count,
            'cn_data_today': cn_count,
            'us_fresh': us_count > 0,
            'cn_fresh': cn_count > 0
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e)
        }


def check_system_resources():
    """检查系统资源"""
    try:
        # 磁盘使用
        disk_usage = subprocess.run(
            ['df', '-h', '/'],
            capture_output=True,
            text=True
        )
        disk_line = disk_usage.stdout.split('\n')[1]
        disk_pct = int(disk_line.split()[4].replace('%', ''))
        
        # 内存使用
        mem_usage = subprocess.run(
            ['vm_stat'],
            capture_output=True,
            text=True
        )
        
        return {
            'status': 'OK',
            'disk_usage_pct': disk_pct,
            'disk_warning': disk_pct > 80
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e)
        }


def generate_report():
    """生成Self-Monitoring报告"""
    now = datetime.now(timezone(PT_OFFSET)).isoformat()
    
    report = {
        'timestamp': now,
        'checks': {}
    }
    
    # 执行各项检查
    report['checks']['timescaledb'] = check_timescaledb()
    report['checks']['cron_jobs'] = check_cron_jobs()
    report['checks']['data_freshness'] = check_data_freshness()
    report['checks']['system_resources'] = check_system_resources()
    
    # 计算总体状态
    all_ok = all(
        check['status'] == 'OK' 
        for check in report['checks'].values()
    )
    
    report['overall_status'] = 'HEALTHY' if all_ok else 'WARNING'
    
    # 生成可读报告
    readable = []
    readable.append(f"🔍 Self-Monitoring Report — {now[:19]}")
    readable.append("")
    readable.append(f"总体状态: {'✅ HEALTHY' if all_ok else '⚠️ WARNING'}")
    readable.append("")
    
    # TimescaleDB
    tsdb = report['checks']['timescaledb']
    if tsdb['status'] == 'OK':
        readable.append(f"✅ TimescaleDB: 正常")
        readable.append(f"   最新数据: {tsdb['latest_date']}, 近7天: {tsdb['recent_rows']}行")
        readable.append(f"   Paper Trades: {tsdb['open_trades']} OPEN, {tsdb['closed_trades']} CLOSED")
    else:
        readable.append(f"❌ TimescaleDB: {tsdb['error']}")
    
    readable.append("")
    
    # Data Freshness
    freshness = report['checks']['data_freshness']
    if freshness['status'] == 'OK':
        readable.append(f"✅ 数据更新: 正常")
        readable.append(f"   US市场: {freshness['us_data_today']}条 ({'今日已更新' if freshness['us_fresh'] else '今日未更新'})")
        readable.append(f"   CN市场: {freshness['cn_data_today']}条 ({'今日已更新' if freshness['cn_fresh'] else '今日未更新'})")
    else:
        readable.append(f"❌ 数据更新: {freshness['error']}")
    
    readable.append("")
    
    # System Resources
    resources = report['checks']['system_resources']
    if resources['status'] == 'OK':
        disk_status = '⚠️' if resources['disk_warning'] else '✅'
        readable.append(f"{disk_status} 系统资源: 磁盘{resources['disk_usage_pct']}%")
    else:
        readable.append(f"❌ 系统资源: {resources['error']}")
    
    readable.append("")
    
    # Cron Jobs
    cron = report['checks']['cron_jobs']
    if cron['status'] == 'OK':
        readable.append(f"✅ Cron Jobs:")
        for job_name, job_status in cron['jobs'].items():
            if job_status['status'] == 'OK':
                readable.append(f"   • {job_name}: {job_status['age_hours']:.1f}h前, 无错误")
            elif job_status['status'] == 'WARNING':
                readable.append(f"   ⚠️ {job_name}: {job_status['age_hours']:.1f}h前, 有错误")
            else:
                readable.append(f"   ❌ {job_name}: 缺失")
    
    report_text = '\n'.join(readable)
    
    # 保存到日志
    log_path = LOG_DIR / f"self_monitoring_report_{now[:10]}.log"
    with open(log_path, 'w') as f:
        f.write(report_text)
        f.write('\n\n')
        f.write(json.dumps(report, indent=2, ensure_ascii=False))
    
    return report, report_text


if __name__ == '__main__':
    report, report_text = generate_report()
    print(report_text)
    
    # 如果有严重问题，返回非零退出码
    if report['overall_status'] != 'HEALTHY':
        exit(1)
