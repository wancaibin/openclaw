#!/bin/bash
# 抓取 YouTube 推荐视频（中文标题）+ 生成摘要
# 需要先导出 YouTube cookie 到 ~/.openclaw/workspace/youtube_cookies.txt

COOKIE_FILE="$HOME/.openclaw/workspace/youtube_cookies.txt"
OUTPUT_DIR="$HOME/.openclaw/workspace/youtube-recommended"

# 代理配置
export http_proxy="http://127.0.0.1:10808"
export https_proxy="http://127.0.0.1:10808"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
OUTPUT_FILE="$OUTPUT_DIR/recommended_$TIMESTAMP.md"

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 检查 cookie 文件或浏览器
COOKIE_ARG=""
if [ -f "$COOKIE_FILE" ]; then
    COOKIE_ARG="--cookies $COOKIE_FILE"
    echo "使用 Cookie 文件：$COOKIE_FILE"
else
    COOKIE_ARG="--cookies-from-browser chrome"
    echo "使用 Chrome 浏览器 Cookie"
fi

echo "📺 抓取 YouTube 推荐视频..."
echo "时间：$(date)"
echo "---"

# 创建临时文件
TEMP_FILE=$(mktemp)

# 使用 yt-dlp 获取推荐视频列表（只获取标题和 URL）
yt-dlp $COOKIE_ARG \
    --flat-playlist \
    --print "%(title)s	%(url)s" \
    "https://www.youtube.com/feed/recommended" \
    2>/dev/null > "$TEMP_FILE"

# 输出文件头
echo "# YouTube 推荐视频 - $(date +"%Y-%m-%d %H:%M")" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# 处理每个视频
count=0
while IFS=$'\t' read -r title url; do
    # 跳过空值
    [ -z "$title" ] && continue
    [ -z "$url" ] && continue
    
    # 检查是否包含中文字符（兼容 macOS）
    if echo "$title" | grep -E '[一 - 龥]' > /dev/null; then
        count=$((count + 1))
        echo "## $title" >> "$OUTPUT_FILE"
        echo "**链接**: $url" >> "$OUTPUT_FILE"
        
        # 获取视频详情（包括描述）
        echo "   正在获取视频 $count 详情..."
        video_info=$(yt-dlp $COOKIE_ARG \
            --dump-json \
            "$url" \
            2>/dev/null)
        
        # 提取描述并生成摘要
        description=$(echo "$video_info" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    desc = data.get('description', '') or ''
    # 截取前 300 字符
    if len(desc) > 300:
        print(desc[:300] + '...')
    elif desc:
        print(desc)
except:
    pass
" 2>/dev/null)
        
        if [ -n "$description" ]; then
            echo "" >> "$OUTPUT_FILE"
            echo "**摘要**: $description" >> "$OUTPUT_FILE"
        fi
        
        echo "" >> "$OUTPUT_FILE"
        
        # 限制处理数量（前 20 个中文视频）
        [ $count -ge 20 ] && break
    fi
done < "$TEMP_FILE"

# 清理临时文件
rm -f "$TEMP_FILE"

echo "---"
echo "✅ 完成！共处理 $count 个视频"
echo "输出文件：$OUTPUT_FILE"

# 显示文件内容
cat "$OUTPUT_FILE"

# 发送邮件到 QQ 邮箱
echo ""
echo "📧 正在发送邮件到 QQ 邮箱..."
python3 << PYTHON_SCRIPT
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from datetime import datetime

# 配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "370583129@qq.com"
SMTP_PASS = "lqcptvkryrrubgde"
RECIPIENT = "370583129@qq.com"
ATTACHMENT_PATH = "$OUTPUT_FILE"

try:
    # 创建邮件
    msg = MIMEMultipart('alternative')
    msg['From'] = SMTP_USER
    msg['To'] = RECIPIENT
    
    # 主题
    subject = f'YouTube 推荐视频 - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    msg['Subject'] = Header(subject, 'utf-8')
    
    # 邮件正文
    body = f"""
YouTube 推荐视频抓取完成！

抓取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
共抓取 {count} 个中文视频，每条包含摘要。
视频列表请查看附件。

---
此邮件由 OpenClaw 定时任务自动发送
    """
    part1 = MIMEText(body, 'plain', 'utf-8')
    msg.attach(part1)
    
    # 添加附件
    with open(ATTACHMENT_PATH, 'rb') as f:
        attachment = MIMEBase('text', 'plain')
        attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        filename = f'youtube_recommended_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}.md'
        attachment.add_header('Content-Disposition', 'attachment', 
                             filename=('utf-8', '', filename))
        msg.attach(attachment)
    
    # 发送
    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    server.login(SMTP_USER, SMTP_PASS)
    server.sendmail(SMTP_USER, [RECIPIENT], msg.as_string())
    server.quit()
    print("✅ 邮件发送成功！")
except Exception as e:
    print(f"❌ 邮件发送失败：{e}")
PYTHON_SCRIPT
