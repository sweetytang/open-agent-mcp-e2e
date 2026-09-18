import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from core.models import HotItem


class HotItemStorage:
    """热点资讯持久化存储管理器 (基于 SQLite & JSON)"""

    def __init__(self, db_path: str = "hot_topics.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据表结构与索引"""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hot_items (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    hot_value TEXT,
                    summary TEXT,
                    category TEXT,
                    extra_json TEXT,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON hot_items(source);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_crawled_at ON hot_items(crawled_at);")
            conn.commit()

    def save_items(self, items: List[HotItem]) -> int:
        """批量保存或更新热点数据"""
        if not items:
            return 0

        saved_count = 0
        now_str = datetime.now().isoformat()

        with self._get_conn() as conn:
            for item in items:
                conn.execute("""
                    INSERT INTO hot_items (
                        id, source, source_name, rank, title, url, hot_value,
                        summary, category, extra_json, crawled_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        rank=excluded.rank,
                        hot_value=excluded.hot_value,
                        updated_at=excluded.updated_at
                """, (
                    item.id,
                    item.source,
                    item.source_name,
                    item.rank,
                    item.title,
                    item.url,
                    item.hot_value or "",
                    item.summary or "",
                    item.category or "综合",
                    json.dumps(item.extra, ensure_ascii=False) if item.extra else "{}",
                    item.crawled_at.isoformat(),
                    now_str
                ))
                saved_count += 1
            conn.commit()
        return saved_count

    def get_latest_by_source(self, source: str, limit: int = 50) -> List[HotItem]:
        """获取指定来源最新的热点条目"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM hot_items
                WHERE source = ?
                ORDER BY rank ASC, updated_at DESC
                LIMIT ?
            """, (source, limit))
            rows = cursor.fetchall()
            return [self._row_to_model(row) for row in rows]

    def get_latest_all(self, limit_per_source: int = 20) -> List[HotItem]:
        """获取所有数据源最新热点"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                WITH Ranked AS (
                    SELECT *,
                           ROW_NUMBER() OVER(PARTITION BY source ORDER BY rank ASC, updated_at DESC) as rn
                    FROM hot_items
                )
                SELECT * FROM Ranked WHERE rn <= ? ORDER BY source, rank ASC
            """, (limit_per_source,))
            rows = cursor.fetchall()
            return [self._row_to_model(row) for row in rows]

    def export_to_json(self, output_file: str) -> str:
        """将当前数据导出为 JSON 文件"""
        items = self.get_latest_all(limit_per_source=50)
        data = [item.model_dump(mode="json") for item in items]
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(path.resolve())

    def export_to_csv(self, output_file: str) -> str:
        """将当前数据导出为 CSV 文件"""
        items = self.get_latest_all(limit_per_source=50)
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["来源平台", "排名", "热点标题", "热度值", "链接", "分类", "更新时间"])
            for item in items:
                writer.writerow([
                    item.source_name,
                    item.rank,
                    item.title,
                    item.hot_value,
                    item.url,
                    item.category,
                    item.crawled_at.strftime("%Y-%m-%d %H:%M:%S")
                ])
        return str(path.resolve())

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> HotItem:
        extra = {}
        if row["extra_json"]:
            try:
                extra = json.loads(row["extra_json"])
            except Exception:
                pass
        return HotItem(
            id=row["id"],
            source=row["source"],
            source_name=row["source_name"],
            rank=row["rank"],
            title=row["title"],
            url=row["url"],
            hot_value=row["hot_value"],
            summary=row["summary"],
            category=row["category"],
            extra=extra,
            crawled_at=datetime.fromisoformat(row["crawled_at"])
        )
