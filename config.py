# 环境变量加载
from dotenv import load_dotenv
import os
import urllib3
from pathlib import Path

# 加载 .env 文件
load_dotenv()

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# API 基础配置
BASE_URL = os.getenv("BASE_URL")
ORIGIN = os.getenv("ORIGIN")

# 敏感信息配置（从环境变量读取）
TRADE_EMAIL = os.getenv("TRADE_EMAIL")
TRADE_PASSWORD = os.getenv("TRADE_PASSWORD")
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL")

# UA
USER_AGENT = os.getenv("USER_AGENT")

useragent = USER_AGENT

# 通用请求头
COMMON_HEADERS = {
    "User-Agent": useragent,
    "Accept": "application/json, text/plain, */*",
    "sec-ch-ua-platform": '"Android"',
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="143", "Google Chrome";v="143"',
    "app-analog": "false",
    "sec-ch-ua-mobile": "?1",
    "set-aws": "true",
    "set-language": "TRADITIONAL_CHINESE",
    "content-type": "application/json;charset=UTF-8",
    "origin": ORIGIN,
    "referer": f"{ORIGIN}/",
    "accept-language": "zh-CN,zh;q=0.9",
    "priority": "u=1, i",
}


def build_headers(token: str = None) -> dict:
    """
    构建请求头

    Args:
        token: 可选的认证 token

    Returns:
        dict: 完整的请求头
    """
    headers = COMMON_HEADERS.copy()
    if token:
        headers["app-login-token"] = token
    return headers

ROOT_PATH = Path(__file__).parent
DATA_PATH = ROOT_PATH / "data"

if not DATA_PATH.exists():
    DATA_PATH.mkdir(exist_ok=True)

# 定时启动配置
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME")
ADVANCE_MINUTES = int(os.getenv("ADVANCE_MINUTES"))
