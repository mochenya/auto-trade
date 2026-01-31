"""
交易相关 API - 使用会话复用的客户端
"""
import time
import random
from datetime import datetime
from zoneinfo import ZoneInfo
from api_client import get_client
import config

CHINA_TZ = ZoneInfo("Asia/Shanghai")


def trade_list(is_finish: bool = False) -> dict:
    """
    获取交易列表（使用客户端中的 token）
    
    Args:
        is_finish: 是否已完成，默认 False
    
    Returns:
        dict: 交易列表数据
    """
    client = get_client()
    payload = {"isFinish": is_finish}
    result = client.post("/second/share/user/list", json_data=payload)
    return result


def parse_trades(trades_data: dict) -> list:
    """
    解析交易列表数据
    
    Args:
        trades_data: trade_list 返回的完整数据
    
    Returns:
        list: 包含字典的列表，每个字典包含 id, title, createTime
    """
    if not trades_data.get("resultCode"):
        raise Exception(f"获取交易列表失败: {trades_data.get('errCodeDes', 'Unknown error')}")
    
    data = trades_data["data"]
    # 合并 showAll 和 page.content 两个列表
    content = data.get("showAll", []) + data.get("page", {}).get("content", [])
    
    return [
        {
            "id": item.get("shareId"),
            "title": item.get("title"),
            "createTime": item.get("createTime"),
        }
        for item in content
    ]


def print_trades(trades: list):
    """
    打印交易列表信息
    
    Args:
        trades: parse_trades 返回的交易列表
    """
    print("\n========== 交易列表 ==========")
    for i, trade in enumerate(trades, 1):
        # 将毫秒时间戳转换为可读时间
        create_time = datetime.fromtimestamp(trade['createTime'] / 1000, tz=CHINA_TZ).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{i}. {trade['title']}")
        print(f"   ID: {trade['id']}")
        print(f"   Create Time: {create_time}")
    print(f"共 {len(trades)} 条交易")
    print("==============================\n")


def follow_trade(share_id: str, quantity: str) -> dict:
    """
    跟单（使用客户端中的 token）
    
    Args:
        share_id: 交易分享 ID
        quantity: 跟单数量
    
    Returns:
        dict: 跟单结果
    """
    client = get_client()
    
    payload = {
        "shareId": share_id,
        "quantity": quantity,
    }
    
    result = client.post("/second/share/user/follow", json_data=payload)
    return result


def parse_follow_result(result: dict) -> dict:
    """
    解析跟单结果
    
    Args:
        result: follow_trade 返回的完整数据
    
    Returns:
        dict: 解析后的跟单结果
    """
    return {
        "success": result.get("resultCode", False),
        "message": result.get("errCodeDes", "Unknown"),
    }


def send_feishu_webhook(webhook_url: str, content: str) -> bool:
    """
    发送飞书 Webhook 消息（使用独立的请求，不影响主会话）
    
    Args:
        webhook_url: 飞书机器人 Webhook 地址
        content: 消息内容
    
    Returns:
        bool: 是否发送成功
    """
    import requests
    
    payload = {
        "msg_type": "text",
        "content": {
            "text": content
        }
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"飞书消息发送失败: {e}")
        return False


def generate_followed_banner(
    create_time: int,
    follow_time: datetime,
    share_id: str,
    available: float,
    quantity: float,
    login_ip: str = None,
    organization: str = None,
    country: str = None,
) -> str:
    """
    生成跟单成功的 Banner

    Args:
        create_time: 订单创建时间（毫秒时间戳）
        follow_time: 跟单时间
        share_id: 交易分享 ID
        available: 可用金额
        quantity: 跟单金额
        login_ip: 登录IP地址
        organization: ISP/组织信息
        country: 国家信息

    Returns:
        str: 格式化的 Banner 文本
    """
    create_dt = datetime.fromtimestamp(create_time / 1000, tz=CHINA_TZ).strftime('%Y-%m-%d %H:%M:%S')
    follow_dt = follow_time.astimezone(CHINA_TZ).strftime('%Y-%m-%d %H:%M:%S')

    location = f"{organization} ({country})" if organization and country else "未知"

    banner = f"""
✨ 跟单成功 ✨

📋 订单信息
  🆔 订单ID: {share_id}
  🕐 创建时间: {create_dt}
  🕒 跟单时间: {follow_dt}

💰 资金信息
  💎 可用金额: {available:.2f} USDT
  📊 跟单金额: {quantity:.2f} USDT

🌐 登录信息
  📍 IP地址: {login_ip or '未知'}
  🏢 位置: {location}
"""
    return banner


