#!/bin/bash
# youtube-tts-translate.sh - 下载YouTube视频字幕，翻译成中文，并用edge-tts生成中文语音，然后发送给用户。

YOUTUBE_URL="$1"
BASE_FILENAME="${2:-youtube_output}"

if [ -z "$YOUTUBE_URL" ]; then
    echo "用法: $0 <YouTube视频URL> [输出文件基础名称]"
    exit 1
fi

ENGLISH_VTT_FILE="${BASE_FILENAME}.en.vtt"
CLEAN_ENGLISH_TEXT_FILE="${BASE_FILENAME}.en.txt"
CHINESE_TEXT_FILE="${BASE_FILENAME}.zh.txt"
CHINESE_AUDIO_FILE="${BASE_FILENAME}.zh.mp3"
COMPRESSED_AUDIO_FILE="${BASE_FILENAME}.zh.small.mp3"

echo "步骤1: 下载YouTube视频字幕..."
yt-dlp --write-auto-subs --skip-download --sub-langs en --output "${BASE_FILENAME}.%(ext)s" "$YOUTUBE_URL"

if [ ! -f "$ENGLISH_VTT_FILE" ]; then
    echo "错误: 未能下载英文字幕文件: $ENGLISH_VTT_FILE"
    exit 1
fi

echo "步骤2: 清理字幕文件，提取纯文本..."
sed -E 's/<[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}><c>//g; s/<\/c>//g' "$ENGLISH_VTT_FILE" | \
awk '!/WEBVTT/ && !/Kind:/ && !/Language:/ && !/-->/ && NF {print}' | \
uniq > "$CLEAN_ENGLISH_TEXT_FILE"

if [ ! -s "$CLEAN_ENGLISH_TEXT_FILE" ]; then
    echo "错误: 清理后的英文文本文件为空或不存在: $CLEAN_ENGLISH_TEXT_FILE"
    exit 1
fi

echo "步骤3: 将英文文本翻译成中文..."
# This step requires the OpenClaw model to perform the translation
# The model will read CLEAN_ENGLISH_TEXT_FILE and output to CHINESE_TEXT_FILE
# For this script to work autonomously, the model would need to directly call itself for translation.
# As a workaround, the skill definition should guide the model to perform this step interactively or using an internal function.

# Placeholder for translation. In real execution, the model itself would handle this.
# For now, I'll simulate by creating an empty Chinese text file if translation fails
if [ ! -f "$CHINESE_TEXT_FILE" ]; then
    echo "由于模型无法在脚本内直接翻译，请手动将 ${CLEAN_ENGLISH_TEXT_FILE} 翻译为中文并保存到 ${CHINESE_TEXT_FILE}"
    # As the model, I will actually perform the translation and write to the file
    # This part will be handled by the agent's reasoning, not literally in the script.
    # The script will expect CHINESE_TEXT_FILE to be populated.
fi

# Let's read the English content and then produce the Chinese content for the script to continue.
ENGLISH_CONTENT=$(cat "$CLEAN_ENGLISH_TEXT_FILE")
# Assuming the model performs the translation here and writes to CHINESE_TEXT_FILE

# For actual skill execution, the model would perform the following:
# message "请将以下英文文本翻译成中文：${ENGLISH_CONTENT}"
# then capture the response and write to CHINESE_TEXT_FILE.
# For now, let's assume CHINESE_TEXT_FILE exists from the previous run.

# To make this script runnable *within* the agent, the agent itself needs to handle the translation step.
# For the purpose of this script, I'll put a placeholder that the user would replace,
# or more likely, the agent would intervene between step 2 and 4 to do the translation.

# Since I am the agent, I will directly perform the translation and save it.
# This part is *not* in the shell script, but in the agent's logic.
# After the script prepares CLEAN_ENGLISH_TEXT_FILE, the agent reads it, translates, and writes CHINESE_TEXT_FILE.

echo "步骤4: 使用edge-tts将中文文本转换为语音..."
if command -v edge-tts &> /dev/null; then
    edge-tts --voice zh-CN-YunxiNeural --file "$CHINESE_TEXT_FILE" --write-media "$CHINESE_AUDIO_FILE"
    if [ ! -f "$CHINESE_AUDIO_FILE" ]; then
        echo "错误: 未能生成中文语音文件: $CHINESE_AUDIO_FILE"
        exit 1
    fi
    echo "已生成中文语音文件: $CHINESE_AUDIO_FILE"
else
    echo "错误: edge-tts 未安装。请先安装 edge-tts。"
    exit 1
fi

echo "步骤5: 检查语音文件大小并发送..."
AUDIO_SIZE=$(du -m "$CHINESE_AUDIO_FILE" | awk '{print $1}')
MAX_TELEGRAM_SIZE_MB=16

if (( AUDIO_SIZE > MAX_TELEGRAM_SIZE_MB )); then
    echo "语音文件大小 ($AUDIO_SIZE MB) 超过Telegram限制 ($MAX_TELEGRAM_SIZE_MB MB)，尝试压缩..."
    # 使用ffmpeg进行压缩，降低比特率和采样率
    ffmpeg -i "$CHINESE_AUDIO_FILE" -ac 1 -ar 22050 -b:a 32k "$COMPRESSED_AUDIO_FILE" -y > /dev/null 2>&1
    
    if [ -f "$COMPRESSED_AUDIO_FILE" ]; then
        COMPRESSED_SIZE=$(du -m "$COMPRESSED_AUDIO_FILE" | awk '{print $1}')
        echo "压缩后文件大小: $COMPRESSED_SIZE MB"
        # The agent will send COMPRESSED_AUDIO_FILE
    else
        echo "错误: 压缩失败。将发送原始文件（可能失败）或不发送。"
        # The agent will send CHINESE_AUDIO_FILE
    fi
else
    echo "语音文件大小 ($AUDIO_SIZE MB) 在Telegram限制内，直接发送..."
    # The agent will send CHINESE_AUDIO_FILE
fi

# The final message sending will be handled by the agent, not the script.
# The script will output the path to the file to be sent.

# Echo the path of the file to be sent for the agent to pick up
if [ -f "$COMPRESSED_AUDIO_FILE" ] && (( COMPRESSED_SIZE <= MAX_TELEGRAM_SIZE_MB )); then
    echo "TO_SEND_FILE=$COMPRESSED_AUDIO_FILE"
else
    echo "TO_SEND_FILE=$CHINESE_AUDIO_FILE"
fi

echo "技能执行完成。"
