#!/usr/bin/env python3
"""
AI News fetcher, deep summarizer, deduplicator, TTS synthesizer, and QQ Bot dispatcher.
Optimized for OpenClaw Gateway cron execution with multi-source ingestion and diversity selection.
"""
import os
import re
import sys
import json
import html
import hashlib
import subprocess
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# Paths & environment
PYTHON_BIN = "/Users/wcb/.hermes/hermes-agent/venv/bin/python3"
EDGE_TTS_BIN = "/Users/wcb/.local/bin/edge-tts"
SEND_MEDIA_SCRIPT = "/Users/wcb/.openclaw/skills/ai-news-qqbot/scripts/send_qq_media.py"
DATA_DIR = Path("/Users/wcb/.openclaw/skills/ai-news-qqbot/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = DATA_DIR / "broadcast_history.json"

TMP_DIR = Path("/tmp/ai_news_cron")
TMP_DIR.mkdir(parents=True, exist_ok=True)

TEXT_FILE = TMP_DIR / "ai_news.txt"
AUDIO_FILE = TMP_DIR / "ai_news.mp3"
SUMMARY_FILE = TMP_DIR / "ai_summary.txt"

REQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
}

def load_history() -> set:
    """Load set of already broadcasted item keys/hashes."""
    if not HISTORY_FILE.exists():
        return set()
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return set(data)
        elif isinstance(data, dict):
            return set(data.get("seen_ids", []))
    except Exception as e:
        print(f"[!] 加载去重历史出错: {e}", file=sys.stderr)
    return set()

