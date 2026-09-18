from typing import List
from core.models import HotItem
from crawlers.base import BaseCrawler


class ZhihuCrawler(BaseCrawler):
    """知乎全站热榜爬虫"""

    name = "zhihu"
    display_name = "知乎热榜"

    def _fetch_raw(self) -> dict:
        url = "https://www.zhihu.com/api/v3/feed/topstory/hot_lists/total?limit=50"
        headers = {
            "Referer": "https://www.zhihu.com/hot",
            "x-requested-with": "fetch",
        }
        resp = self.session.get(url, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _parse_items(self, data: dict) -> List[HotItem]:
        items: List[HotItem] = []
        hot_list = data.get("data", [])

        for idx, entry in enumerate(hot_list, start=1):
            target = entry.get("target", {})
            title = target.get("title", "")
            if not title:
                continue

            target_id = target.get("id")
            # 区分问答与文章链接
            if target.get("type") == "question" or "question" in str(target.get("url", "")):
                url = f"https://www.zhihu.com/question/{target_id}"
            else:
                url = target.get("url") or f"https://www.zhihu.com/question/{target_id}"

            detail_text = entry.get("detail_text", "")  # 如 "1230 万热度"
            excerpt = target.get("excerpt", "")

            items.append(HotItem(
                id=self.make_id(str(target_id or title)),
                source=self.name,
                source_name=self.display_name,
                rank=idx,
                title=title,
                url=url,
                hot_value=detail_text,
                summary=excerpt[:150] if excerpt else "",
                category="问答/深度",
                extra={
                    "answer_count": target.get("answer_count", 0),
                    "comment_count": target.get("comment_count", 0),
                }
            ))

        return items
