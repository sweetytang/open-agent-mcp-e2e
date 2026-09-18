import urllib.parse
from typing import List
from core.models import HotItem
from crawlers.base import BaseCrawler


class BaiduCrawler(BaseCrawler):
    """百度实时热搜榜爬虫 (采用稳定移动端 JSON 接口)"""

    name = "baidu"
    display_name = "百度热搜"

    def _fetch_raw(self) -> dict:
        url = "https://top.baidu.com/api/board?platform=wise&tab=realtime"
        headers = {
            "Referer": "https://top.baidu.com/board?tab=realtime",
        }
        resp = self.session.get(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _parse_items(self, data: dict) -> List[HotItem]:
        items: List[HotItem] = []
        cards = data.get("data", {}).get("cards", [])
        if not cards:
            return items

        # 第一张卡片通常为实时热搜榜
        realtime_content = cards[0].get("content", [])
        for idx, entry in enumerate(realtime_content, start=1):
            word = entry.get("word") or entry.get("query", "")
            if not word:
                continue

            raw_url = entry.get("rawUrl")
            if not raw_url:
                raw_url = f"https://www.baidu.com/s?wd={urllib.parse.quote(word)}"

            hot_score = entry.get("hotScore") or entry.get("hotTagImg", "")
            desc = entry.get("desc", "")

            items.append(HotItem(
                id=self.make_id(word),
                source=self.name,
                source_name=self.display_name,
                rank=idx,
                title=word,
                url=raw_url,
                hot_value=str(hot_score),
                summary=desc,
                category="实时热搜",
                extra={
                    "img": entry.get("img", ""),
                    "is_top": entry.get("isTop", False)
                }
            ))

        return items
