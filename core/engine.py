import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Dict, List, Optional
from core.models import FetchResult, HotItem
from core.storage import HotItemStorage
from crawlers.base import BaseCrawler

logger = logging.getLogger(__name__)


class RealtimeEngine:
    """实时热点爬虫聚合与调度调度引擎"""

    def __init__(self, storage: Optional[HotItemStorage] = None):
        self.storage = storage or HotItemStorage()
        self.crawlers: Dict[str, BaseCrawler] = {}
        self._is_running = False
        self._stop_event = threading.Event()
        self._listeners: List[Callable[[List[HotItem]], None]] = []
        self._last_seen_titles: set = set()

    def register_crawler(self, crawler: BaseCrawler) -> "RealtimeEngine":
        """注册数据源爬虫"""
        self.crawlers[crawler.name] = crawler
        return self

    def add_listener(self, callback: Callable[[List[HotItem]], None]) -> None:
        """添加新上榜/热点变更监听回调"""
        self._listeners.append(callback)

    def fetch_source(self, source_name: str) -> FetchResult:
        """同步拉取单一来源数据"""
        crawler = self.crawlers.get(source_name)
        if not crawler:
            return FetchResult(
                source=source_name,
                source_name=source_name,
                success=False,
                error=f"未注册的抓取源: {source_name}"
            )
        res = crawler.fetch()
        if res.success and res.items:
            self.storage.save_items(res.items)
        return res

    def fetch_all(self, max_workers: int = 5) -> List[FetchResult]:
        """并发拉取所有已注册数据源"""
        results: List[FetchResult] = []
        new_top_items: List[HotItem] = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_crawler = {
                executor.submit(crawler.fetch): crawler for crawler in self.crawlers.values()
            }
            for future in as_completed(future_to_crawler):
                crawler = future_to_crawler[future]
                try:
                    res: FetchResult = future.result()
                    results.append(res)
                    if res.success and res.items:
                        self.storage.save_items(res.items)
                        # 检测首次登榜的新热点
                        for item in res.items:
                            title_key = f"{item.source}:{item.title}"
                            if title_key not in self._last_seen_titles:
                                self._last_seen_titles.add(title_key)
                                new_top_items.append(item)
                except Exception as exc:
                    logger.error(f"[{crawler.name}] 执行抓取异常: {exc}", exc_info=True)
                    results.append(FetchResult(
                        source=crawler.name,
                        source_name=crawler.display_name,
                        success=False,
                        error=str(exc)
                    ))

        # 触发新上榜热点通知
        if new_top_items and self._listeners:
            for listener in self._listeners:
                try:
                    listener(new_top_items)
                except Exception as e:
                    logger.error(f"监听回调执行异常: {e}")

        return results

    def start_polling(self, interval_seconds: int = 60, run_forever: bool = True) -> None:
        """启动后台定时持续轮询"""
        self._is_running = True
        self._stop_event.clear()
        logger.info(f"实时热点引擎已启动，轮询周期: {interval_seconds}s")

        try:
            while not self._stop_event.is_set():
                start_t = time.time()
                self.fetch_all()
                elapsed = time.time() - start_t
                sleep_time = max(0.0, interval_seconds - elapsed)
                if self._stop_event.wait(timeout=sleep_time):
                    break
        except KeyboardInterrupt:
            logger.info("接收到停止信号，正在停止轮询...")
        finally:
            self._is_running = False

    def stop_polling(self) -> None:
        """优雅停止轮询"""
        self._stop_event.set()
        self._is_running = False