def save_history(seen_ids: set):
    """Save seen item keys/hashes to persistent storage (keep recent 2000)."""
    try:
        data_list = list(seen_ids)[-2000:]
        HISTORY_FILE.write_text(json.dumps(data_list, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[!] 保存去重历史出错: {e}", file=sys.stderr)

def get_item_key(title: str, link: str = "") -> str:
    """Generate a stable deduplication key for news item."""
    if link and link.strip():
        raw = link.strip().lower()
    else:
        raw = re.sub(r'[\W_]+', '', title.strip().lower())
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def clean_html(raw_html: str) -> str:
    """Strip HTML tags, unescape entities, and clean whitespaces."""
    if not raw_html:
        return ""
    cleanr = re.compile(r'<.*?>')
    text = re.sub(cleanr, ' ', raw_html)
    text = html.unescape(text)
    # 过滤常见无意义前缀
    text = re.sub(r'^(Abstract:?|Summary:?)\s*', '', text.strip(), flags=re.IGNORECASE)
    return " ".join(text.split())

def translate_to_zh(text: str) -> str:
    """Translate text to Chinese using Google Translate web API without premature truncation."""
    if not text or not text.strip():
        return ""
    # 若本身主要包含中文字符，则直接返回
    zh_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    if zh_chars > len(text) * 0.3:
        return text.strip()

    # 分块翻译，避免单次 URL 超长导致截断或请求失败
    remaining = text.strip()
    chunks = []
    chunk_limit = 1200
    while len(remaining) > chunk_limit:
        split_idx = remaining.rfind(' ', 0, chunk_limit)
        if split_idx == -1:
            split_idx = chunk_limit
        chunks.append(remaining[:split_idx])
        remaining = remaining[split_idx:].strip()
    if remaining:
        chunks.append(remaining)

    translated_parts = []
    for chunk in chunks:
        try:
            url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q=" + urllib.parse.quote(chunk)
            req = urllib.request.Request(url, headers=REQ_HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                chunk_zh = "".join([part[0] for part in data[0] if part and part[0]]).strip()
                translated_parts.append(chunk_zh)
        except Exception as e:
            print(f"[!] 翻译片段出错: {e}", file=sys.stderr)
            translated_parts.append(chunk)

    return " ".join(translated_parts).strip()

# ==================== 数据源抓取模块 ====================

def fetch_techcrunch_ai():
    """1. 商业前沿: TechCrunch AI 投融资与产品报道"""
    items = []
    try:
        url = "https://techcrunch.com/category/artificial-intelligence/feed/"
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="replace"))
            for entry in root.findall(".//item")[:15]:
                title = entry.find("title").text if entry.find("title") is not None else ""
                link = entry.find("link").text if entry.find("link") is not None else ""
                desc_el = entry.find("description")
                desc = clean_html(desc_el.text) if desc_el is not None and desc_el.text else ""
                if title:
                    items.append({
                        "category": "商业前沿",
                        "source": "TechCrunch",
                        "title": title.strip(),
                        "details": desc,
                        "link": link.strip(),
                        "key": get_item_key(title, link)
                    })
    except Exception as e:
        print(f"[!] 抓取 TechCrunch 失败: {e}", file=sys.stderr)
    return items

def fetch_verge_ai():
    """2. 科技前沿: The Verge AI 热点"""
    items = []
    try:
        url = "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="replace"))
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                title = entry.find("atom:title", ns).text if entry.find("atom:title", ns) is not None else ""
                link_el = entry.find("atom:link", ns)
                link = link_el.attrib.get("href", "") if link_el is not None else ""
                content_el = entry.find("atom:content", ns)
                if content_el is None:
                    content_el = entry.find("atom:summary", ns)
                desc = clean_html(content_el.text) if content_el is not None and content_el.text else ""
                if title:
                    items.append({
                        "category": "科技动态",
                        "source": "The Verge",
                        "title": title.strip(),
                        "details": desc,
                        "link": link.strip(),
                        "key": get_item_key(title, link)
                    })
    except Exception as e:
        print(f"[!] 抓取 The Verge 失败: {e}", file=sys.stderr)
    return items

def fetch_hn_ai():
    """3. 社区热点: Hacker News 首页高赞 AI/Agent 讨论"""
    items = []
    ai_keywords = [
        "ai", "llm", "gpt", "claude", "agent", "deepseek", "gemini",
        "neural", "model", "openai", "anthropic", "robot", "reasoning"
    ]
    try:
        url = "https://news.ycombinator.com/rss"
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="replace"))
            for entry in root.findall(".//item"):
                title = entry.find("title").text if entry.find("title") is not None else ""
                link = entry.find("link").text if entry.find("link") is not None else ""
                title_lower = title.lower()
                if any(re.search(rf"\b{re.escape(kw)}\b", title_lower) for kw in ai_keywords):
                    items.append({
                        "category": "社区热议",
                        "source": "Hacker News",
                        "title": title.strip(),
                        "details": "该议题目前在 Hacker News 技术社区引发广泛关注与热烈讨论。",
                        "link": link.strip(),
                        "key": get_item_key(title, link)
                    })
                if len(items) >= 6:
                    break
    except Exception as e:
        print(f"[!] 抓取 Hacker News 失败: {e}", file=sys.stderr)
    return items

def fetch_hf_papers():
    """4. 顶会精选: Hugging Face Daily Papers 社区高赞前沿论文"""
    items = []
    try:
        url = "https://huggingface.co/api/daily_papers"
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for entry in data[:15]:
                paper = entry.get("paper", {})
                title = paper.get("title", "")
                summary = paper.get("summary", "")
                pid = paper.get("id", "")
                link = f"https://huggingface.co/papers/{pid}" if pid else ""
                if title:
                    items.append({
                        "category": "顶会精选",
                        "source": "Hugging Face",
                        "title": title.strip(),
                        "details": clean_html(summary),
                        "link": link,
                        "key": get_item_key(title, link)
                    })
    except Exception as e:
        print(f"[!] 抓取 Hugging Face 论文失败: {e}", file=sys.stderr)
    return items

