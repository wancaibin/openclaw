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
    for i, item in enumerate(new_items[:5]):
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
    PROMPT="请将以下几条最新还未播报过的外网新闻翻译并总结成流畅自然的中文语音播报稿。要求：1. 必须全中文，遇到专有名词或者公司名可以音译或意译；2. 语气像朋友聊天一样自然，开头用'铁狗蛋，最新5分钟的科技猛料来啦：'，依次生动播报；3. 直接给出最终的纯中文稿本，不要解释。\n\n$RAW_TEXT"
    
    openclaw infer model run --model custom-127-0-0-1-7861/gemini-pro-agent --prompt "$PROMPT" --json > /tmp/cron_agent_news_infer.json
    cat /tmp/cron_agent_news_infer.json | jq -r '.outputs[0].text' > /tmp/cron_agent_news.txt
    /Users/wcb/.openclaw/workspace/scripts/text_to_speech.py /tmp/cron_agent_news.txt /tmp/cron_agent_news.mp3
    echo "SUCCESS"
else
    echo "NO_NEW_NEWS"
fi
