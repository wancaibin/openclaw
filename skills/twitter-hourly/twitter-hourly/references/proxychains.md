# Proxychains 配置指南

## 安装

```bash
brew install proxychains-ng
```

## 配置文件

配置文件位于：`/opt/homebrew/etc/proxychains.conf`

### 基本配置

```bash
# 编辑配置
sudo vim /opt/homebrew/etc/proxychains.conf
```

### 链模式选择

```bash
# 推荐：动态链（按顺序尝试，直到成功）
dynamic_chain

# 或：严格链（所有代理必须在线）
# strict_chain

# 或：随机链（随机选择代理）
# random_chain
```

### 代理配置

```bash
[ProxyList]
# 注释掉默认的 tor 配置
# socks4 127.0.0.1 9050

# 添加你的代理
socks5 127.0.0.1 10808
```

### 常见代理类型

| 类型 | 格式 | 示例 |
|------|------|------|
| SOCKS5 | `socks5 host port [user pass]` | `socks5 127.0.0.1 10808` |
| SOCKS4 | `socks4 host port [user]` | `socks4 127.0.0.1 9050` |
| HTTP | `http host port [user pass]` | `http 127.0.0.1 7890` |
| Raw | `raw host port` | `raw 127.0.0.1 8080` |

## 使用方法

### 基本用法

```bash
# 在命令前加 proxychains4 -q
proxychains4 -q curl https://x.com
proxychains4 -q bird home -n 100
```

### 静默模式

```bash
# -q 减少输出（推荐）
proxychains4 -q <command>
```

### 测试代理

```bash
# 测试连接
proxychains4 -q curl -I https://x.com

# 检查 IP
proxychains4 -q curl https://api.ip.sb/ip
```

## 故障排查

### 无法连接

```bash
# 检查代理是否运行
curl --socks5-hostname 127.0.0.1:10808 -I https://x.com

# 检查配置文件
cat /opt/homebrew/etc/proxychains.conf | grep -v "^#" | grep -v "^$"

# 测试 proxychains
proxychains4 -q curl -I https://google.com
```

### DNS 泄漏

确保配置中包含：

```bash
# 在 proxychains.conf 中
proxy_dns
```

### 性能问题

- 使用 `dynamic_chain` 而非 `strict_chain`
- 移除不可用的代理
- 考虑使用更快的代理服务器

## 与鸟 (bird) 配合使用

```bash
# 设置环境变量
export AUTH_TOKEN="your_token"
export CT0="your_ct0"

# 运行 bird
proxychains4 -q bird home -n 100 --auth-token "$AUTH_TOKEN" --ct0 "$CT0"
```

## 安全提示

- 仅使用可信的代理服务器
- 代理可能记录你的流量
- 敏感操作使用 HTTPS
- 定期检查代理是否正常工作
