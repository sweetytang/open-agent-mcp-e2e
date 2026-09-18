import logging
import threading
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from config import settings
from core.engine import RealtimeEngine
from core.models import HotItem
from core.storage import HotItemStorage
from crawlers.baidu import BaiduCrawler
from crawlers.bilibili import BilibiliCrawler
from crawlers.kr36 import Kr36Crawler
from crawlers.weibo import WeiboCrawler
from crawlers.zhihu import ZhihuCrawler

logger = logging.getLogger(__name__)

storage = HotItemStorage(settings.SQLITE_DB_PATH)
engine = RealtimeEngine(storage=storage)

# 注册支持的爬虫源
for crawler in [
    WeiboCrawler(),
    ZhihuCrawler(),
    BaiduCrawler(),
    BilibiliCrawler(),
    Kr36Crawler(),
]:
    engine.register_crawler(crawler)

# 后台轮询线程
_polling_thread: Optional[threading.Thread] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：服务启动时自动开启后台爬取和定时轮询"""
    global _polling_thread
    # 启动后台守护轮询线程，周期抓取
    _polling_thread = threading.Thread(
        target=engine.start_polling,
        args=(settings.FETCH_INTERVAL,),
        daemon=True
    )
    _polling_thread.start()
    logger.info("已随 Web 服务自动启动后台实时热点抓取调度线程")
    yield
    # 关闭服务时优雅停止
    engine.stop_polling()


app = FastAPI(
    title="Realtime Hot Topics Engine API",
    description="多平台实时热点聚合与监控系统接口",
    version="1.1.0",
    lifespan=lifespan
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Hot Topics Engine is running smoothly"}


@app.get("/api/hot", response_model=List[HotItem])
def get_all_hot_items(
    limit: int = Query(default=20, ge=1, le=50, description="每个平台返回条数")
):
    """获取所有支持平台的最新热点列表。如果数据库首次为空，会自动触发即时抓取预热。"""
    items = storage.get_latest_all(limit_per_source=limit)
    if not items:
        # 首次启动数据库为空，即时执行一次预热爬取
        logger.info("数据库尚无数据，触发首次即时抓取预热...")
        engine.fetch_all()
        items = storage.get_latest_all(limit_per_source=limit)
    return items


@app.get("/api/hot/{source}", response_model=List[HotItem])
def get_hot_by_source(
    source: str,
    limit: int = Query(default=30, ge=1, le=100, description="返回条数")
):
    """获取指定平台（如 weibo, zhihu, baidu, bilibili, kr36）的热点列表"""
    items = storage.get_latest_by_source(source=source, limit=limit)
    if not items:
        engine.fetch_source(source)
        items = storage.get_latest_by_source(source=source, limit=limit)
    return items


@app.post("/api/refresh")
def refresh_all_now(background_tasks: BackgroundTasks):
    """手动触发一次即时全网拉取"""
    background_tasks.add_task(engine.fetch_all)
    return {"status": "triggered", "message": "后台已开始执行全网热点拉取"}


@app.get("/", response_class=HTMLResponse)
def index_dashboard():
    """现代化响应式实时热点监控大屏 (内置暗黑主题单页，支持空状态友好提示与手动刷新)"""
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 实时全网热点雷达 - Live Hot Dashboard</title>
    <style>
        :root {
            --bg-color: #0d1117;
            --card-bg: #161b22;
            --border-color: #30363d;
            --text-main: #c9d1d9;
            --text-highlight: #58a6ff;
            --accent: #f85149;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 24px;
        }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }
        h1 { margin: 0; font-size: 24px; color: #fff; display: flex; align-items: center; gap: 8px; }
        .badge {
            font-size: 12px;
            background: #238636;
            color: #fff;
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: normal;
        }
        .actions {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .refresh-btn {
            background: #238636;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .refresh-btn:hover { background: #2ea043; }
        .refresh-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .status-bar {
            font-size: 13px;
            color: #8b949e;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .card-header {
            font-size: 17px;
            font-weight: bold;
            color: #fff;
            margin-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .item-row {
            display: flex;
            align-items: center;
            padding: 7px 0;
            text-decoration: none;
            color: var(--text-main);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 14px;
            transition: color 0.15s, background 0.15s;
        }
        .item-row:hover {
            color: var(--text-highlight);
            background: rgba(255, 255, 255, 0.03);
            border-radius: 4px;
        }
        .rank {
            width: 28px;
            font-weight: bold;
            color: #8b949e;
            text-align: center;
        }
        .rank-top { color: #f85149; font-weight: 900; }
        .title {
            flex: 1;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            padding: 0 8px;
        }
        .hot-val {
            font-size: 12px;
            color: #8b949e;
            white-space: nowrap;
        }
        .loading-box {
            text-align: center;
            padding: 60px 20px;
            color: #8b949e;
            grid-column: 1 / -1;
            background: var(--card-bg);
            border-radius: 8px;
            border: 1px dashed var(--border-color);
        }
        .spinner {
            display: inline-block;
            width: 32px;
            height: 32px;
            border: 3px solid rgba(255,255,255,0.1);
            border-radius: 50%;
            border-top-color: var(--text-highlight);
            animation: spin 1s ease-in-out infinite;
            margin-bottom: 12px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>
                🔥 实时全网热点雷达
                <span class="badge">已连接</span>
            </h1>
            <div class="status-bar" id="update-time">聚合微博、知乎、百度、B站、36氪资讯 | 正在连接数据源...</div>
        </div>
        <div class="actions">
            <button class="refresh-btn" id="ref-btn" onclick="triggerRefresh()">
                <span id="btn-text">🔄 立即抓取</span>
            </button>
        </div>
    </header>

    <div class="grid" id="container">
        <div class="loading-box">
            <div class="spinner"></div>
            <div>正在拉取并解析全网最新热点，请稍候约 2~3 秒...</div>
        </div>
    </div>

    <script>
        async function loadData() {
            try {
                const res = await fetch('/api/hot?limit=15');
                const items = await res.json();

                if (!items || items.length === 0) {
                    document.getElementById('container').innerHTML = `
                        <div class="loading-box">
                            <div class="spinner"></div>
                            <div>后台正在首次爬取热点数据，请稍候几秒后将自动呈现...</div>
                        </div>
                    `;
                    return;
                }

                // 按照来源平台分类
                const groups = {};
                items.forEach(item => {
                    if (!groups[item.source_name]) {
                        groups[item.source_name] = [];
                    }
                    groups[item.source_name].push(item);
                });

                const container = document.getElementById('container');
                container.innerHTML = '';

                for (const [sourceName, list] of Object.entries(groups)) {
                    const card = document.createElement('div');
                    card.className = 'card';
                    
                    let html = `<div class="card-header"><span>${sourceName}</span><span style="font-size:12px;color:#8b949e">TOP ${list.length}</span></div>`;
                    list.sort((a, b) => a.rank - b.rank);
                    list.forEach(i => {
                        const rankClass = i.rank <= 3 ? 'rank rank-top' : 'rank';
                        html += `
                            <a href="${i.url}" target="_blank" class="item-row">
                                <span class="${rankClass}">#${i.rank}</span>
                                <span class="title" title="${i.title}">${i.title}</span>
                                <span class="hot-val">${i.hot_value || ''}</span>
                            </a>
                        `;
                    });
                    card.innerHTML = html;
                    container.appendChild(card);
                }

                document.getElementById('update-time').innerText = '最后同步时间: ' + new Date().toLocaleTimeString() + ' (每 30 秒自动刷新)';
            } catch (err) {
                console.error("加载热点数据失败:", err);
            }
        }

        async function triggerRefresh() {
            const btn = document.getElementById('ref-btn');
            const txt = document.getElementById('btn-text');
            btn.disabled = true;
            txt.innerText = '抓取中...';
            try {
                await fetch('/api/refresh', { method: 'POST' });
                setTimeout(async () => {
                    await loadData();
                    btn.disabled = false;
                    txt.innerText = '🔄 立即抓取';
                }, 2000);
            } catch (e) {
                btn.disabled = false;
                txt.innerText = '🔄 立即抓取';
            }
        }

        loadData();
        // 首次如果是空，5秒后再自动尝试一次；之后每 30 秒自动刷新
        setTimeout(loadData, 3500);
        setInterval(loadData, 30000);
    </script>
</body>
</html>
    """
