#!/usr/bin/env python3
"""
量子光学可视化服务器
====================

一个轻量级HTTP服务器，接收Obsidian笔记中的可视化请求，
执行对应的Python可视化脚本，并返回图片路径。

启动方式:
    python viz_server.py [--port 8765]

Obsidian中使用方式:
    [[runviz:fock_state|显示Fock态可视化]]

服务器会自动：
1. 解析请求的概念名称
2. 调用viz_engine.py生成可视化
3. 返回JSON响应（含图片路径）
"""

import json
import os
import sys
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import subprocess
import time

# 配置
DEFAULT_PORT = 8765
VIZ_ENGINE = os.path.join(os.path.dirname(__file__), 'viz_engine.py')
VIZ_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'Obsidian-Vault', '6️⃣ 工具', 'visualizations'
)

# 确保输出目录存在
os.makedirs(VIZ_OUTPUT_DIR, exist_ok=True)


class VizRequestHandler(BaseHTTPRequestHandler):
    """处理可视化请求"""

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{self.log_date_time_string()}] {format % args}")

    def do_GET(self):
        """处理GET请求"""
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == '/' or path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'ok',
                'service': 'Quantum Optics Visualization Server',
                'version': '1.0',
                'endpoints': {
                    '/viz/<concept>': 'Generate visualization for concept',
                    '/list': 'List all available concepts',
                    '/viz/<concept>?params=key1:value1,key2:value2': 'With parameters'
                },
                'supported_concepts': list(VISUALIZATION_FUNCTIONS.keys())
            }
            self.wfile.write(json.dumps(response, indent=2).encode())

        elif path == '/list':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            concepts = {}
            for name, func in VISUALIZATION_FUNCTIONS.items():
                doc = func.__doc__.split('\n')[0].strip() if func.__doc__ else '无描述'
                concepts[name] = doc

            response = {'concepts': concepts}
            self.wfile.write(json.dumps(response, indent=2).encode())

        elif path.startswith('/viz/'):
            concept = path[5:]  # 去掉 '/viz/' 前缀
            self.handle_viz_request(concept, query)

        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'error': 'Not found', 'path': path}
            self.wfile.write(json.dumps(response).encode())

    def handle_viz_request(self, concept, query):
        """处理可视化生成请求"""
        if concept not in VISUALIZATION_FUNCTIONS:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'error': f'Unknown concept: {concept}',
                'available': list(VISUALIZATION_FUNCTIONS.keys())
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            return

        # 解析参数
        params_str = query.get('params', [''])[0]
        params = {}
        if params_str:
            for pair in params_str.split(','):
                if ':' in pair:
                    key, value = pair.split(':', 1)
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                    params[key.strip()] = value

        # 生成可视化
        try:
            output_filename = f"{concept}.png"
            output_path = os.path.join(VIZ_OUTPUT_DIR, output_filename)

            func = VISUALIZATION_FUNCTIONS[concept]
            result_path = func(output_path=output_path, **params)

            # 返回成功响应
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {
                'status': 'success',
                'concept': concept,
                'output_path': result_path,
                'output_url': f'file://{result_path}',
                'params': params
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            print(f"Generated: {concept} -> {result_path}")

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'error': str(e),
                'concept': concept
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            print(f"Error generating {concept}: {e}")


def get_viz_functions():
    """动态导入可视化函数"""
    # 动态导入viz_engine模块
    import importlib.util
    spec = importlib.util.spec_from_file_location("viz_engine", VIZ_ENGINE)
    viz_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(viz_module)
    return viz_module.VISUALIZATION_FUNCTIONS


def main():
    parser = argparse.ArgumentParser(description='量子光学可视化服务器')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT,
                       help=f'服务器端口 (默认: {DEFAULT_PORT})')
    parser.add_argument('--host', type=str, default='localhost',
                       help='监听地址 (默认: localhost)')
    args = parser.parse_args()

    # 获取可视化函数
    global VISUALIZATION_FUNCTIONS
    try:
        VISUALIZATION_FUNCTIONS = get_viz_functions()
        print(f"✓ 加载了 {len(VISUALIZATION_FUNCTIONS)} 个可视化概念")
    except Exception as e:
        print(f"✗ 无法加载可视化引擎: {e}")
        sys.exit(1)

    # 启动服务器
    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, VizRequestHandler)

    print(f"""
╔════════════════════════════════════════════════════════════╗
║        量子光学可视化服务器 v1.0                             ║
╠════════════════════════════════════════════════════════════╣
║  服务地址: http://{args.host}:{args.port}                         ║
║  输出目录: {VIZ_OUTPUT_DIR}          ║
╠════════════════════════════════════════════════════════════╣
║  端点:                                                    ║
║    GET /              - 健康检查                          ║
║    GET /list          - 列出所有可视化概念                 ║
║    GET /viz/<concept> - 生成指定概念的可视化              ║
║                                                            ║
║  Obsidian中使用:                                          ║
║    [[runviz:fock_state]]                                   ║
║    [[runviz:rabi_oscillation|显示动画]]                     ║
╠════════════════════════════════════════════════════════════╣
║  按 Ctrl+C 停止服务器                                      ║
╚════════════════════════════════════════════════════════════╝
    """)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        httpd.shutdown()


if __name__ == '__main__':
    main()
