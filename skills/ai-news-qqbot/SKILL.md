---
name: ai-news-qqbot
description: >-
  搜索 X (Twitter)、Reddit、Hacker News (HN)、TechCrunch、The Verge、GitHub Trending、ArXiv 及 Hugging Face 等全网人工智能 (AI) 最新动态，直接读取完整文章与资讯全文（不再进行摘要截取），通过 TTS 转为完整自然语音音频，并直接推送音频与完整图文内容到绑定的 QQ 机器人。适用于用户需要获取每日/即时 AI 完整深度资讯播报并推送到 QQ 机器人的场景。
---

# AI 资讯完整全文读取、TTS 语音播报与 QQ 机器人推送

该技能自动化执行以下完整流程：
1. **多源深度检索**：在 TechCrunch、The Verge、Hacker News、ArXiv cs.AI、Hugging Face 等渠道检索最新的 AI 技术、行业动态与热点讨论。
2. **全文直读与翻译**：直接抓取文章与资讯的完整网页正文及论文 Abstract 全文（不再进行摘要截断），完整翻译为中文。
3. **TTS 语音合成**：使用 edge-tts 生成高质量中文自然语音音频文件（MP3）。
4. **QQ 机器人推送**：
   - 调用专用脚本将音频文件（以语音/文件格式）推送到绑定的 QQ 机器人。
   - 通过 `hermes send --to qqbot` 发送完整文字版资讯内容（超长自动分段发送）。

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
