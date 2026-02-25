---
name: twitter-hourly
description: 定时抓取 Twitter Home Timeline 并发送邮件。支持通过 SOCKS5 代理获取数据，自动发送带附件的邮件。Use when setting up automated Twitter monitoring, hourly timeline抓取，或需要定时邮件通知的 Twitter 数据同步任务。
---

# Twitter Hourly Timeline 技能

## 快速开始

### 安装依赖

确保以下工具已安装：

```bash
# proxychains-ng（用于代理）
brew install proxychains-ng

# bird（Twitter CLI）
npm install -g bird

# Python 3（邮件发送）
python3 --version
```

### 配置代理

编辑 `/opt/homebrew/etc/proxychains.conf`：

```bash
# 注释掉默认的 tor 配置
# socks4 127.0.0.1 9050

# 添加你的 SOCKS5 代理
socks5 127.0.0.1 10808
```

### 设置凭据

将 Twitter 和邮件凭据存储到 macOS 钥匙串：

```bash
# Twitter API 凭据（从浏览器 Cookie 获取）
security add-generic-password -a "your_email@qq.com" -s "twitter-auth-token" -w "YOUR_AUTH_TOKEN"
security add-generic-password -a "your_email@qq.com" -s "twitter-ct0" -w "YOUR_CT0"

# 邮件密码（SMTP/IMAP）
security add-generic-password -a "your_email@qq.com" -s "himalaya-imap-qq" -w "YOUR_SMTP_PASSWORD"
```

### 运行脚本

```bash
# 手动执行一次
./scripts/twitter_hourly.sh

# 或指定输出目录
cd /your/workspace && ./scripts/twitter_hourly.sh
```

## 设置定时任务

### 方式 1：使用 OpenClaw Cron

```bash
cron add --job '{
  "name": "Twitter Hourly Timeline",
  "schedule": {"kind": "cron", "expr": "0 * * * *", "tz": "Asia/Shanghai"},
  "payload": {"kind": "agentTurn", "message": "执行 Twitter 抓取脚本", "timeoutSeconds": 300},
  "sessionTarget": "isolated"
}'
```

### 方式 2：使用系统 Crontab

```bash
(crontab -l 2>/dev/null; echo "0 * * * * /path/to/scripts/twitter_hourly.sh >> /path/to/logs/twitter.log 2>&1") | crontab -
```

## 脚本说明

### twitter_hourly.sh

主脚本，执行以下操作：

1. 从钥匙串获取 Twitter 凭据
2. 通过 proxychains4 + bird 抓取 Home Timeline（100 条）
3. 调用 Python 脚本发送邮件
4. 输出执行日志

### send_twitter_email.py

邮件发送脚本：

- **SMTP**: smtp.qq.com:465 (SSL)
- **内容**: 正文包含前 50 条预览，附件为完整 x.md
- **收件人**: 默认发送到配置邮箱

## 获取 Twitter 凭据

1. 在浏览器（Safari/Chrome/Firefox）登录 x.com
2. 打开开发者工具 → Application/Storage → Cookies
3. 复制 `auth_token` 和 `ct0` 值
4. 存入钥匙串（见上方配置步骤）

**注意**: 凭据会过期，如抓取失败请重新获取。

## 故障排查

### 获取 Twitter 数据失败

```bash
# 检查代理是否运行
curl --socks5-hostname 127.0.0.1:10808 -I https://x.com

# 检查 bird 是否安装
bird --version

# 检查凭据是否正确
security find-generic-password -a "your_email@qq.com" -s "twitter-auth-token" -w
```

### 邮件发送失败

```bash
# 检查 SMTP 密码
security find-generic-password -a "your_email@qq.com" -s "himalaya-imap-qq" -w

# 测试邮件发送
python3 scripts/send_twitter_email.py
```

### 代理配置问题

```bash
# 测试 proxychains4
proxychains4 -q curl -I https://x.com
```

## 管理定时任务

```bash
# 查看任务
cron list

# 立即执行
cron run --jobId <JOB_ID>

# 禁用/启用
cron update --jobId <JOB_ID> --patch '{"enabled": false}'
cron update --jobId <JOB_ID> --patch '{"enabled": true}'

# 删除任务
cron remove --jobId <JOB_ID>
```

## 输出文件

- **x.md**: Twitter 数据文件（100 条动态）
- **logs/twitter_hourly.log**: 执行日志（如配置）

## 参考文档

- [Twitter Cookie 获取](references/twitter-cookies.md)
- [QQ 邮箱 SMTP 配置](references/qq-mail-smtp.md)
- [Proxychains 配置](references/proxychains.md)
