from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HotItem(BaseModel):
    """单个热点资讯条目模型"""
    id: str = Field(description="全局唯一 ID (通常为 source:item_id 或 source:md5(title))")
    source: str = Field(description="来源平台标识，如 weibo, zhihu, baidu 等")
    source_name: str = Field(description="来源平台展示名，如 微博、知乎、百度热搜")
    rank: int = Field(default=0, description="平台当前排名，从 1 开始")
    title: str = Field(description="热点标题/搜索词")
    url: str = Field(description="目标原文或搜索跳转链接")
    hot_value: Optional[str] = Field(default="", description="热度值描述（如 120万、爆、新等）")
    summary: Optional[str] = Field(default="", description="内容简述/摘要")
    category: Optional[str] = Field(default="综合", description="分类标签")
    extra: Optional[Dict[str, Any]] = Field(default_factory=dict, description="源平台特有附加信息")
    crawled_at: datetime = Field(default_factory=datetime.now, description="抓取时间戳")


class FetchResult(BaseModel):
    """单个爬虫的单次抓取结果汇总"""
    source: str
    source_name: str
    success: bool
    items: List[HotItem] = Field(default_factory=list)
    error: Optional[str] = None
    duration_ms: float = 0.0
    crawled_at: datetime = Field(default_factory=datetime.now)
