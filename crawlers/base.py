import abc
import hashlib
import time
from typing import List, Optional
import requests
from config import settings
from core.models import FetchResult, HotItem


class BaseCrawler(abc.ABC):
    """热点爬虫基类"""

    name: str = "base"
    display_name: str = "基础爬虫"

    def __init__(self, timeout: Optional[int] = None):
        self.timeout = timeout or settings.REQUEST_TIMEOUT
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": settings.DEFAULT_USER_AGENT,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })

    def make_id(self, identifier: str) -> str:
        """生成全局唯一防冲突 ID"""
        raw = f"{self.name}:{identifier}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    @abc.abstractmethod
    def _parse_items(self, response_data: dict) -> List[HotItem]:
        """子类需实现的解析逻辑"""
        pass

    @abc.abstractmethod
    def _fetch_raw(self) -> dict:
        """发起网络请求获取原始数据"""
        pass

    def fetch(self) -> FetchResult:
        """统一执行抓取，包含耗时统计与异常防护"""
        start_time = time.time()
        try:
            raw_data = self._fetch_raw()
            items = self._parse_items(raw_data)
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return FetchResult(
                source=self.name,
                source_name=self.display_name,
                success=True,
                items=items,
                duration_ms=duration_ms
            )
        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return FetchResult(
                source=self.name,
                source_name=self.display_name,
                success=False,
                items=[],
                error=str(exc),
                duration_ms=duration_ms
            )
