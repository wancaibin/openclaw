#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 中文推文搜索脚本
每 2 小时自动搜索 X 上关于 openclaw 的中文推文
"""

import httpx
import json
import re
import sys
from datetime import datetime

# 配置
AUTH_TOKEN = "0a737b6b0c06801bbded3102464c411f76a7f480"
CT0 = "cae02b7d96fe7c51e36503b85b92b7541528c656aa7f0cb7f234ea64c63138c2ff46eb55d937d48dac9757d47272ffa8025963561c60c0fae79638863566a562e1d4b201e1566920bc943aaafb2411a3"
PROXY = "socks5://127.0.0.1:10808"
SEARCH_KEYWORD = "openclaw"
COUNT = 100

def is_chinese(text):
    """检查文本是否包含中文字符"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def search_tweets():
    """搜索包含 openclaw 的中文推文"""
    
    cookies = {
        'auth_token': AUTH_TOKEN,
        'ct0': CT0
    }

    headers = {
        'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'x-twitter-active-user': 'yes',
        'x-twitter-client-language': 'zh-cn',
        'x-csrf-token': CT0,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    # 获取时间线
    url = 'https://x.com/i/api/graphql/edseUwk9sP5Phz__9TIRnA/HomeTimeline'
    params = {
        'variables': json.dumps({
            'count': COUNT,
            'includePromotedContent': True,
            'latestControlAvailable': True,
            'requestContext': 'launch',
            'withCommunity': True
        })
    }

    try:
        with httpx.Client(cookies=cookies, headers=headers, timeout=30.0, proxy=PROXY) as client:
            response = client.get(url, params=params)
            if response.status_code != 200:
                print(f"❌ 请求失败：{response.status_code}")
                return []
            
            data = response.json()
            instructions = data.get('data', {}).get('home', {}).get('home_timeline_urt', {}).get('instructions', [])
            
            tweets = []
            for instruction in instructions:
                entries = instruction.get('entries', [])
                for entry in entries:
                    content = entry.get('content', {})
                    item_content = content.get('itemContent', {})
                    tweet_results = item_content.get('tweet_results', {})
                    result = tweet_results.get('result', {})
                    
                    if result.get('__typename') == 'Tweet':
                        tweet_text = result.get('legacy', {}).get('full_text', '')
                        user = result.get('core', {}).get('user_results', {}).get('result', {}).get('legacy', {})
                        screen_name = user.get('screen_name', 'unknown')
                        name = user.get('name', 'unknown')
                        created_at = result.get('legacy', {}).get('created_at', '')
                        
                        # 只过滤包含中文的推文
                        if tweet_text and is_chinese(tweet_text):
                            # 清理文本
                            tweet_text = re.sub(r'https?://t\.co/\w+', '', tweet_text)
                            tweet_text = re.sub(r'[\U00010000-\U00010ffff]', '', tweet_text)
                            tweets.append({
                                'user': f"@{screen_name} ({name})",
                                'time': created_at,
                                'text': tweet_text.strip()
                            })
            
            return tweets
            
    except Exception as e:
        print(f"❌ 错误：{e}")
        return []

def main():
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    output_dir = '/Users/wcb/.openclaw/workspace/output'
    output_file = f'{output_dir}/openclaw_tweets_{timestamp}.txt'
    latest_file = f'{output_dir}/openclaw_tweets_latest.txt'
    
    # 创建输出目录
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"🔍 开始搜索 OpenClaw 中文推文... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n")
    
    tweets = search_tweets()
    
    # 准备输出内容
    output_content = []
    output_content.append(f"OpenClaw 中文推文搜索报告")
    output_content.append(f"搜索时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_content.append(f"搜索关键词：{SEARCH_KEYWORD}")
    output_content.append(f"找到推文数：{len(tweets)}")
    output_content.append("=" * 80)
    output_content.append("")
    
    if not tweets:
        output_content.append("本次未发现新的 OpenClaw 中文推文")
        print("本次未发现新的 OpenClaw 中文推文")
    else:
        print(f"✅ 找到 {len(tweets)} 条关于 '{SEARCH_KEYWORD}' 的中文推文:\n")
        print("=" * 80)
        
        for i, t in enumerate(tweets, 1):
            tweet_text = f"\n{i}. {t['user']} - {t['time'][:16]}\n   {t['text']}"
            output_content.append(tweet_text)
            print(tweet_text)
        
        print("\n" + "=" * 80)
        print(f"搜索完成！共 {len(tweets)} 条推文")
    
    output_content.append("")
    output_content.append("=" * 80)
    output_content.append(f"搜索完成！共 {len(tweets)} 条推文")
    
    # 保存到文件
    final_content = "\n".join(output_content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print(f"\n📄 结果已保存到：{output_file}")
    
    # 同时更新最新结果文件
    with open(latest_file, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print(f"📄 最新结果已更新：{latest_file}")

if __name__ == "__main__":
    main()