def watch_and_follow(email: str = None, password: str = None, max_trades: int = 1):
    """
    循环监听交易列表，发现交易后跟单，然后退出

    Args:
        email: 登录邮箱（可选，默认从环境变量读取）
        password: 登录密码（可选，默认从环境变量读取）
        max_trades: 最多跟单数量，默认 1
    """
    from user import post_login, fetch_get_info
    from funds import funds_overview, parse_balance
    from utils import parse_ip_address

    # 如果未传入，使用配置中的默认值
    if email is None:
        email = config.TRADE_EMAIL
    if password is None:
        password = config.TRADE_PASSWORD
    if not email or not password:
        raise ValueError("请在 .env 文件中设置 TRADE_EMAIL 和 TRADE_PASSWORD")
    
    # 初始登录获取 token
    print("正在登录...")
    token = post_login(email=email, password=password)
    print(f"登录成功: {token}")
    
    # 获取登录IP并解析
    login_ip = None
    organization = None
    country = None

    user_info = fetch_get_info()
    if user_info and (info_data := user_info.get("data")):
        login_ip = info_data.get("loginIp")
        if login_ip:
            ip_info = parse_ip_address(login_ip)
            organization = ip_info.get("organization")
            country = ip_info.get("country")

    # 打印登录信息
    print(f"登录IP: {login_ip or '未知'}")
    print(f"位置: {organization or '未知'} ({country or '未知'})")

    # 获取钱包余额并计算跟单数量
    funds_data = funds_overview()
    balance = parse_balance(funds_data)
    available = balance["usdt_available"]
    quantity = round(available * 0.01, 2)
    
    print(f"可用余额: {available:.2f} USDT")
    print(f"跟单数量: {quantity:.2f} USDT")
    print("开始监听交易，每 30~40 秒随机检查一次...")
    print("按 Ctrl+C 可随时退出\n")
    
    followed_count = 0
    
    def is_token_expired(data: dict) -> bool:
        """检查 token 是否失效"""
        return (
            data.get("errCode") == 100007
            and "Invalid credentials used or login expired" in data.get("errCodeDes", "")
        )
    
    try:
        while followed_count < max_trades:
            # 获取交易列表
            trades = trade_list(is_finish=False)
            
            # 检查 token 是否失效
            if is_token_expired(trades):
                print(f"[{datetime.now(tz=CHINA_TZ).strftime('%H:%M:%S')}] Token 已失效，重新登录...")
                token = post_login(email=email, password=password)
                print(f"重新登录成功: {token[:10]}...")
                continue  # 重新获取交易列表
            
            try:
                parsed_trades = parse_trades(trades)
            except Exception:
                # parse_trades 抛出异常说明无数据或其他错误，跳过本次循环
                wait_time = round(random.uniform(30, 40), 2)
                print(f"[{datetime.now(tz=CHINA_TZ).strftime('%H:%M:%S')}] 暂无交易，{wait_time} 秒后继续...")
                time.sleep(wait_time)
                continue
            
            if parsed_trades:
                print(f"[{datetime.now(tz=CHINA_TZ).strftime('%H:%M:%S')}] 发现 {len(parsed_trades)} 条交易！")
                
                # 跟单
                for trade in parsed_trades:
                    print(f"正在跟单: {trade['title']}")
                    result = follow_trade(trade['id'], str(quantity))
                    
                    # 检查 token 是否失效
                    if is_token_expired(result):
                        print("Token 已失效，重新登录...")
                        token = post_login(email=email, password=password)
                        print(f"重新登录成功: {token[:10]}...")
                        continue  # 重新跟单
                    
                    parsed = parse_follow_result(result)
                    status = "成功" if parsed["success"] else "失败"
                    print(f"跟单{status}: {parsed['message']}")
                    
                    if parsed["success"]:
                        # 生成并打印跟单成功 Banner
                        banner = generate_followed_banner(
                            create_time=trade['createTime'],
                            follow_time=datetime.now(tz=CHINA_TZ),
                            share_id=trade['id'],
                            available=available,
                            quantity=quantity,
                            login_ip=login_ip,
                            organization=organization,
                            country=country,
                        )
                        print(banner)
                        
                        # 发送飞书通知
                        send_feishu_webhook(
                            webhook_url=config.FEISHU_WEBHOOK_URL,
                            content=banner,
                        )
                        
                        followed_count += 1
                        if followed_count >= max_trades:
                            print(f"\n已完成 {max_trades} 笔跟单，退出监听")
                            break
                
                if followed_count >= max_trades:
                    break
            else:
                wait_time = round(random.uniform(30, 40), 2)
                print(f"[{datetime.now(tz=CHINA_TZ).strftime('%H:%M:%S')}] 暂无交易，{wait_time} 秒后继续...")
            
            # 等待随机间隔
            wait_time = round(random.uniform(30, 40), 2)
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("\n用户中断，退出监听")
    except Exception as e:
        print(f"\n发生错误: {e}")
    finally:
        # 清理：关闭客户端会话
        from api_client import get_client
        get_client().close()


if __name__ == "__main__":
    from utils import wait_until_scheduled

    # 等待到指定时间
    # wait_until_scheduled(config.SCHEDULE_TIME, config.ADVANCE_MINUTES)

    # 执行跟单
    watch_and_follow()
