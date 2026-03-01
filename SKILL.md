---
name: youtube-tts-translate
description: 下载YouTube视频字幕，翻译成中文，并用edge-tts生成中文语音，然后发送给用户。
---

# YouTube字幕翻译及语音生成技能

此技能自动化了从YouTube视频下载字幕、将其翻译成中文、并使用edge-tts工具生成中文语音的整个过程。最终生成的音频文件将通过Telegram发送给用户。

## 使用方法

**通过脚本运行：**

```bash
./scripts/youtube-tts-translate.sh <YouTube视频URL> [输出文件基础名称]
```

**示例：**

```bash
./scripts/youtube-tts-translate.sh "https://www.youtube.com/watch?v=YUznWuxA-jE" "my_video"
```

这将会：
1. 下载指定YouTube视频的英文字幕。
2. 清理字幕文件，提取纯文本内容。
3. 将纯英文文本翻译成中文。
4. 使用`edge-tts`将中文文本转换成语音文件（默认为`zh-CN-YunxiNeural`）。
5. 将生成的`.mp3`语音文件发送给用户。

## 依赖

- `yt-dlp`: 用于下载YouTube字幕。
- `awk`, `sed`: 用于处理文本。
- `edge-tts`: 用于将文本转换为语音。
- OpenClaw自身：用于执行翻译和发送文件。

## 注意事项

- 确保您的OpenClaw环境已正确安装并配置`yt-dlp`和`edge-tts`。
- 如果生成的音频文件过大（超过Telegram限制），此技能会尝试进行压缩。
- 视频必须包含英文字幕才能成功下载。
- 翻译步骤将由OpenClaw当前的模型完成。
