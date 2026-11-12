#!/usr/bin/env python3
"""
QQ media dispatcher:
1. Supports splitting audio into <= 55s parts so QQ mobile/desktop client won't truncate voice messages at 60s.
2. Supports fallback to File upload if voice fails or if duration is long.
3. Automatically names parts (e.g., 播报语音 (第1/2段)).
"""
import asyncio
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/Users/wcb/.hermes/.env")

from gateway.platforms.qqbot.adapter import QQAdapter, MSG_TYPE_MEDIA, MEDIA_TYPE_VOICE, MEDIA_TYPE_FILE
from gateway.platforms.qqbot.chunked_upload import ChunkedUploader
from gateway.platforms.base import PlatformConfig
import httpx

MAX_VOICE_SECONDS = 55.0  # QQ 客户端单条语音硬限制通常为 60 秒，超过会被截断无法完整播放

def get_audio_duration(file_path: str) -> float:
    """获取音频文件精确时长（秒）"""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        print(f"[!] 获取音频时长失败: {e}", file=sys.stderr)
        return 0.0

def split_audio(file_path: str, max_duration: float = MAX_VOICE_SECONDS) -> list[str]:
    """若音频时长超过限制，切分为多段（每段 <= max_duration 秒）"""
    dur = get_audio_duration(file_path)
    if dur <= 0 or dur <= max_duration:
        return [file_path]

    parts = []
    start = 0.0
    idx = 1
    stem = Path(file_path).stem
    parent = Path(file_path).parent

    while start < dur:
        out_part = str(parent / f"{stem}_part{idx}.mp3")
        # 重新编码以确保切割点精准、MP3头信息完整
        cmd = [
            "ffmpeg", "-y", "-ss", str(start), "-t", str(max_duration),
            "-i", file_path, "-acodec", "libmp3lame", "-ar", "24000", "-b:a", "48k", out_part
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        parts.append(out_part)
        start += max_duration
        idx += 1

    print(f"[*] 音频总长 {dur:.1f} 秒超过单条语音上限（{max_duration}秒），已切分为 {len(parts)} 个语音片段以保证播放完整。")
    return parts

async def send_media(file_path: str, display_name: str = "AI资讯简报.mp3"):
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    cfg = PlatformConfig(
        enabled=True,
        extra={
            "app_id": os.getenv("QQ_APP_ID"),
            "client_secret": os.getenv("QQ_CLIENT_SECRET"),
        }
    )
    adapter = QQAdapter(cfg)
    chat_id = os.getenv("QQBOT_HOME_CHANNEL")
    if not chat_id:
        print("Error: QQBOT_HOME_CHANNEL not configured in /Users/wcb/.hermes/.env", file=sys.stderr)
        sys.exit(1)

    chat_type = adapter._guess_chat_type(chat_id)
    adapter._http_client = httpx.AsyncClient(timeout=60.0)
    uploader = ChunkedUploader(api_request=adapter._api_request, http_put=adapter._http_client.put, log_tag=adapter._log_tag)

    # 1. 检查时长并进行切片以解决 QQ 客户端 60 秒截断问题
    parts = split_audio(file_path, max_duration=MAX_VOICE_SECONDS)
    total_parts = len(parts)

    all_voice_success = True
    msg_seq = 1

    for idx, part_path in enumerate(parts, 1):
        part_name = f"{display_name}_第{idx}_{total_parts}段.mp3" if total_parts > 1 else display_name
        print(f"[*] 正在推送语音 {idx}/{total_parts} ({part_name})...")
        try:
            up = await uploader.upload(
                chat_type=chat_type,
                target_id=chat_id,
                file_path=part_path,
                file_type=MEDIA_TYPE_VOICE,
                file_name=part_name
            )
            file_info = up.get("file_info") or (up.get("data", {}) or {}).get("file_info")
            if file_info:
                body = {"msg_type": MSG_TYPE_MEDIA, "media": {"file_info": file_info}, "msg_seq": msg_seq}
                res = await adapter._post_message(adapter._messages_path(chat_type, chat_id), body)
                print(f"[+] 语音分段 {idx}/{total_parts} 发送成功:", res.message_id if hasattr(res, "message_id") else res)
                msg_seq += 1
            else:
                all_voice_success = False
                break
        except Exception as e:
            print(f"[-] 语音分段 {idx} 发送失败: {e}", file=sys.stderr)
            all_voice_success = False
            break

        if idx < total_parts:
            await asyncio.sleep(0.8)

    # 2. 如果语音发送失败，降级为直接发送完整 MP3 文件
    if not all_voice_success:
        print(f"[*] 尝试以完整文件形式发送: {file_path}")
        try:
            up = await uploader.upload(
                chat_type=chat_type,
                target_id=chat_id,
                file_path=file_path,
                file_type=MEDIA_TYPE_FILE,
                file_name=display_name
            )
            file_info = up.get("file_info") or (up.get("data", {}) or {}).get("file_info")
            if file_info:
                body = {"msg_type": MSG_TYPE_MEDIA, "media": {"file_info": file_info}, "msg_seq": msg_seq + 10}
                res = await adapter._post_message(adapter._messages_path(chat_type, chat_id), body)
                print("[+] 文件形式发送成功:", res.message_id if hasattr(res, "message_id") else res)
        except Exception as e2:
            print(f"[!] 文件形式发送也失败: {e2}", file=sys.stderr)
            await adapter._http_client.aclose()
            sys.exit(1)

    await adapter._http_client.aclose()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: send_qq_media.py <audio_file_path> [display_name]")
        sys.exit(1)
    target_file = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "AI最新动态简报.mp3"
    asyncio.run(send_media(target_file, name))
