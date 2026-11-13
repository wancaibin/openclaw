---
name: ai-news-qqbot
description: >-
  通过 bird 工具从用户的 X (Twitter) 时间线检索最新动态与 AI 资讯，直接读取完整推文及引用讨论全文（不截断），通过 TTS 转为自然语音音频，并推送音频到绑定的 QQ 机器人（仅发送音频，不发送文字）。
---

# X 时间线资讯全文读取、TTS 语音播报与 QQ 机器人推送

该技能自动化执行以下完整流程：
1. **个人 X 时间线检索（基于 bird 工具）**：通过 `bird` 命令行工具读取当前登录用户的 X (Twitter) Home 时间线（优先筛选 AI 前沿动态及核心讨论）。
2. **推文全文直读与翻译**：完整提取推文正文、作者信息、引用推文（Quote Tweet）及讨论全文，完整翻译为中文（若为外语）。
3. **TTS 语音合成**：使用 edge-tts 生成高质量中文自然语音音频文件（MP3）。
4. **QQ 机器人推送**：
   - 调用专用脚本将音频文件（以语音/文件格式）推送到绑定的 QQ 机器人。
   - （仅发送音频，不发送文字版资讯）。

---

## 执行步骤

### 1. 使用 bird 工具抓取个人 X 时间线

使用 `bird` CLI 获取主页关注动态与时间线：

```bash
# 获取 Home 时间线并输出 JSON
bird home --count 30 --json
```

若需仅抓取关注者时间线，可添加 `--following` 参数：
```bash
bird home --following --count 30 --json
```

### 2. 生成播报稿并合成语音

将时间线上的高价值资讯提取完整内容并翻译为适合朗读的播报稿（保存至临时文件 `/tmp/ai_news.txt`），要求：
- 口语化、自然流畅；
- 去掉一头一尾的套话（如开场白、结束语等），去掉推文作者与推文标题，直接朗读推文核心内容与引用补充；
- 避免复杂的 URL 链接与特殊字符。

执行 `edge-tts` 进行语音转换：
```bash
/Users/wcb/.local/bin/edge-tts --voice zh-CN-XiaoxiaoNeural -f /tmp/ai_news.txt --write-media /tmp/ai_news.mp3
```

### 3. 推送音频至 QQ 机器人

使用内置封装的上传推送脚本进行推送（基于 Hermes 虚拟环境与 QQ 开放平台 API）：
```bash
/Users/wcb/.hermes/hermes-agent/venv/bin/python3 ~/.gemini/config/skills/ai-news-qqbot/scripts/send_qq_media.py /tmp/ai_news.mp3 "X时间线动态简报.mp3"
```

### 4. 发送文字版速览

通过 Hermes 发送配套的文字版要点摘要，方便用户快速阅读：
```bash
hermes send --to qqbot "📢 X 时间线最新动态速递（语音已发送至上方，以下为要点文字版）：\n\n1. ...\n2. ..."
```

---

## 依赖与环境说明

- **X CLI 工具**：`bird` (`/opt/homebrew/bin/bird`)，自动读取 `~/.birdrc.json5` 或 `~/.config/bird/config.json5` 中的认证凭证 (`AUTH_TOKEN`, `CT0`)。
- **Python 环境**：`/Users/wcb/.hermes/hermes-agent/venv/bin/python3`
- **TTS 工具**：`/Users/wcb/.local/bin/edge-tts` (声音模型推荐 `zh-CN-XiaoxiaoNeural` 或 `zh-CN-YunxiNeural`)
- **配置文件**：`/Users/wcb/.hermes/.env` (包含 `QQ_APP_ID`, `QQ_CLIENT_SECRET`, `QQBOT_HOME_CHANNEL`)
- **自动化执行脚本**：[run_ai_news.py](./scripts/run_ai_news.py)
- **推送脚本**：[send_qq_media.py](./scripts/send_qq_media.py)
