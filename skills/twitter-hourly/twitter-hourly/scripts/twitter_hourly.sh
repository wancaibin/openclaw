#!/bin/bash
# Twitter Home Timeline 每小时抓取并发送邮件

set -e

WORKSPACE="/Users/wcb/.openclaw/workspace"
cd "$WORKSPACE"

echo "🐦 开始抓取 Twitter Home Timeline..."

# 获取 Twitter 凭据（从钥匙串）
AUTH_TOKEN=$(security find-generic-password -a "370583129@qq.com" -s "twitter-auth-token" -w 2>/dev/null || echo "")
CT0=$(security find-generic-password -a "370583129@qq.com" -s "twitter-ct0" -w 2>/dev/null || echo "")

if [ -z "$AUTH_TOKEN" ] || [ -z "$CT0" ]; then
    echo "❌ 缺少 Twitter 凭据，请设置钥匙串项："
    echo "   security add-generic-password -a \"370583129@qq.com\" -s \"twitter-auth-token\" -w \"YOUR_AUTH_TOKEN\""
    echo "   security add-generic-password -a \"370583129@qq.com\" -s \"twitter-ct0\" -w \"YOUR_CT0\""
    exit 1
fi

# 使用 proxychains4 通过代理获取 Twitter
echo "📡 通过代理获取 Twitter 数据..."
proxychains4 -q bird home -n 100 --auth-token "$AUTH_TOKEN" --ct0 "$CT0" > x_raw.md 2>&1

if [ $? -ne 0 ] || [ ! -s x_raw.md ]; then
    echo "❌ 获取 Twitter 数据失败"
    cat x_raw.md
    exit 1
fi

# 过滤：只保留中文推文正文（去掉用户名、分隔线、图片链接、时间、链接、日语等）
echo "🧹 过滤非正文内容..."
python3 << 'EOF'
import re

def is_mostly_chinese(text):
    """检查文本是否主要为中文（排除日语）"""
    # 中文字符范围
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    # 日语平假名、片假名范围
    japanese_hiragana = re.findall(r'[\u3040-\u309f]', text)
    japanese_katakana = re.findall(r'[\u30a0-\u30ff]', text)
    
    total_cjk = len(chinese_chars) + len(japanese_hiragana) + len(japanese_katakana)
    if total_cjk == 0:
        return False
    
    # 如果有日语字符，且日语字符占比超过 20%，则认为是日语
    japanese_ratio = (len(japanese_hiragana) + len(japanese_katakana)) / total_cjk
    if japanese_ratio > 0.2:
        return False
    
    # 中文字符占比超过 50% 则认为是中文
    chinese_ratio = len(chinese_chars) / total_cjk
    return chinese_ratio >= 0.5

with open('x_raw.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 按分隔符分割推文
tweets = re.split(r'─{10,}', content)

cleaned = []
for tweet in tweets:
    lines = tweet.strip().split('\n')
    text_lines = []
    for line in lines:
        line = line.strip()
        # 跳过空行
        if not line:
            continue
        # 跳过用户名行 (@xxx (xxx):)
        if re.match(r'^@\w+\s*\(', line):
            continue
        # 跳过图片/视频链接 (🎬 🖼️ 📸)
        if line.startswith('🎬') or line.startswith('🖼️') or line.startswith('📸'):
            continue
        # 跳过时间行 (📅)
        if line.startswith('📅'):
            continue
        # 跳过链接行 (🔗)
        if line.startswith('🔗'):
            continue
        # 跳过分隔线
        if re.match(r'^─{10,}$', line):
            continue
        # 去掉 t.co 短链接
        line = re.sub(r'\s*https?://t\.co/\w+', '', line)
        # 去掉 📰 等前缀
        line = re.sub(r'^[📰🎬🖼️📸🔗📅]\s*', '', line)
        # 跳过处理后的空行
        if not line.strip():
            continue
        # 保留正文
        text_lines.append(line.strip())
    
    # 检查整条推文是否主要为中文
    if text_lines:
        tweet_text = ' '.join(text_lines)
        if is_mostly_chinese(tweet_text):
            cleaned.append('\n'.join(text_lines))

# 写入过滤后的文件
with open('x.md', 'w', encoding='utf-8') as f:
    f.write('\n\n──────────────────────────────────────────────────\n\n'.join(cleaned))

print(f"✅ 过滤完成，保留 {len(cleaned)} 条中文推文")
EOF

rm -f x_raw.md

LINES=$(wc -l < x.md)
echo "✅ 成功获取 $LINES 行 Twitter 数据"

# 发送邮件
echo "📧 发送邮件..."
python3 "$WORKSPACE/scripts/send_twitter_email.py" "$(date +%Y-%m-%d_%H:%M)"

if [ $? -eq 0 ]; then
    echo "✅ 邮件发送成功！"
    echo "📅 完成时间：$(date)"
else
    echo "❌ 邮件发送失败"
    exit 1
fi
