#!/usr/bin/env python3
"""
Tavily API Key 自动轮换脚本
当 Tavily API 遇到问题时，自动切换到下一个 key

用法:
    python tavily_key_rotation.py search "query"
    python tavily_key_rotation.py test
"""

import os
import sys
import subprocess
import time
import json

# Tavily API Keys
TAVILY_KEYS = [
    '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',
    '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',
    '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',
    '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'
]

CURRENT_KEY_INDEX = 0
MAX_RETRIES = 3
RETRY_DELAY = 60  # 秒


def get_current_key():
    """获取当前使用的 key"""
    return TAVILY_KEYS[CURRENT_KEY_INDEX]


def rotate_key():
    """轮换到下一个 key"""
    global CURRENT_KEY_INDEX
    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(TAVILY_KEYS)
    return get_current_key()


def get_next_key():
    """获取下一个 key（不改变当前）"""
    next_index = (CURRENT_KEY_INDEX + 1) % len(TAVILY_KEYS)
    return TAVILY_KEYS[next_index]


def test_api_key(key):
    """测试 API key 是否有效"""
    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'GET', 'https://api.tavily.com/search',
             '-H', f'X-API-KEY: {key}',
             '-d', 'query=test'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if 'Unauthorized' in result.stdout or 'Forbidden' in result.stdout:
            return False
        if 'rate_limit' in result.stdout.lower() or '429' in result.stdout:
            return False
        return True
    except Exception as e:
        print(f"测试 key 时出错: {e}")
        return False


def call_tavily_with_rotation(query, max_retries=None):
    """使用自动轮换调用 Tavily API"""
    if max_retries is None:
        max_retries = MAX_RETRIES

    tried_keys = []
    last_error = None

    for attempt in range(max_retries):
        # 如果已经尝试过所有 key，退出
        if len(tried_keys) >= len(TAVILY_KEYS):
            print(f"所有 Tavily API keys 都失败")
            return None

        key = get_current_key()

        # 跳过已尝试的 key
        if key in tried_keys:
            rotate_key()
            continue

        print(f"尝试使用 key: {key[:15]}... (尝试 {len(tried_keys) + 1}/{len(TAVILY_KEYS)})")

        try:
            # 构建 curl 命令
            cmd = [
                'curl', '-s', '-X', 'POST',
                'https://api.tavily.com/search',
                '-H', f'X-API-KEY: {key}',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps({'query': query, 'max_results': 5})
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            response = result.stdout

            # 检查错误
            if 'Unauthorized' in response or '403' in response:
                print(f"Key {key[:15]}... 返回 Unauthorized")
                tried_keys.append(key)
                rotate_key()
                continue

            if 'rate_limit' in response.lower() or '429' in response:
                print(f"Key {key[:15]}... 触发 rate limit")
                tried_keys.append(key)
                rotate_key()
                continue

            if not response or len(response) < 50:
                print(f"Key {key[:15]}... 返回空响应")
                tried_keys.append(key)
                rotate_key()
                continue

            # 成功
            print(f"成功使用 key: {key[:15]}...")
            return response

        except subprocess.TimeoutExpired:
            print(f"Key {key[:15]}... 请求超时")
            tried_keys.append(key)
            rotate_key()
            continue

        except Exception as e:
            print(f"Key {key[:15]}... 出错: {e}")
            last_error = str(e)
            tried_keys.append(key)
            rotate_key()
            continue

    # 所有 key 都失败
    print(f"Tavily API 调用失败，最后错误: {last_error}")
    return None


def search(query):
    """搜索函数"""
    result = call_tavily_with_rotation(query)
    if result:
        print(result)
    else:
        print("搜索失败")


def test_all_keys():
    """测试所有 key"""
    print("测试所有 Tavily API keys...")
    for i, key in enumerate(TAVILY_KEYS):
        status = "[OK] valid" if test_api_key(key) else "[FAIL] invalid"
        print(f"Key {i+1}: {key[:20]}... - {status}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法:")
        print("  python tavily_key_rotation.py search <query>")
        print("  python tavily_key_rotation.py test")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'search':
        if len(sys.argv) < 3:
            print("请提供搜索查询")
            sys.exit(1)
        search(' '.join(sys.argv[2:]))

    elif command == 'test':
        test_all_keys()

    else:
        print(f"未知命令: {command}")
        sys.exit(1)
