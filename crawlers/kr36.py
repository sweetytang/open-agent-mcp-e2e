from typing import List
from core.models import HotItem
from crawlers.base import BaseCrawler


class Kr36Crawler(BaseCrawler):
    """36氪热门资讯热榜"""

    name = "kr36"
    display_name = "36氪热榜"

    def _fetch_raw(self) -> dict:
        url = "https://gateway.36kr.com/api/mis/nav/home/nav/rank/hot"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Referer": "https://36kr.com/hot-list/catalog",
        }
        payload = {
            "partner_id": "wap",
            "param": {
                "siteId": 1,
                "platformId": 2
            }
        }
        resp = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _parse_items(self, data: dict) -> List[HotItem]:
        items: List[HotItem] = []
        hot_list = data.get("data", {}).get("hotRankList", [])

        for idx, entry in enumerate(hot_list, start=1):
            item_id = entry.get("itemId")
            template_material = entry.get("templateMaterial", {})
            title = template_material.get("widgetTitle") or entry.get("title", "")
            if not title:
                continue

            url = f"https://36kr.com/p/{item_id}" if item_id else "https://36kr.com"
            hot_value = template_material.get("statRead") or "科技热门"

            items.append(HotItem(
                id=self.make_id(str(item_id or title)),
                source=self.name,
                source_name=self.display_name,
                rank=idx,
                title=title,
                url=url,
                hot_value=str(hot_value),
                summary=template_material.get("summary", ""),
                category="科技/商业",
                extra={
                    "author": template_material.get("authorName", ""),
                    "publish_time": template_material.get("publishTime")
                }
            ))

        return items
