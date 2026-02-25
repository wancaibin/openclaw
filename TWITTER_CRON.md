# Twitter 定时任务

## 任务说明

每小时自动抓取 Twitter Home Timeline 并发送邮件。

## 文件结构

```
/Users/wcb/.openclaw/workspace/scripts/
├── twitter_hourly.sh          # 主脚本（每小时执行）
├── send_twitter_email.py      # 邮件发送脚本
└── send_email.py              # 通用邮件脚本

/Users/wcb/.openclaw/workspace/
├── x.md                       # Twitter 数据输出文件
└── logs/
    └── twitter_hourly.log     # 执行日志（可选）
```

## Cron 配置

- **任务 ID**: `3ebc509d-62ba-40ab-a00c-ae2bfc209a4c`
- **执行时间**: 每小时整点（0 * * * *，Asia/Shanghai 时区）
- **下次执行**: 查看 `cron list` 的 `nextRunAtMs`

## 凭据管理

Twitter API 凭据存储在 macOS 钥匙串中：

```bash
# 查看凭据
security find-generic-password -a "370583129@qq.com" -s "twitter-auth-token" -w
security find-generic-password -a "370583129@qq.com" -s "twitter-ct0" -w

# 更新凭据（当过期时）
security add-generic-password -a "370583129@qq.com" -s "twitter-auth-token" -w "NEW_TOKEN"
security add-generic-password -a "370583129@qq.com" -s "twitter-ct0" -w "NEW_CT0"
```

## 手动执行

```bash
/Users/wcb/.openclaw/workspace/scripts/twitter_hourly.sh
```

## 邮件配置

- **收件人**: 370583129@qq.com
- **发件人**: OpenClaw <370583129@qq.com>
- **SMTP**: smtp.qq.com:465 (SSL)
- **内容**: 
  - 正文：前 50 条动态预览
  - 附件：x.md（完整 100 条动态）

## 故障排查

1. **获取 Twitter 数据失败**: 检查代理是否运行 (SOCKS5 127.0.0.1:10808)
2. **邮件发送失败**: 检查钥匙串中的 SMTP 密码
3. **凭据过期**: 从浏览器重新获取 auth_token 和 ct0

## 管理命令

```bash
# 查看定时任务
cron list

# 立即执行一次
cron run --jobId 3ebc509d-62ba-40ab-a00c-ae2bfc209a4c

# 禁用任务
cron update --jobId 3ebc509d-62ba-40ab-a00c-ae2bfc209a4c --patch '{"enabled": false}'

# 启用任务
cron update --jobId 3ebc509d-62ba-40ab-a00c-ae2bfc209a4c --patch '{"enabled": true}'

# 删除任务
cron remove --jobId 3ebc509d-62ba-40ab-a00c-ae2bfc209a4c
```

---
最后更新：2026-02-26
