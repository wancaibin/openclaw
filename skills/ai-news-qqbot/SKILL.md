---
name: ai-news-qqbot
description: >-
  搜索 X (Twitter)、Reddit、Hacker News (HN)、GitHub Trending、ArXiv 及主流技术媒体等全网人工智能 (AI) 最新动态，整理为新闻播报稿，通过 TTS 转为音频，并直接推送音频与文字摘要到绑定的 QQ 机器人。适用于用户需要获取每日/即时 AI 资讯播报并推送到 QQ 机器人的场景。
---

# AI 资讯检索、TTS 语音播报与 QQ 机器人推送

该技能自动化执行以下完整流程：
1. **多源检索**：在 X (Twitter)、Reddit、Hacker News (HN)、GitHub、ArXiv 等多渠道检索最新的 AI 技术、行业动态与热点讨论。
2. **文本生成**：梳理并编写结构清晰、适合语音播报的中文简报稿件（分段、去外链与特殊符号）。
3. **TTS 语音合成**：使用 edge-tts 生成高质量中文自然语音音频文件（MP3）。
4. **QQ 机器人推送**：
   - 调用专用脚本将音频文件（以语音/文件格式）推送到绑定的 QQ 机器人。
   - 通过 `hermes send --to qqbot` 发送图文/文字版要点速览。

---

## 执行步骤

### 1. 多源搜索最新 AI 资讯

使用 `search_web` 工具检索多渠道的最新热点（可根据需要组合查询）：

- **X (Twitter) 趋势检索**：
  `query: "site:x.com OR site:twitter.com AI news OR LLM OR OpenAI OR Claude OR Anthropic"`
- **Reddit 社区热点**：
  `query: "site:reddit.com/r/ArtificialInteligence OR site:reddit.com/r/LocalLLaMA OR site:reddit.com/r/singularity OR site:reddit.com/r/MachineLearning AI latest"`
- **Hacker News (HN) 技术热议**：
  `query: "site:news.ycombinator.com AI OR LLM OR GPT OR OpenAI OR Anthropic"`
- **GitHub Trending / 开源前沿**：
  `query: "site:github.com trending AI OR LLM OR agent"`
- **前沿论文与技术动态 (ArXiv / HuggingFace)**：
  `query: "site:arxiv.org OR site:huggingface.co/papers AI LLM"`

### 2. 生成播报稿并合成语音

将资讯提炼为适合朗读的播报稿（保存至临时文件 `/tmp/ai_news.txt`），要求：
- 口语化、自然流畅；
- 提炼 3~4 个核心模块（例如：大模型突破、开源社区热点、行业趋势与商业落地）；
- 避免复杂的 URL 链接与特殊字符。

执行 `edge-tts` 进行语音转换：
```bash
/Users/wcb/.local/bin/edge-tts --voice zh-CN-XiaoxiaoNeural -f /tmp/ai_news.txt --write-media /tmp/ai_news.mp3
```

### 3. 推送音频至 QQ 机器人

使用内置封装的上传推送脚本进行推送（基于 Hermes 虚拟环境与 QQ 开放平台 API）：
```bash
/Users/wcb/.hermes/hermes-agent/venv/bin/python3 ~/.gemini/config/skills/ai-news-qqbot/scripts/send_qq_media.py /tmp/ai_news.mp3 "AI最新动态简报.mp3"
```

### 4. 发送文字版速览

通过 Hermes 发送配套的文字版要点摘要，方便用户快速阅读：
```bash
hermes send --to qqbot "📢 今日 AI 最新动态简报（语音已发送至上方，以下为要点文字版）：\n\n1. ...\n2. ..."
```

---

## 依赖与环境说明

- **Python 环境**：`/Users/wcb/.hermes/hermes-agent/venv/bin/python3`
- **TTS 工具**：`/Users/wcb/.local/bin/edge-tts` (声音模型推荐 `zh-CN-XiaoxiaoNeural` 或 `zh-CN-YunxiNeural`)
- **配置文件**：`/Users/wcb/.hermes/.env` (包含 `QQ_APP_ID`, `QQ_CLIENT_SECRET`, `QQBOT_HOME_CHANNEL`)
- **推送脚本**：[send_qq_media.py](./scripts/send_qq_media.py)
