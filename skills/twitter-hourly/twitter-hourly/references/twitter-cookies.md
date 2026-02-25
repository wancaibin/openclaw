# Twitter Cookie 获取指南

## 从 Safari 获取

1. 打开 Safari，登录 https://x.com
2. 按 `Cmd+Option+C` 打开开发者工具
3. 切换到 **Storage** 标签
4. 左侧展开 **Cookies** → **https://x.com**
5. 找到以下 Cookie：
   - `auth_token` - Twitter 认证令牌
   - `ct0` - CSRF 令牌
6. 双击值复制

## 从 Chrome 获取

1. 打开 Chrome，登录 https://x.com
2. 按 `F12` 或 `Cmd+Option+I` 打开开发者工具
3. 切换到 **Application** 标签
4. 左侧展开 **Cookies** → **https://x.com**
5. 找到 `auth_token` 和 `ct0`
6. 右键 → **Copy Value**

## 从 Firefox 获取

1. 打开 Firefox，登录 https://x.com
2. 按 `F12` 或 `Cmd+Option+I` 打开开发者工具
3. 切换到 **Storage** 标签
4. 左侧展开 **Cookies** → **https://x.com**
5. 找到 `auth_token` 和 `ct0`
6. 双击值复制

## 存储到钥匙串

```bash
# 替换 YOUR_EMAIL 和 YOUR_TOKEN 为实际值
security add-generic-password \
  -a "YOUR_EMAIL@qq.com" \
  -s "twitter-auth-token" \
  -w "YOUR_AUTH_TOKEN"

security add-generic-password \
  -a "YOUR_EMAIL@qq.com" \
  -s "twitter-ct0" \
  -w "YOUR_CT0"
```

## 验证凭据

```bash
# 读取凭据
security find-generic-password -a "YOUR_EMAIL@qq.com" -s "twitter-auth-token" -w
security find-generic-password -a "YOUR_EMAIL@qq.com" -s "twitter-ct0" -w
```

## 凭据过期

Twitter Cookie 会定期过期（通常几周到几个月）。如遇到以下错误，请重新获取：

- `Failed to fetch home timeline: Unable to connect`
- `Could not authenticate you`
- `This request requires a matching csrf cookie and header`

## 安全提示

⚠️ **不要分享你的 Cookie！**

- `auth_token` 和 `ct0` 等同于你的登录凭据
- 拥有这些值的人可以访问你的 Twitter 账户
- 仅存储在本地钥匙串中
- 不要提交到 Git 或公开仓库
