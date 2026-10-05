#!/Users/wcb/.local/pipx/venvs/edge-tts/bin/python
import sys
import asyncio
import edge_tts

async def synthesize(text_path, out_path, voice="zh-CN-XiaoxiaoNeural"):
    with open(text_path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    
    if not text:
        print("Empty text", file=sys.stderr)
        sys.exit(1)

    comm = edge_tts.Communicate(text, voice)
    chunks = 0
    with open(out_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
                chunks += 1
    print(f"Generated {out_path} ({chunks} chunks)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: text_to_speech.py <text_file> <output_mp3> [voice]")
        sys.exit(1)
    voice = sys.argv[3] if len(sys.argv) > 3 else "zh-CN-XiaoxiaoNeural"
    asyncio.run(synthesize(sys.argv[1], sys.argv[2], voice))
