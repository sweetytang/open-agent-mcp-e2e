import os
from dataclasses import dataclass, field
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """系统全局配置"""
    # 轮询抓取间隔（秒）
    FETCH_INTERVAL: int = int(os.getenv("HOT_FETCH_INTERVAL", "60"))

    # 请求超时时间（秒）
    REQUEST_TIMEOUT: int = int(os.getenv("HOT_REQUEST_TIMEOUT", "10"))

    # 最大重试次数
    MAX_RETRIES: int = int(os.getenv("HOT_MAX_RETRIES", "3"))

    # 数据存储 SQLite 数据库路径
    SQLITE_DB_PATH: str = os.getenv("HOT_SQLITE_PATH", "hot_topics.db")

    # 默认启用的抓取源列表
    ENABLED_CRAWLERS: List[str] = field(
        default_factory=lambda: os.getenv(
            "HOT_ENABLED_CRAWLERS", "weibo,zhihu,baidu,bilibili,kr36"
        ).split(",")
    )

    # 默认通用 User-Agent
    DEFAULT_USER_AGENT: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # Webhook 推送地址（例如飞书/钉钉/企业微信群机器人，可选）
    WEBHOOK_URL: Optional[str] = os.getenv("HOT_WEBHOOK_URL", None)

    # API 服务主机与端口
    API_HOST: str = os.getenv("HOT_API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("HOT_API_PORT", "8000"))


settings = Settings()
