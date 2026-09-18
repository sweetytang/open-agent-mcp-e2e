import json
import logging
from typing import List, Optional
import requests
from rich.console import Console
from rich.table import Table
from core.models import HotItem

logger = logging.getLogger(__name__)


class BaseNotifier:
    """通知器基类"""
    def send(self, new_items: List[HotItem]) -> bool:
        raise NotImplementedError


class RichConsoleNotifier(BaseNotifier):
    """终端控制台富文本表格打印器"""

    def __init__(self):
        self.console = Console()

    def display_hot_list(self, items: List[HotItem], title: str = "实时热点聚焦"):
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("来源", style="cyan", width=10)
        table.add_column("排名", justify="right", style="bold yellow", width=6)
        table.add_column("热点标题", style="white", min_width=30)
        table.add_column("热度/指数", justify="right", style="green", width=14)
        table.add_column("分类", style="dim", width=10)
        table.add_column("链接", style="blue underline")

        for item in items:
            table.add_row(
                item.source_name,
                f"#{item.rank}",
                item.title,
                item.hot_value or "-",
                item.category or "综合",
                item.url
            )

        self.console.print(table)

    def send(self, new_items: List[HotItem]) -> bool:
        if not new_items:
            return True
        self.display_hot_list(new_items[:15], title=f"⚡ 发现 {len(new_items)} 条最新登榜热点")
        return True


class WebhookNotifier(BaseNotifier):
    """群机器人 Webhook 推送通知器 (支持飞书/钉钉等常用结构)"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, new_items: List[HotItem]) -> bool:
        if not self.webhook_url or not new_items:
            return False

        top_items = new_items[:8]
        lines = [f"🔥 **【实时热点动态提醒】** 发现 {len(new_items)} 条新热点：\n"]
        for item in top_items:
            lines.append(f"- [{item.source_name} #{item.rank}] [{item.title}]({item.url}) ({item.hot_value})")

        payload = {
            "msg_type": "text",
            "content": {
                "text": "\n".join(lines)
            }
        }

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Webhook 推送失败: {e}")
            return False
