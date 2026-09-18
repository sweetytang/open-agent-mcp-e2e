import urllib.parse
from typing import List
from core.models import HotItem
from crawlers.base import BaseCrawler


class BilibiliCrawler(BaseCrawler):
    """哔哩哔哩热搜榜与综合热门"""

    name = "bilibili"
    display_name = "B站热搜"

    def _fetch_raw(self) -> dict:
        url = "https://api.bilibili.com/x/web-interface/wbi/search/square?limit=30"
        headers = {
            "Referer": "https://www.bilibili.com/",
        }
        resp = self.session.get(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _parse_items(self, data: dict) -> List[HotItem]:
        items: List[HotItem] = []
        trending_list = data.get("data", {}).get("trending", {}).get("list", [])

        for idx, entry in enumerate(trending_list, start=1):
            keyword = entry.get("keyword") or entry.get("show_name", "")
            if not keyword:
                continue

            search_url = f"https://search.bilibili.com/all?keyword={urllib.parse.quote(keyword)}"
            icon = entry.get("icon", "")

            items.append(HotItem(
                id=self.make_id(keyword),
                source=self.name,
                source_name=self.display_name,
                rank=idx,
                title=keyword,
                url=search_url,
                hot_value="热搜" if not icon else "上升",
                category="二次元/视频",
                extra={
                    "icon": icon,
                    "position": entry.get("position", idx)
                }
            ))

        return items
