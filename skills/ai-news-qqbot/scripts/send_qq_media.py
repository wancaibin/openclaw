#!/usr/bin/env python3
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
    
    # 优先尝试作为语音类型上传
    print(f"[*] 正在尝试以语音类型 (VOICE) 上传到 QQ 目标: {chat_id} (类型: {chat_type})...")
    uploaded = False
    try:
        up = await uploader.upload(chat_type=chat_type, target_id=chat_id, file_path=file_path, file_type=MEDIA_TYPE_VOICE, file_name=os.path.basename(file_path))
        file_info = up.get("file_info") or (up.get("data", {}) or {}).get("file_info")
        if file_info:
            body = {"msg_type": MSG_TYPE_MEDIA, "media": {"file_info": file_info}, "msg_seq": 1}
            res = await adapter._post_message(adapter._messages_path(chat_type, chat_id), body)
            print("[+] 语音发送成功:", res)
            uploaded = True
    except Exception as e:
        print(f"[-] 语音发送失败: {e}，将尝试以文件形式发送...")

    if not uploaded:
        # 回退为文件形式发送
        try:
            up = await uploader.upload(chat_type=chat_type, target_id=chat_id, file_path=file_path, file_type=MEDIA_TYPE_FILE, file_name=display_name)
            file_info = up.get("file_info") or (up.get("data", {}) or {}).get("file_info")
            if file_info:
                body = {"msg_type": MSG_TYPE_MEDIA, "media": {"file_info": file_info}, "msg_seq": 2}
                res = await adapter._post_message(adapter._messages_path(chat_type, chat_id), body)
                print("[+] 文件形式发送成功:", res)
                uploaded = True
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
