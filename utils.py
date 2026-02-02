"""
工具函数模块
"""
import secrets
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import json
import httpx

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

    # 如果已经过了今天的启动时间，直接开始执行不等待
    if now >= target:
        print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"目标时间 {schedule_time} (提前{advance_minutes}分钟) 已过，立即开始执行...")
        return

    # 添加1~10秒的随机抖动，更像人类行为
    jitter = secrets.SystemRandom().uniform(1, 10)
    target = target + timedelta(seconds=jitter)

    wait_seconds = (target - now).total_seconds()

    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"计划启动时间: {target.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"等待 {wait_seconds / 60:.2f} 分钟后开始...")

    time.sleep(wait_seconds)
    print("开始执行 watch_and_follow...")

def parse_ip_address(
        ip: str,
        timeout: int = 10,
) -> dict | None:
    """
    查询 IP 地址的地理位置信息

    Args:
        ip: 要查询的 IP 地址（支持 IPv4 和 IPv6）
        timeout: 请求超时时间（秒），默认 10 秒

    Returns:
        包含地理位置信息的字典，结构如下：
        {
            "continent_code": "<continent_code>",    # 大洲代码
            "country": "<country>",                  # 国家
            "country_code": "<country_code>",        # 国家代码
            "city": "<city>",                        # 城市
            "isp": "<isp>",                          # 运营商
            "organization": "<organization>",        # 组织
            "asn": <asn>,                            # ASN 号
            "asn_organization": "<asn_organization>", # ASN 组织
            "latitude": <latitude>,                  # 纬度
            "longitude": <longitude>,                # 经度
            "timezone": "<timezone>",                # 时区
            "offset": <offset>,                      # UTC 偏移（秒）
            "postal_code": "<postal_code>",          # 邮编
            "ip": "<ip>"                             # 查询的 IP
        }
        查询失败时返回 None

    Example:
        >>> result = parse_ip_address("<your_ip_address>")
        >>> print(result.get('country'))
        'Singapore'
    """
    if not ip:
        print("错误：未输入 IP 地址")
        return None

    BASE_URL = "https://api.ip.sb/geoip/"
    url = f"{BASE_URL}{ip}"

    print(f"查询 IP 地理位置: {url}")

    try:
        response = httpx.get(
            url=url,
            timeout=timeout,
            follow_redirects=True,
        )
        response.raise_for_status()  # 检查 HTTP 错误状态码
        return response.json()

    except httpx.ConnectError:
        print("错误：网络连接失败，请检查网络设置")
    except httpx.TimeoutException:
        print(f"错误：请求超时（超过 {timeout} 秒）")
    except httpx.HTTPStatusError as e:
        print(f"错误：HTTP 状态码异常 - {e.response.status_code}")
    except httpx.JSONDecodeError:
        print("错误：响应数据解析失败，API 可能返回了非 JSON 格式")
    except Exception as e:
        print(f"错误：未知异常 - {type(e).__name__}: {e}")

    return None

if __name__ == "__main__":
    # 示例：查询 IP 地址地理位置
    result = parse_ip_address("2406:da18:1d9a:c37c:e94f:9129:1753:9283")
    if result:
        organization = result.get("organization")
        country = result.get("country")
        print(f"organization:{organization}\ncountry:{country}")
        print(json.dumps(result, indent=2, ensure_ascii=False))