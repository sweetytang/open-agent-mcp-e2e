# 🔥 全网实时热点消息聚合与监控系统 (Live Hot Topics Engine)

一套生产级、轻量高效、多平台聚合的**实时热点消息爬取与雷达监控系统**。内置支持主流社交与资讯平台热搜/热榜，提供多源并发抓取、热度去重、SQLite 历史归档、Rich 终端表格、实时变化预警、FastAPI 接口与现代化实时监控大屏。

---

## ✨ 核心特性

- 🌐 **多平台实时聚合**：
  - **微博**：实时热搜榜（热度指数、爆/热/新标签识别）
  - **知乎**：全站热榜（热度值、问答/文章跳转、摘要提取）
  - **百度**：实时热搜（热搜指数、分类与详情链接）
  - **哔哩哔哩**：全站热搜词与实时热门
  - **36氪**：科技商业热门资讯排行
- ⚡ **高性能并发调度引擎**：
  - 支持 `ThreadPoolExecutor` 多源并发采集
  - 自动异常隔离与降级机制，单一平台波动不影响整体运行
- 💾 **数据持久化与导出**：
  - 内置 SQLite 高性能存储与索引去重
  - 支持一键导出为 **JSON** 和 **CSV** 格式
- 🖥️ **现代化可视化看板 & REST API**：
  - 内置 FastAPI 高性能 Web 服务
  - 自带响应式暗黑模式实时大屏（无需繁琐打包，即启即用）
  - 交互式 Swagger API 文档 (`/docs`)
- 🔔 **实时预警 & 终端交互**：
  - `rich` 终端彩色富文本热点表格
  - 自动化登榜热点监听，支持群机器人 Webhook 推送（飞书/钉钉等）

---

## 🏗️ 系统架构

```text
┌──────────────────────────────────────────────────────────┐
│                      用户使用入口                          │
│   CLI (fetch / watch / export)   │   Web Dashboard / API │
└──────────────┬───────────────────────────┬───────────────┘
               │                           │
┌──────────────▼───────────────────────────▼───────────────┐
│               RealtimeEngine (核心调度引擎)                │
│    - 并发控制 (ThreadPoolExecutor)  - 新榜变化监听器      │
└──────────────┬───────────────────────────┬───────────────┘
               │                           │
  ┌────────────▼────────────┐ ┌────────────▼─────────────┐
  │   Crawlers (数据适配器)   │ │ Storage & Notifiers      │
  │  - WeiboCrawler         │ │  - SQLite Storage (本地库) │
  │  - ZhihuCrawler         │ │  - RichConsoleNotifier   │
  │  - BaiduCrawler         │ │  - WebhookNotifier       │
  │  - BilibiliCrawler      │ │  - JSON / CSV Exporter   │
  │  - Kr36Crawler          │ └──────────────────────────┘
  └─────────────────────────┘
```

---

## 🚀 快速上手

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 命令行使用

#### ① 一次性拉取全网热点（默认以终端精美表格展示）
```bash
python main.py fetch
```

也可以拉取指定平台或指定展示条数：
```bash
python main.py fetch --source weibo --limit 20
python main.py fetch --source zhihu --limit 15
```

#### ② 开启持续实时监控巡检 (Watch 模式)
默认每 60 秒轮询一次，自动检测新上榜话题并高亮告警：
```bash
python main.py watch --interval 30
```

#### ③ 导出热点数据
```bash
# 导出为 JSON
python main.py export --format json --output ./data/hot.json

# 导出为 CSV
python main.py export --format csv --output ./data/hot.csv
```

#### ④ 启动 Web 可视化大屏与 API 服务
```bash
python main.py serve --port 8000
```
启动后打开浏览器访问：
- 📊 **可视化监控大屏**：`http://localhost:8000`
- 📑 **Swagger API 文档**：`http://localhost:8000/docs`

---

## 📡 REST API 说明

| 端点 | 方法 | 说明 |
| :--- | :--- | :--- |
| `/` | `GET` | 实时热点可视化监控看板（HTML 单页） |
| `/api/hot` | `GET` | 获取所有平台最新热点列表（可带 `limit` 参数） |
| `/api/hot/{source}` | `GET` | 获取指定来源热点（例如 `/api/hot/weibo`） |
| `/api/health` | `GET` | 服务健康检查 |

---

## ⚙️ 环境变量配置 (.env)

支持通过环境变量灵活配置系统参数：

```ini
# 轮询抓取间隔（秒）
HOT_FETCH_INTERVAL=60

# 单个平台请求超时（秒）
HOT_REQUEST_TIMEOUT=10

# SQLite 数据库存储路径
HOT_SQLITE_PATH=hot_topics.db

# Webhook 告警地址（如飞书自定义机器人）
HOT_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxx

# Web 服务端口
HOT_API_PORT=8000
```

---

## 🧪 单元测试

```bash
pytest tests/
```

---

## 🔌 如何扩展新数据源

继承 `BaseCrawler` 并实现 `_fetch_raw` 与 `_parse_items` 方法即可：

```python
from crawlers.base import BaseCrawler
from core.models import HotItem

class CustomCrawler(BaseCrawler):
    name = "custom"
    display_name = "我的自定义热点源"

    def _fetch_raw(self) -> dict:
        return self.session.get("https://api.example.com/hot").json()

    def _parse_items(self, data: dict) -> list[HotItem]:
        # 解析并返回 List[HotItem]
        ...
```
在 `main.py` 的 `create_engine()` 中注册该爬虫实例即可自动享受并发抓取、数据持久化与大屏展示。
