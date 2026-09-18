import os
import tempfile
import pytest
from core.models import HotItem, FetchResult
from core.storage import HotItemStorage
from core.engine import RealtimeEngine
from crawlers.base import BaseCrawler


class MockCrawler(BaseCrawler):
    name = "mock"
    display_name = "测试爬虫"

    def _fetch_raw(self) -> dict:
        return {"items": [{"title": "测试热搜标题 1", "rank": 1}]}

    def _parse_items(self, data: dict) -> list[HotItem]:
        return [
            HotItem(
                id=self.make_id("item_1"),
                source=self.name,
                source_name=self.display_name,
                rank=1,
                title=data["items"][0]["title"],
                url="https://example.com/item/1",
                hot_value="99999",
                category="测试"
            )
        ]


def test_hot_item_creation():
    item = HotItem(
        id="test:1",
        source="test",
        source_name="测试",
        rank=1,
        title="测试标题",
        url="https://example.com"
    )
    assert item.id == "test:1"
    assert item.rank == 1


def test_storage_and_query():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        storage = HotItemStorage(db_path=db_path)
        items = [
            HotItem(
                id="weibo:1",
                source="weibo",
                source_name="微博",
                rank=1,
                title="热搜 1",
                url="https://s.weibo.com"
            ),
            HotItem(
                id="weibo:2",
                source="weibo",
                source_name="微博",
                rank=2,
                title="热搜 2",
                url="https://s.weibo.com"
            )
        ]
        saved = storage.save_items(items)
        assert saved == 2

        latest = storage.get_latest_by_source("weibo")
        assert len(latest) == 2
        assert latest[0].title == "热搜 1"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_engine_fetch():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        storage = HotItemStorage(db_path=db_path)
        engine = RealtimeEngine(storage=storage)
        mock_crawler = MockCrawler()
        engine.register_crawler(mock_crawler)

        results = engine.fetch_all()
        assert len(results) == 1
        assert results[0].success is True
        assert len(results[0].items) == 1
        assert results[0].items[0].title == "测试热搜标题 1"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
