# -*- coding: utf-8 -*-
"""部署画廊静态服务器 -> http://localhost:8091

读取脚本同级目录下的 shuixian-deploy（部署版画廊源码）。
启动方式：
    py serve_deploy_gallery.py
或双击 start_deploy_gallery.bat
"""
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = 8091
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shuixian-deploy")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        # 禁用缓存：改完源码刷新浏览器即可见，便于本地对比
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def log_message(self, fmt, *args):
        try:
            sys.stdout.write("[8091] " + (fmt % args) + "\n")
        except Exception:
            pass


def main():
    if not os.path.isdir(ROOT):
        print("目录不存在:", ROOT)
        sys.exit(1)
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("=" * 52)
    print(" 部署画廊 (shuixian-deploy) 已启动")
    print(f" 地址:   http://localhost:{PORT}")
    print(f" 根目录: {ROOT}")
    print(" 按 Ctrl+C 停止")
    print("=" * 52)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[8091] 已停止")
        httpd.server_close()


if __name__ == "__main__":
    main()
