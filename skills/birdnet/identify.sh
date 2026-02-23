#!/bin/bash
# BirdNET 鸟类识别脚本

API_URL="https://birdnet.cornell.edu/api/v1/identify"
API_KEY="${BIRDNET_API_KEY:-}"

usage() {
    echo "Usage: $0 <audio_file>"
    echo ""
    echo "识别鸟类鸣叫声"
    echo ""
    echo "参数:"
    echo "  audio_file    WAV/MP3 音频文件路径"
    echo ""
    echo "环境变量:"
    echo "  BIRDNET_API_KEY   BirdNET API 密钥（可选）"
    echo ""
    exit 1
}

if [ -z "$1" ]; then
    usage
fi

AUDIO_FILE="$1"

if [ ! -f "$AUDIO_FILE" ]; then
    echo "错误：文件不存在：$AUDIO_FILE"
    exit 1
fi

# 如果有 API 密钥，使用 API
if [ -n "$API_KEY" ]; then
    response=$(curl -s -X POST "$API_URL" \
        -H "Authorization: Bearer $API_KEY" \
        -F "audio=@$AUDIO_FILE" \
        -F "format=json")
    echo "$response" | jq .
else
    # 本地模式（需要安装 birdnet-analyzer）
    if command -v birdnet-analyzer &> /dev/null; then
        birdnet-analyzer predict --i "$AUDIO_FILE" --o predictions.csv
        cat predictions.csv
    else
        echo "错误：未配置 API 密钥且未安装 birdnet-analyzer"
        echo ""
        echo "安装方式:"
        echo "  1. 获取 API 密钥：https://birdnet.cornell.edu/api/"
        echo "  2. 或安装本地工具：brew install birdnet-analyzer"
        exit 1
    fi
fi
