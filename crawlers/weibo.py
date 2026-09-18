import urllib.parse
from typing import List
from core.models import HotItem
from crawlers.base import BaseCrawler


class WeiboCrawler(BaseCrawler):
    """微博实时热搜榜爬虫"""

    name = "weibo"
    display_name = "微博热搜"

    def _fetch_raw(self) -> dict:
        url = "https://weibo.com/ajax/side/hotSearch"
        headers = {
            "Referer": "https://weibo.com/hot/search",
        }
        resp = self.session.get(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _parse_items(self, data: dict) -> List[HotItem]:
        items: List[HotItem] = []
        realtime = data.get("data", {}).get("realtime", [])
        rank = 1

        for raw in realtime:
            # 过滤广告推荐位（is_ad 标记）
            if raw.get("is_ad"):
                continue

            word = raw.get("word") or raw.get("word_scheme") or ""
            if not word:
                continue

            # 热度值或标识（如：爆、热、新、商）
            num = raw.get("num") or raw.get("raw_hot") or 0
            label = raw.get("label_name", "")
            hot_value = f"{num:,}" if num else label

            query_encoded = urllib.parse.quote(word)
            item_url = f"https://s.weibo.com/weibo?q=%23{query_encoded}%23"

            items.append(HotItem(
                id=self.make_id(word),
                source=self.name,
                source_name=self.display_name,
                rank=rank,
                title=word,
                url=item_url,
                hot_value=str(hot_value),
                category=raw.get("category", "综合"),
                extra={
                    "icon_desc": label,
                    "raw_hot": num
                }
            ))
            rank += 1
            if rank > 50:
                break

        return items