def fetch_arxiv_ai():
    """5. 学术科研: arXiv cs.AI 论文库 (扩大遍历至前80篇)"""
    items = []
    try:
        url = "https://rss.arxiv.org/rss/cs.AI"
        req = urllib.request.Request(url, headers={**REQ_HEADERS, "Accept-Encoding": "identity"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="replace"))
            # 遍历前 80 篇，避免原先死切片 [:20] 导致被去重吃满后永远无法读后续新论文
            for entry in root.findall(".//item")[:80]:
                title = entry.find("title").text if entry.find("title") is not None else ""
                link = entry.find("link").text if entry.find("link") is not None else ""
                raw_desc = entry.find("description").text if entry.find("description") is not None else ""
                desc = clean_html(raw_desc)
                if "Abstract:" in desc:
                    desc = desc.split("Abstract:", 1)[1].strip()
                if title:
                    clean_title = title.split("(")[0].strip()
                    items.append({
                        "category": "学术科研",
                        "source": "arXiv cs.AI",
                        "title": clean_title,
                        "details": desc,
                        "link": link.strip(),
                        "key": get_item_key(clean_title, link)
                    })
    except Exception as e:
        print(f"[!] 抓取 arXiv 失败: {e}", file=sys.stderr)
    return items

# ==================== 多样化挑选与排版 ====================

def select_diverse_news(fresh_news, max_count=3):
    """
    智能跨源均衡挑选：
    优先从不同类别（商业前沿、科技动态、社区热议、学术科研）各挑 1 条，
    确保每次播报内容丰富均衡，避免单一类别霸屏。
    """
    grouped = {}
    for item in fresh_news:
        cat = item["category"]
        grouped.setdefault(cat, []).append(item)

    selected = []
    # 优先级类别轮询
    priority_order = ["商业前沿", "科技动态", "社区热议", "顶会精选", "学术科研"]
    while len(selected) < max_count:
        picked_in_this_round = False
        for cat in priority_order:
            if cat in grouped and grouped[cat]:
                selected.append(grouped[cat].pop(0))
                picked_in_this_round = True
                if len(selected) >= max_count:
                    break
        # 如果所有已知类别都空了，检查其他剩余
        if not picked_in_this_round:
            for cat, items in list(grouped.items()):
                if items:
                    selected.append(items.pop(0))
                    if len(selected) >= max_count:
                        break
            break
    return selected

def build_broadcast_and_summary(news_items):
    """提炼中文播报稿与微信/QQ速览文本"""
    now_str = datetime.now().strftime("%H点%M分")

    broadcast_lines = [
        f"大家好，这里是人工智能最新动态播报，当前时间为{now_str}。",
        "接下来为您带来最新精选的AI行业前沿与技术进展："
    ]

    summary_lines = [
        f"📢 今日 AI 最新动态速览 ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
        "（语音播报已同步发送至上方，以下为核心要点解读）：\n"
    ]

    for idx, item in enumerate(news_items, 1):
        cat = item["category"]
        src = item["source"]
        title_en = item["title"]
        details_en = item["details"]

        # 翻译并提炼中文标题与细节总结
        title_zh = translate_to_zh(title_en)
        details_zh = translate_to_zh(details_en) if details_en else "暂无更多详细背景。"

        # 语音播报文案
        speech_item = f"第{idx}条，{src}关于【{cat}】关注到：{title_zh}。核心要点指出：{details_zh}"
        broadcast_lines.append(speech_item)

        # 文字版速览文案
        summary_lines.append(f"{idx}. 【{cat} · {src}】{title_zh}")
        summary_lines.append(f"   💡 核心要点：{details_zh}")
        if item.get("link"):
            summary_lines.append(f"   🔗 来源链接：{item['link']}")
        summary_lines.append("")

    broadcast_lines.append("以上就是本次AI动态播报的全部内容，感谢您的收听！")

    broadcast_text = "\n".join(broadcast_lines)
    summary_text = "\n".join(summary_lines)
    return broadcast_text, summary_text

# ==================== 发送与执行流程 ====================

