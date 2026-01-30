"""
工具函数模块
"""
import secrets
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

CHINA_TZ = ZoneInfo("Asia/Shanghai")


def wait_until_scheduled(schedule_time: str, advance_minutes: int) -> None:
    """
    等待到指定时间前 X 分钟

    Args:
        schedule_time: 目标时间，格式 "HH:MM"
        advance_minutes: 提前启动的分钟数
    """
    target_hour, target_minute = map(int, schedule_time.split(':'))

    now = datetime.now(tz=CHINA_TZ)
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    target = target - timedelta(minutes=advance_minutes)

    # 如果已经过了今天的启动时间，则等到明天
    if now >= target:
        target = target + timedelta(days=1)

    # 添加1~10秒的随机抖动，更像人类行为
    jitter = secrets.SystemRandom().uniform(1, 10)
    target = target + timedelta(seconds=jitter)

    wait_seconds = (target - now).total_seconds()

    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"计划启动时间: {target.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"等待 {wait_seconds / 60:.2f} 分钟后开始...")

    time.sleep(wait_seconds)
    print("开始执行 watch_and_follow...")
