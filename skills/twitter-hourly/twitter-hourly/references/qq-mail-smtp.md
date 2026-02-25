# QQ 邮箱 SMTP 配置

## 开启 SMTP 服务

1. 登录 https://mail.qq.com
2. 点击 **设置** → **账户**
3. 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务**
4. 开启 **IMAP/SMTP 服务**
5. 按提示发送短信验证
6. 获取 **授权码**（16 位字母，无空格）

## SMTP 配置

| 配置项 | 值 |
|--------|-----|
| SMTP 服务器 | smtp.qq.com |
| SMTP 端口（SSL） | 465 |
| SMTP 端口（TLS） | 587 |
| IMAP 服务器 | imap.qq.com |
| IMAP 端口 | 993 |
| 用户名 | 完整 QQ 邮箱地址 |
| 密码 | 授权码（非 QQ 密码） |

## 存储到钥匙串

```bash
# 替换 YOUR_EMAIL 和 YOUR_AUTH_CODE 为实际值
security add-generic-password \
  -a "YOUR_EMAIL@qq.com" \
  -s "himalaya-imap-qq" \
  -w "YOUR_AUTH_CODE"
```

## 测试连接

```bash
# 使用 himalaya 测试
himalaya account doctor qq

# 或手动测试
python3 -c "
import smtplib
server = smtplib.SMTP_SSL('smtp.qq.com', 465)
server.login('YOUR_EMAIL@qq.com', 'YOUR_AUTH_CODE')
print('连接成功！')
server.quit()
"
```

## 常见问题

### 502 Invalid parameters

- 检查发件人地址格式是否正确
- 确保使用授权码而非 QQ 密码
- 尝试使用 SSL 端口 465

### 535 Authentication failed

- 授权码错误
- 重新获取授权码（QQ 邮箱 → 设置 → 账户）
- 检查是否开启了 SMTP 服务

### 550 From header is missing or invalid

- 确保 From 头包含完整邮箱地址
- 格式：`From: Name <email@qq.com>`
- 避免使用特殊字符或 emoji 在发件人名称中

## 安全提示

- 授权码等同于密码，妥善保管
- 定期更换授权码
- 不要在代码中硬编码授权码
- 使用钥匙串或环境变量存储
