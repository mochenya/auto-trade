"""
用户相关 API - 使用会话复用的客户端
"""
import json
import config
from api_client import get_client


def post_login(email: str, password: str) -> str:
    """
    登录 API
    
    Args:
        email: 登录邮箱
        password: 登录密码
    
    Returns:
        str: 登录成功后的 token
    """
    client = get_client()
    
    payload = {
        "email": email,
        "password": password
    }
    
    result = client.post("/user/login", json_data=payload)
    
    if not result.get("resultCode"):
        raise Exception(f"Login failed: {result.get('errCodeDes', 'Unknown error')}")
    
    token = result["data"]
    
    # 设置 token 到客户端
    client.set_token(token)
    
    return token


def fetch_get_info() -> dict:
    """
    获取用户信息（使用客户端中的 token）
    
    Returns:
        dict: 用户信息数据
    """
    client = get_client()
    result = client.post("/user/get/info", json_data={})
    return result


def fetch_certification_status() -> dict:
    """
    获取认证状态（使用客户端中的 token）
    
    Returns:
        dict: 认证状态数据
    """
    client = get_client()
    result = client.post("/user/certification/status", json_data={})
    return result


if __name__ == "__main__":
    from funds import funds_overview, parse_balance, print_balance

    # 从配置读取登录信息
    if not config.TRADE_EMAIL or not config.TRADE_PASSWORD:
        raise ValueError("请在 .env 文件中设置 TRADE_EMAIL 和 TRADE_PASSWORD")

    token = post_login(email=config.TRADE_EMAIL, password=config.TRADE_PASSWORD)
    print(f"Token: {token}")
    
    # 获取并保存用户信息
    info_return = fetch_get_info()
    info_json = json.dumps(info_return, indent=2, ensure_ascii=False)
    print("User Info:")
    print(info_json)
    with open(config.DATA_PATH / "user_info.json", encoding="utf-8", mode="+w") as f:
        f.write(info_json)
    
    # 获取并保存认证状态
    certification_return = fetch_certification_status()
    certification_json = json.dumps(certification_return, indent=2, ensure_ascii=False)
    print("Certification Status:")
    print(certification_json)
    with open(config.DATA_PATH / "certification.json", encoding="utf-8", mode="+w") as f:
        f.write(certification_json)
    
    # 获取并保存钱包余额
    funds_return = funds_overview()
    funds_json = json.dumps(funds_return, indent=2, ensure_ascii=False)
    print("Funds Overview:")
    print(funds_json)
    with open(config.DATA_PATH / "funds_overview.json", encoding="utf-8", mode="+w") as f:
        f.write(funds_json)
    
    # 解析并打印余额
    balance = parse_balance(funds_return)
    print_balance(balance)
