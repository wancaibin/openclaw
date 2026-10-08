#!/bin/bash
export PATH=$PATH:/Users/wcb/.local/bin:/opt/homebrew/bin:/usr/local/bin

HISTORY_FILE="/tmp/news_history.txt"
touch $HISTORY_FILE

xreach search "breaking news OR AI OR Tech min_faves:200" -n 60 --json > /tmp/cron_agent_news.json

python3 -c "
import json, sys
try:
    with open('/tmp/cron_agent_news.json', 'r') as f: data = json.load(f)
    with open('$HISTORY_FILE', 'r') as f: history = set(f.read().splitlines())
    items = data.get('items', [])
    new_items = [item for item in items if str(item.get('id')) not in history]
    if not new_items: sys.exit(1)
    text = ''
    new_history = []
    # 控制每次精选最多 2-3 条短新闻，确保播报长度在 60 秒以内，防止 QQBot 平台端传输或播放截断
    for i, item in enumerate(new_items[:3]):
        text += f'新闻{i+1}: {item.get(\"text\", \"\")} \n\n'
        new_history.append(str(item.get('id')))
    with open('/tmp/cron_agent_news_raw.txt', 'w') as f: f.write(text)
    with open('$HISTORY_FILE', 'a') as f:
        for h in new_history: f.write(h + '\n')
except Exception as e:
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    RAW_TEXT=$(cat /tmp/cron_agent_news_raw.txt)
    PROMPT="请将以下外网新闻精简总结成流畅自然的中文语音播报短稿。严格要求：1. 控制在200到300字以内（语速适中，时长约50秒左右，严禁过长）；2. 必须全中文，专有名词可音译或意译；3. 语气像老朋友聊天，开头统一用'铁狗蛋，最新科技猛料来啦：'，自然精炼播报；4. 直接给出最终纯中文稿本，不要解释。\n\n$RAW_TEXT"
    
    openclaw infer model run --model custom-127-0-0-1-7861/gemini-3.8-flash-tiered --prompt "$PROMPT" --json > /tmp/cron_agent_news_infer.json
    cat /tmp/cron_agent_news_infer.json | jq -r '.outputs[0].text' > /tmp/cron_agent_news.txt
    /Users/wcb/.openclaw/workspace/scripts/text_to_speech.py /tmp/cron_agent_news.txt /tmp/cron_agent_news.mp3
    echo "SUCCESS"
else
    echo "NO_NEW_NEWS"
fi
