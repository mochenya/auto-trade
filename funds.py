"""
资金相关 API - 使用会话复用的客户端
"""
from api_client import get_client


def funds_overview() -> dict:
    """
    获取钱包余额概览（使用客户端中的 token）
    
    Returns:
        dict: 钱包余额数据
    """
    client = get_client()
    result = client.post("/funds/overview", json_data={})
    return result


def parse_balance(funds_data: dict) -> dict:
    """
    解析钱包余额数据
    
    Args:
        funds_data: funds_overview 返回的完整数据
    
    Returns:
        dict: 解析后的余额信息
    """
    if not funds_data.get("resultCode"):
        raise Exception(f"获取余额失败: {funds_data.get('errCodeDes', 'Unknown error')}")
    
    data = funds_data["data"]
    
    return {
        "usdt_total": data.get("usdtTotal", 0.0),
        "usdt_available": data.get("usdtAvailable", 0.0),
        "usdt_unavailable": data.get("usdtUnavailable", 0.0),
        "today_income": data.get("todayIncome", "0"),
    }


def print_balance(balance: dict):
    """
    打印钱包余额信息
    
    Args:
        balance: parse_balance 返回的余额数据
    """
    print("\n========== 钱包余额 ==========")
    print(f"总资产 (USDT):   {balance['usdt_total']:.2f}")
    print(f"可用余额 (USDT): {balance['usdt_available']:.2f}")
    print(f"冻结余额 (USDT): {balance['usdt_unavailable']:.2f}")
    print(f"今日收益:        {balance['today_income']}")
    print("==============================\n")
