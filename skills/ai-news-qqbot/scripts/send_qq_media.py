#!/usr/bin/env python3
"""
QQ media dispatcher:
Sends the entire audio file directly in one piece (no chunking/splitting).
Tries voice message first, falls back to file message if voice is rejected or fails.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv("/Users/wcb/.hermes/.env")

from gateway.platforms.qqbot.adapter import QQAdapter, MSG_TYPE_MEDIA, MEDIA_TYPE_VOICE, MEDIA_TYPE_FILE
from gateway.platforms.qqbot.chunked_upload import ChunkedUploader
from gateway.platforms.base import PlatformConfig
import httpx

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

    print(f"[*] 准备一次性推送完整音频: {file_path} ({display_name})")
    success = False

    # 1. 尝试以完整语音 (MEDIA_TYPE_VOICE) 发送
    try:
        print("[*] 正在尝试以语音格式发送完整音频...")
        up = await uploader.upload(
            chat_type=chat_type,
            target_id=chat_id,
            file_path=file_path,
            file_type=MEDIA_TYPE_VOICE,
            file_name=display_name
        )
        file_info = up.get("file_info") or (up.get("data", {}) or {}).get("file_info")
        if file_info:
            body = {"msg_type": MSG_TYPE_MEDIA, "media": {"file_info": file_info}, "msg_seq": 1}
            res = await adapter._post_message(adapter._messages_path(chat_type, chat_id), body)
            print("[+] 语音发送成功:", res.message_id if hasattr(res, "message_id") else res)
            success = True
        else:
            print("[-] 上传语音未返回有效 file_info，准备尝试文件格式...", file=sys.stderr)
    except Exception as e:
        print(f"[-] 语音格式发送未成功 ({e})，准备尝试文件格式...")

    # 2. 若语音格式未成功，直接以完整文件格式 (MEDIA_TYPE_FILE) 发送
    if not success:
        print("[*] 正在以完整文件格式发送音频...")
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
                body = {"msg_type": MSG_TYPE_MEDIA, "media": {"file_info": file_info}, "msg_seq": 1}
                res = await adapter._post_message(adapter._messages_path(chat_type, chat_id), body)
                print("[+] 文件格式发送成功:", res.message_id if hasattr(res, "message_id") else res)
                success = True
            else:
                print("[-] 文件上传未返回有效 file_info", file=sys.stderr)
        except Exception as e2:
            print(f"[!] 文件格式发送失败: {e2}", file=sys.stderr)

    await adapter._http_client.aclose()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: send_qq_media.py <audio_file_path> [display_name]")
        sys.exit(1)
    target_file = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else "AI最新动态简报.mp3"
    asyncio.run(send_media(target_file, name))
