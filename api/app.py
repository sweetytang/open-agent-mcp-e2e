from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from core.models import HotItem
from core.storage import HotItemStorage

app = FastAPI(
    title="Realtime Hot Topics Engine API",
    description="多平台实时热点聚合与监控系统接口",
    version="1.0.0"
)

storage = HotItemStorage()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Hot Topics Engine is running smoothly"}


@app.get("/api/hot", response_model=List[HotItem])
def get_all_hot_items(
    limit: int = Query(default=20, ge=1, le=50, description="每个平台返回条数")
):
    """获取所有支持平台的最新热点列表"""
    return storage.get_latest_all(limit_per_source=limit)


@app.get("/api/hot/{source}", response_model=List[HotItem])
def get_hot_by_source(
    source: str,
    limit: int = Query(default=30, ge=1, le=100, description="返回条数")
):
    """获取指定平台（如 weibo, zhihu, baidu, bilibili, kr36）的热点列表"""
    return storage.get_latest_by_source(source=source, limit=limit)


@app.get("/", response_class=HTMLResponse)
def index_dashboard():
    """现代化响应式实时热点监控大屏 (内置轻量级纯前端单页)"""
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
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
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
        h1 { margin: 0; font-size: 24px; color: #fff; }
        .refresh-btn {
            background: #238636;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }
        .refresh-btn:hover { background: #2ea043; }
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
        }
        .card-header {
            font-size: 18px;
            font-weight: bold;
            color: #fff;
            margin-bottom: 12px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
            display: flex;
            justify-content: space-between;
        }
        .item-row {
            display: flex;
            align-items: center;
            padding: 6px 0;
            text-decoration: none;
            color: var(--text-main);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 14px;
        }
        .item-row:hover {
            color: var(--text-highlight);
            background: rgba(255, 255, 255, 0.02);
        }
        .rank {
            width: 28px;
            font-weight: bold;
            color: #8b949e;
        }
        .rank-top { color: #f85149; }
        .title {
            flex: 1;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            padding-right: 8px;
        }
        .hot-val {
            font-size: 12px;
            color: #8b949e;
            white-space: nowrap;
        }
    </style>
</head>
<body>
    <header>
        <div>
            <h1>🔥 实时全网热点雷达 (Live Hot Topics)</h1>
            <small style="color: #8b949e;">聚合微博、知乎、百度、B站、36氪实时资讯 | 每 30 秒自动刷新</small>
        </div>
        <button class="refresh-btn" onclick="loadData()">立即刷新</button>
    </header>

    <div class="grid" id="container">
        <!-- 动态生成各平台卡片 -->
    </div>

    <script>
        async function loadData() {
            try {
                const res = await fetch('/api/hot?limit=15');
                const items = await res.json();
                
                // 按来源分组
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
                    
                    let html = `<div class="card-header"><span>${sourceName}</span><span style="font-size:12px;color:#8b949e">Top ${list.length}</span></div>`;
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
            } catch (err) {
                console.error("加载热点数据失败:", err);
            }
        }

        loadData();
        setInterval(loadData, 30000);
    </script>
</body>
</html>
    """
