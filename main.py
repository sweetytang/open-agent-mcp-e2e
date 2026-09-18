import argparse
import sys
import uvicorn
from config import settings
from core.engine import RealtimeEngine
from core.storage import HotItemStorage
from crawlers.baidu import BaiduCrawler
from crawlers.bilibili import BilibiliCrawler
from crawlers.kr36 import Kr36Crawler
from crawlers.weibo import WeiboCrawler
from crawlers.zhihu import ZhihuCrawler
from notifiers.base import RichConsoleNotifier, WebhookNotifier


def create_engine() -> RealtimeEngine:
    """初始化并组装所有热点爬虫与通知器"""
    storage = HotItemStorage(settings.SQLITE_DB_PATH)
    engine = RealtimeEngine(storage=storage)

    # 注册支持的平台爬虫
    crawlers = [
        WeiboCrawler(),
        ZhihuCrawler(),
        BaiduCrawler(),
        BilibiliCrawler(),
        Kr36Crawler(),
    ]
    for c in crawlers:
        engine.register_crawler(c)

    # 注册富文本通知与 Webhook
    engine.add_listener(RichConsoleNotifier().send)
    if settings.WEBHOOK_URL:
        engine.add_listener(WebhookNotifier(settings.WEBHOOK_URL).send)

    return engine


def cmd_fetch(args):
    """单次抓取并展示"""
    engine = create_engine()
    notifier = RichConsoleNotifier()

    if args.source and args.source != "all":
        print(f"正在拉取单个数据源: {args.source} ...")
        res = engine.fetch_source(args.source)
        if res.success:
            notifier.display_hot_list(res.items, title=f"📊 {res.source_name} 实时热点")
        else:
            print(f"❌ 抓取失败: {res.error}")
    else:
        print("⚡ 正在并发拉取全网最新热点...")
        results = engine.fetch_all()
        for res in results:
            if res.success:
                notifier.display_hot_list(res.items[:args.limit], title=f"📊 {res.source_name} (Top {args.limit})")
            else:
                print(f"⚠️ [{res.source_name}] 抓取失败: {res.error}")


def cmd_watch(args):
    """实时监控模式：定时循环抓取并提示最新榜单变化"""
    engine = create_engine()
    interval = args.interval or settings.FETCH_INTERVAL
    print(f"🚀 启动热点实时雷达监控 (轮询周期: {interval}秒，按 Ctrl+C 退出)...")
    engine.start_polling(interval_seconds=interval)


def cmd_export(args):
    """数据导出工具"""
    storage = HotItemStorage(settings.SQLITE_DB_PATH)
    output = args.output
    fmt = args.format.lower()

    if fmt == "json":
        saved_path = storage.export_to_json(output or "hot_topics.json")
        print(f"✅ 成功导出最新热点数据至: {saved_path}")
    elif fmt == "csv":
        saved_path = storage.export_to_csv(output or "hot_topics.csv")
        print(f"✅ 成功导出最新热点数据至: {saved_path}")
    else:
        print(f"❌ 不支持的格式: {fmt}")


def cmd_serve(args):
    """启动 REST API 与 Web 监控面板服务"""
    host = args.host or settings.API_HOST
    port = args.port or settings.API_PORT
    print(f"🌟 启动 Web 监控面板与 REST API 服务: http://{host}:{port}")
    print(f"🔗 访问在线大屏: http://localhost:{port}")
    print(f"🔗 API 文档交互界面: http://localhost:{port}/docs")
    uvicorn.run("api.app:app", host=host, port=port, reload=False)


def main():
    parser = argparse.ArgumentParser(
        description="🔥 全网实时热点消息爬取与监控系统",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令列表")

    # fetch 命令
    fetch_parser = subparsers.add_parser("fetch", help="执行一次性爬取并输出展示")
    fetch_parser.add_argument("--source", default="all", help="指定平台代码 (weibo, zhihu, baidu, bilibili, kr36, all)")
    fetch_parser.add_argument("--limit", type=int, default=10, help="每个平台展示的条数上限 (默认: 10)")
    fetch_parser.set_defaults(func=cmd_fetch)

    # watch 命令
    watch_parser = subparsers.add_parser("watch", help="开启实时监控巡检模式")
    watch_parser.add_argument("--interval", type=int, default=60, help="轮询抓取间隔（秒，默认 60 秒）")
    watch_parser.set_defaults(func=cmd_watch)

    # export 命令
    export_parser = subparsers.add_parser("export", help="导出热点数据到文件")
    export_parser.add_argument("--format", default="json", choices=["json", "csv"], help="导出文件格式")
    export_parser.add_argument("--output", default="", help="保存文件路径")
    export_parser.set_defaults(func=cmd_export)

    # serve 命令
    serve_parser = subparsers.add_parser("serve", help="启动 FastAPI Web 服务与可视化看板")
    serve_parser.add_argument("--host", default="0.0.0.0", help="监听主机 IP")
    serve_parser.add_argument("--port", type=int, default=8000, help="监听端口")
    serve_parser.set_defaults(func=cmd_serve)

    if len(sys.argv) == 1:
        # 默认执行一次单次抓取展示
        sys.argv.append("fetch")

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