def synthesize_audio(text: str, output_path: Path):
    print(f"[*] 正在合成 TTS 语音到: {output_path}")
    TEXT_FILE.write_text(text, encoding="utf-8")
    cmd = [
        EDGE_TTS_BIN,
        "--voice", "zh-CN-XiaoxiaoNeural",
        "-f", str(TEXT_FILE),
        "--write-media", str(output_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"edge-tts 执行失败: {res.stderr}")
    print("[+] TTS 语音合成完成")

def send_qq_audio(audio_path: Path, title: str):
    print(f"[*] 正在推送音频至 QQ 机器人: {audio_path}")
    cmd = [PYTHON_BIN, SEND_MEDIA_SCRIPT, str(audio_path), title]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.returncode != 0:
        print(f"[-] 推送音频失败: {res.stderr}", file=sys.stderr)

def send_qq_text(summary_text: str):
    print("[*] 正在发送 QQ 文字版要点速览...")
    cmd = ["hermes", "send", "--to", "qqbot", summary_text]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.returncode != 0:
        print(f"[-] 发送文字版失败: {res.stderr}", file=sys.stderr)

def main():
    start_time = datetime.now()
    print(f"=== [OpenClaw AI News Cron Job Started at {start_time.isoformat()}] ===")
    
    # 1. 加载历史去重库
    history_keys = load_history()
    print(f"[*] 已加载历史去重记录库，共 {len(history_keys)} 条记录")

    # 2. 多源并发/顺序抓取
    all_fetched = []
    sources = [
        ("TechCrunch AI", fetch_techcrunch_ai),
        ("The Verge AI", fetch_verge_ai),
        ("Hacker News AI", fetch_hn_ai),
        ("Hugging Face Daily Papers", fetch_hf_papers),
        ("arXiv cs.AI", fetch_arxiv_ai),
    ]

    for name, fetcher in sources:
        try:
            items = fetcher()
            print(f"[+] [{name}] 获取成功: {len(items)} 条资讯")
            all_fetched.extend(items)
        except Exception as e:
            print(f"[-] [{name}] 抓取出现异常: {e}", file=sys.stderr)

    # 3. 过滤历史已播报内容
    fresh_news = [item for item in all_fetched if item["key"] not in history_keys]
    print(f"[*] 全网共获取资讯 {len(all_fetched)} 条，过滤历史去重后剩余全新资讯 {len(fresh_news)} 条")

    if not fresh_news:
        print("[i] 没有检测到未播报的新资讯，跳过本次推送，静待下次检测周期。")
        print("=== [OpenClaw AI News Cron Job Finished (No New Content)] ===")
        return

    # 4. 智能跨源挑选 2~3 条
    selected_news = select_diverse_news(fresh_news, max_count=3)
    print(f"[*] 已选定 {len(selected_news)} 条多元资讯进行提炼与语音播报:")
    for it in selected_news:
        print(f"    - [{it['category']} · {it['source']}] {it['title']}")

    # 5. 生成播报稿件与文字速览
    broadcast_text, summary_text = build_broadcast_and_summary(selected_news)
    SUMMARY_FILE.write_text(summary_text, encoding="utf-8")
    print(f"[+] 播报文案准备完成，语音稿共 {len(broadcast_text)} 字")

    # 6. TTS 语音合成
    synthesize_audio(broadcast_text, AUDIO_FILE)

    # 7. 推送音频至 QQ 机器人
    send_qq_audio(AUDIO_FILE, f"AI新动态播报_{datetime.now().strftime('%H%M')}.mp3")

    # 8. 推送图文/文字要点速览至 QQ 机器人
    send_qq_text(summary_text)

    # 9. 记录已播报资讯至去重库
    for item in selected_news:
        history_keys.add(item["key"])
    save_history(history_keys)
    print(f"[+] 已将本次播报的 {len(selected_news)} 条资讯记录至去重库（当前总计 {len(history_keys)} 条）")

    duration = (datetime.now() - start_time).total_seconds()
    print(f"=== [OpenClaw AI News Cron Job Completed Successfully in {duration:.1f}s] ===")

if __name__ == "__main__":
    main()
