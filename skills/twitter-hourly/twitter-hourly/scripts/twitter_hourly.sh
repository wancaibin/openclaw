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
proxychains4 -q bird home -n 100 --auth-token "$AUTH_TOKEN" --ct0 "$CT0" > x.md 2>&1

if [ $? -ne 0 ] || [ ! -s x.md ]; then
    echo "❌ 获取 Twitter 数据失败"
    cat x.md
    exit 1
fi

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
