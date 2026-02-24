---
name: x-tweet-search
description: Search X (Twitter) for tweets by keyword, filter by language, and email results. Use when users want to monitor social media mentions, track brand sentiment, or collect tweets about specific topics.
---

# X Tweet Search + Email

Automated X (Twitter) search skill that finds tweets by keyword, filters by language, saves results to files, and optionally emails a report.

## Quick Start

Run the search script:

```bash
python3 /Users/wcb/.openclaw/workspace/skills/x-tweet-search/scripts/search_and_email.py
```

## Configuration

Edit the script to customize:

| Setting | Variable | Default |
|---------|----------|---------|
| Search keyword | `SEARCH_KEYWORD` | `"openclaw"` |
| Tweet count | `COUNT` | `100` |
| SMTP server | `SMTP_SERVER` | `"smtp.qq.com"` |
| SMTP port | `SMTP_PORT` | `465` |
| Sender email | `SMTP_USER` | `"370583129@qq.com"` |
| Sender password | `SMTP_PASS` | (需要 QQ 邮箱授权码) |
| Recipient | `RECIPIENT` | `"370583129@qq.com"` |
| Proxy | `PROXY` | `"socks5://127.0.0.1:10808"` |

### QQ 邮箱授权码

1. 登录 QQ 邮箱网页版 (mail.qq.com)
2. 设置 → 账户 → POP3/IMAP/SMTP 服务
3. 开启 IMAP/SMTP 服务
4. 生成授权码（需短信验证）
5. 替换脚本中的 `SMTP_PASS`

## Output

- **带时间戳文件**: `/Users/wcb/.openclaw/workspace/output/openclaw_tweets_YYYY-MM-DD_HHMMSS.txt`
- **最新结果**: `/Users/wcb/.openclaw/workspace/output/openclaw_tweets_latest.txt`

## Cron Setup (Optional)

Add to crontab for hourly execution:

```bash
0 * * * * python3 /Users/wcb/.openclaw/workspace/skills/x-tweet-search/scripts/search_and_email.py
```

Or use OpenClaw cron:

```bash
openclaw cron add --name "X Tweet Search" --schedule "0 * * * *" --command "python3 /Users/wcb/.openclaw/workspace/skills/x-tweet-search/scripts/search_and_email.py"
```

## Notes

- Requires SOCKS5 proxy for X API access
- Only saves tweets containing Chinese characters
- Strips URLs and emojis from tweet text
- Email uses UTF-8 encoding for Chinese content
