"""
API 客户端 - 支持会话复用和连接池管理
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import config


class APIClient:
    """API 客户端，管理会话和连接池"""
    
    def __init__(self, pool_connections=10, pool_maxsize=20, max_retries=3):
        """
        初始化 API 客户端
        
        Args:
            pool_connections: 连接池中的连接数
            pool_maxsize: 连接池最大大小
            max_retries: 最大重试次数
        """
        self.session = requests.Session()
        self.token = None
        
        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # 重试间隔: 1s, 2s, 4s...
            status_forcelist=[429, 500, 502, 503, 504],  # 这些状态码会重试
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # 配置适配器
        adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=retry_strategy
        )
        
        # 为 http 和 https 都配置适配器
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 设置通用请求头
        self.session.headers.update(config.COMMON_HEADERS)
        
        # 禁用 SSL 验证
        self.session.verify = False
    
    def set_token(self, token: str):
        """
        设置认证 token
        
        Args:
            token: 认证 token
        """
        self.token = token
        self.session.headers.update({"app-login-token": token})
    
    def clear_token(self):
        """清除认证 token"""
        self.token = None
        if "app-login-token" in self.session.headers:
            del self.session.headers["app-login-token"]
    
    def post(self, endpoint: str, json_data: dict = None, timeout: int = 30) -> dict:
        """
        发送 POST 请求
        
        Args:
            endpoint: API 端点路径 (例如: /user/login)
            json_data: JSON 数据
            timeout: 请求超时时间（秒）
        
        Returns:
            dict: 响应的 JSON 数据
        
        Raises:
            requests.exceptions.RequestException: 请求失败
        """
        url = f"{config.BASE_URL}{endpoint}"
        
        if json_data is None:
            json_data = {}
        
        response = self.session.post(url, json=json_data, timeout=timeout)
        response.raise_for_status()
        
        return response.json()
    
    def get(self, endpoint: str, params: dict = None, timeout: int = 30) -> dict:
        """
        发送 GET 请求
        
        Args:
            endpoint: API 端点路径
            params: URL 参数
            timeout: 请求超时时间（秒）
        
        Returns:
            dict: 响应的 JSON 数据
        
        Raises:
            requests.exceptions.RequestException: 请求失败
        """
        url = f"{config.BASE_URL}{endpoint}"
        
        response = self.session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        
        return response.json()
    
    def close(self):
        """关闭会话，释放连接"""
        self.session.close()
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时自动关闭会话"""
        self.close()


# 全局客户端实例（单例模式）
_global_client = None


def get_client() -> APIClient:
    """
    获取全局 API 客户端实例
    
    Returns:
        APIClient: 全局客户端实例
    """
    global _global_client
    if _global_client is None:
        _global_client = APIClient()
    return _global_client


def reset_client():
    """重置全局客户端（用于测试或需要重新初始化的场景）"""
    global _global_client
    if _global_client is not None:
        _global_client.close()
        _global_client = None
