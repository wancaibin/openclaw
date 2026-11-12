#!/usr/bin/env python3
"""
AI News fetcher, full-text reader, deduplicator, TTS synthesizer, and QQ Bot dispatcher.
Reads full articles/papers/discussions without summary truncation.
Integrated Sources:
  - TechCrunch AI (Business/Funding/Industry)
  - The Verge AI (Consumer Tech & Trends)
  - Hacker News AI (Top Community Tech Debates via Algolia & RSS)
  - Hugging Face Daily Papers (Top Community Papers)
  - arXiv cs.AI (Academic Research Abstracts)
  - X / Twitter AI (Frontier labs & AI figures trending discussions)
  - Reddit AI (r/LocalLLaMA, r/singularity, r/MachineLearning)
  - OpenAI Newsroom (Official Models & Releases)
  - GitHub Trending (Trending Open-Source AI/LLM Projects)
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
    text = re.sub(r'^(Abstract:?|Summary:?)\s*', '', text.strip(), flags=re.IGNORECASE)
    return " ".join(text.split())

def fetch_full_web_article(url: str) -> str:
    """Fetch complete web article content from URL without truncation."""
    if not url or not url.startswith("http"):
        return ""
    try:
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "application/xhtml" not in content_type:
                return ""
            raw = resp.read().decode("utf-8", errors="replace")

        # Strip scripts, styles, metadata
        clean = re.sub(r'<(script|style|nav|header|footer|aside|form|svg|noscript)[^>]*>.*?</\1>', ' ', raw, flags=re.DOTALL|re.IGNORECASE)
        
        # Look for article or main content tags
        article_match = re.search(r'<(article|main)[^>]*>(.*?)</\1>', clean, flags=re.DOTALL|re.IGNORECASE)
        target_html = article_match.group(2) if article_match else clean

        # Extract paragraphs
        p_matches = re.findall(r'<p[^>]*>(.*?)</p>', target_html, flags=re.DOTALL|re.IGNORECASE)
        paras = []
        skip_phrases = [
            "cookie", "subscribe", "sign up", "privacy policy", "terms of service", 
            "terms of use", "all rights reserved", "advertisement", "newsletter",
            "follow us", "share this", "photo by", "image credit"
        ]
        for p in p_matches:
            t = clean_html(p)
            if len(t) > 35 and not any(skip in t.lower() for skip in skip_phrases):
                paras.append(t)
        
        if paras:
            return "\n\n".join(paras)
        return ""
    except Exception as e:
        print(f"[!] 抓取原文全文失败 ({url}): {e}", file=sys.stderr)
        return ""

def translate_via_youdao(text: str) -> str:
    """Use Youdao free translation API."""
    if not text or not text.strip():
        return ""
    try:
        url = "https://aidemo.youdao.com/trans"
        data = urllib.parse.urlencode({"q": text, "from": "Auto", "to": "zh-CHS"}).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translations = data.get("translation", [])
            if translations and translations[0]:
                return "\n".join(translations).strip()
    except Exception as e:
        pass
    return ""

def translate_via_mymemory(text: str) -> str:
    """Use MyMemory free translation API."""
    if not text or not text.strip():
        return ""
    try:
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text[:500])}&langpair=en|zh-CN"
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated and not translated.startswith("MYMEMORY WARNING"):
                return translated.strip()
    except Exception as e:
        pass
    return ""

def translate_to_zh(text: str) -> str:
    """Translate text to Chinese using fast free online web services (Youdao / MyMemory / Google fallback)."""
    if not text or not text.strip():
        return ""
    # 若本身主要包含中文字符，则直接返回
    zh_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
    if zh_chars > len(text) * 0.3:
        return text.strip()

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks = []
    chunk_limit = 1000
    for p in paragraphs:
        remaining = p
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
        # 1. 优先使用快速稳定的有道在线翻译接口（毫秒级响应）
        translated_chunk = translate_via_youdao(chunk)

        # 2. 备选 MyMemory 免费翻译服务
        if not translated_chunk:
            translated_chunk = translate_via_mymemory(chunk)

        # 3. 备选 Google Web 翻译接口
        if not translated_chunk:
            try:
                url = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=zh-CN&q=" + urllib.parse.quote(chunk)
                req = urllib.request.Request(url, headers=REQ_HEADERS)
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    if isinstance(data, list) and data and isinstance(data[0], list) and data[0]:
                        translated_chunk = data[0][0]
                    elif isinstance(data, list) and data and isinstance(data[0], str):
                        translated_chunk = data[0]
            except Exception:
                pass

        if not translated_chunk:
            try:
                url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q=" + urllib.parse.quote(chunk)
                req = urllib.request.Request(url, headers=REQ_HEADERS)
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    translated_chunk = "".join([part[0] for part in data[0] if part and part[0]]).strip()
            except Exception:
                pass

        translated_parts.append(translated_chunk if translated_chunk else chunk)

    return "\n".join(translated_parts).strip()

# ==================== 数据源抓取模块 ====================

def fetch_techcrunch_ai():
    """1. 商业前沿: TechCrunch AI"""
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
                if title and link:
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
    """2. 科技动态: The Verge AI"""
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
                if title and link:
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
    """3. 社区热议: Hacker News 最新 AI 讨论 (通过 Algolia API 及 RSS)"""
    items = []
    try:
        url = "https://hn.algolia.com/api/v1/search_by_date?tags=story&query=AI&hitsPerPage=10"
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for hit in data.get("hits", []):
                title = hit.get("title", "")
                link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                story_text = clean_html(hit.get("story_text", ""))
                points = hit.get("points", 0)
                comments = hit.get("num_comments", 0)
                desc = story_text if story_text else f"Hacker News 热议议题，当前获得 {points} 点赞及 {comments} 条深度技术讨论。"
                if title:
                    items.append({
                        "category": "社区热议",
                        "source": "Hacker News",
                        "title": title.strip(),
                        "details": desc,
                        "link": link.strip(),
                        "comments_link": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        "key": get_item_key(title, link)
                    })
    except Exception as e:
        print(f"[!] 抓取 Hacker News 失败: {e}", file=sys.stderr)
    return items

def fetch_hf_papers():
    """4. 顶会精选: Hugging Face Daily Papers 社区高赞论文"""
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
    """5. 学术科研: arXiv cs.AI 论文库"""
    items = []
    try:
        url = "https://rss.arxiv.org/rss/cs.AI"
        req = urllib.request.Request(url, headers={**REQ_HEADERS, "Accept-Encoding": "identity"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="replace"))
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

def fetch_x_ai():
    """6. 社交动态: X (Twitter) 前沿 AI 实验室与核心关注点"""
    items = []
    try:
        url = "https://news.google.com/rss/search?q=site:x.com+AI+OR+LLM+OR+OpenAI+OR+Anthropic+OR+DeepSeek+when:1d&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="replace"))
            for entry in root.findall(".//item")[:15]:
                title = entry.find("title").text if entry.find("title") is not None else ""
                link = entry.find("link").text if entry.find("link") is not None else ""
                desc = clean_html(entry.find("description").text) if entry.find("description") is not None else ""
                clean_t = re.sub(r'\s*-\s*X$', '', title).strip()
                if clean_t:
                    items.append({
                        "category": "社交动态",
                        "source": "X (Twitter)",
                        "title": clean_t,
                        "details": desc if len(desc) > len(clean_t) else f"来自 X 平台关于前沿 AI 模型与行业最新动态的讨论：{clean_t}",
                        "link": link.strip(),
                        "key": get_item_key(clean_t, link)
                    })
    except Exception as e:
        print(f"[!] 抓取 X (Twitter) 动态失败: {e}", file=sys.stderr)
    return items

def fetch_reddit_ai():
    """7. 社区热点: Reddit (r/LocalLLaMA, r/singularity, r/MachineLearning)"""
    items = []
    try:
        url = "https://news.google.com/rss/search?q=site:reddit.com/r/LocalLLaMA+OR+site:reddit.com/r/singularity+OR+site:reddit.com/r/MachineLearning+when:1d&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="replace"))
            for entry in root.findall(".//item")[:15]:
                title = entry.find("title").text if entry.find("title") is not None else ""
                link = entry.find("link").text if entry.find("link") is not None else ""
                desc = clean_html(entry.find("description").text) if entry.find("description") is not None else ""
                clean_t = re.sub(r'\s*-\s*Reddit$', '', title).strip()
                if clean_t:
                    items.append({
                        "category": "社区热点",
                        "source": "Reddit",
                        "title": clean_t,
                        "details": desc if len(desc) > len(clean_t) else f"Reddit AI 核心社区热门主题讨论：{clean_t}",
                        "link": link.strip(),
                        "key": get_item_key(clean_t, link)
                    })
    except Exception as e:
        print(f"[!] 抓取 Reddit 失败: {e}", file=sys.stderr)
    return items

def fetch_openai_news():
    """8. 官方动态: OpenAI Newsroom 官方公告与模型发布"""
    items = []
    try:
        url = "https://openai.com/news/rss.xml"
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            root = ET.fromstring(resp.read().decode("utf-8", errors="replace"))
            for entry in root.findall(".//item")[:10]:
                title = entry.find("title").text if entry.find("title") is not None else ""
                link = entry.find("link").text if entry.find("link") is not None else ""
                desc = clean_html(entry.find("description").text) if entry.find("description") is not None else ""
                if title:
                    items.append({
                        "category": "官方发布",
                        "source": "OpenAI",
                        "title": title.strip(),
                        "details": desc if desc else f"OpenAI 官方发布最新动态：{title.strip()}",
                        "link": link.strip(),
                        "key": get_item_key(title, link)
                    })
    except Exception as e:
        print(f"[!] 抓取 OpenAI 动态失败: {e}", file=sys.stderr)
    return items

def fetch_github_trending_ai():
    """9. 开源前沿: GitHub Trending 开源热门 AI/LLM 项目"""
    items = []
    try:
        url = "https://github.com/trending?since=daily"
        req = urllib.request.Request(url, headers=REQ_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html_text = resp.read().decode("utf-8", errors="replace")
            articles = re.findall(r'<article class="Box-row">(.*?)</article>', html_text, flags=re.DOTALL)
            ai_kw = ["ai", "llm", "agent", "model", "gpt", "rag", "deepseek", "chat", "voice", "reasoning", "diffusion"]
            for art in articles:
                repo_m = re.search(r'href="/([a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+)"', art)
                if not repo_m:
                    continue
                repo_name = repo_m.group(1)
                desc_m = re.search(r'<p class="col-9[^\"]*">(.*?)</p>', art, flags=re.DOTALL)
                desc = clean_html(desc_m.group(1)) if desc_m else ""
                check_str = f"{repo_name} {desc}".lower()
                if any(kw in check_str for kw in ai_kw):
                    title = f"热门开源项目: {repo_name}"
                    items.append({
                        "category": "开源前沿",
                        "source": "GitHub Trending",
                        "title": title,
                        "details": desc if desc else f"GitHub 当日热门开源 AI 项目：{repo_name}",
                        "link": f"https://github.com/{repo_name}",
                        "key": get_item_key(title, f"https://github.com/{repo_name}")
                    })
    except Exception as e:
        print(f"[!] 抓取 GitHub Trending 失败: {e}", file=sys.stderr)
    return items

# ==================== 多样化挑选与排版 ====================

def select_diverse_news(fresh_news, max_count=2):
    """
    智能跨源均衡挑选：
    优先从不同源与不同类别各挑选 1 条，
    确保每次播报内容丰富均衡，避免单一类别垄断。
    """
    grouped = {}
    for item in fresh_news:
        src = item["source"]
        grouped.setdefault(src, []).append(item)

    selected = []
    # 轮流从各个不同的 source 挑选
    sources_pool = list(grouped.keys())
    while len(selected) < max_count and sources_pool:
        for s in list(sources_pool):
            if grouped[s]:
                selected.append(grouped[s].pop(0))
                if len(selected) >= max_count:
                    break
            else:
                sources_pool.remove(s)
    return selected

def populate_full_content(item: dict) -> str:
    """获取条目的完整原文内容（优先获取网页正文，降级使用完整摘要或讨论）"""
    link = item.get("link", "")
    src = item.get("source", "")
    
    # 商业前沿、科技动态、OpenAI 官方博客：抓取文章网页完整正文
    if src in ["TechCrunch", "The Verge", "OpenAI"] and link:
        print(f"[*] 正在抓取 [{src}] 网页完整正文: {link}")
        full_text = fetch_full_web_article(link)
        if full_text and len(full_text) > 100:
            return full_text

    # Hacker News: 优先抓取外链原文，若不可读则回退
    if src == "Hacker News":
        if link and not link.startswith("https://news.ycombinator.com"):
            print(f"[*] 正在抓取 [HN 外链] 网页完整正文: {link}")
            full_text = fetch_full_web_article(link)
            if full_text and len(full_text) > 100:
                return full_text
        c_link = item.get("comments_link", "")
        if c_link:
            full_text = fetch_full_web_article(c_link)
            if full_text and len(full_text) > 100:
                return full_text

    # GitHub Trending: 尝试抓取仓库 README 正文
    if src == "GitHub Trending" and link:
        readme_url = link.rstrip("/") + "/blob/main/README.md"
        full_text = fetch_full_web_article(readme_url)
        if full_text and len(full_text) > 100:
            return full_text

    # 顶会精选 (Hugging Face) 与 学术科研 (arXiv): details 本身已是完整官方 Abstract 全文
    # 社交动态 (X) 与 社区热点 (Reddit): details 为完整核心主题描述
    return item.get("details", "")

def build_broadcast_and_summary(news_items):
    """直接读取完整文章与资讯全文，生成完整播报稿与微信/QQ速览文本（不再进行摘要截取）"""
    now_str = datetime.now().strftime("%H点%M分")

    broadcast_lines = [
        f"大家好，这里是人工智能最新动态播报，当前时间为{now_str}。",
        "接下来为您带来最新精选AI前沿文章与技术成果的完整内容解读："
    ]

    summary_lines = [
        f"📢 今日 AI 最新动态完整速递 ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
        "（语音播报已同步发送至上方，以下为完整全文内容呈现）：\n"
    ]

    for idx, item in enumerate(news_items, 1):
        cat = item["category"]
        src = item["source"]
        title_en = item["title"]

        # 1. 抓取完整全文（不再使用短摘要截取）
        full_content_en = populate_full_content(item)
        if not full_content_en:
            full_content_en = item.get("details", "暂无更多详细背景。")

        # 2. 翻译完整标题与完整正文内容
        title_zh = translate_to_zh(title_en)
        content_zh = translate_to_zh(full_content_en)

        # 3. 语音播报文案（朗读完整文章/报告内容）
        speech_item = f"第{idx}条，{src}关于【{cat}】发表文章：{title_zh}。完整内容如下：{content_zh}"
        broadcast_lines.append(speech_item)

        # 4. 文字版速览文案（展示完整正文与段落）
        summary_lines.append(f"{idx}. 【{cat} · {src}】{title_zh}")
        summary_lines.append(f"   📄 完整内容：\n{content_zh}")
        if item.get("link"):
            summary_lines.append(f"   🔗 来源链接：{item['link']}")
        summary_lines.append("")

    broadcast_lines.append("以上就是本次AI动态播报的全部完整资讯，感谢您的收听！")

    broadcast_text = "\n\n".join(broadcast_lines)
    summary_text = "\n".join(summary_lines)
    return broadcast_text, summary_text

# ==================== 发送与执行流程 ====================

def synthesize_audio(text: str, output_path: Path):
    print(f"[*] 正在合成 TTS 语音到: {output_path} (文本总字数: {len(text)})")
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
    print("[*] 正在发送 QQ 文字版完整资讯...")
    max_chunk = 3000
    if len(summary_text) <= max_chunk:
        cmd = ["hermes", "send", "--to", "qqbot", summary_text]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.stdout:
            print(res.stdout.strip())
        if res.returncode != 0:
            print(f"[-] 发送文字版失败: {res.stderr}", file=sys.stderr)
    else:
        remaining = summary_text
        part_idx = 1
        while remaining:
            chunk = remaining[:max_chunk]
            remaining = remaining[max_chunk:]
            header = f"[第{part_idx}部分] " if part_idx > 1 else ""
            cmd = ["hermes", "send", "--to", "qqbot", header + chunk]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.stdout:
                print(res.stdout.strip())
            part_idx += 1

def main():
    start_time = datetime.now()
    print(f"=== [OpenClaw AI News Cron Job Started at {start_time.isoformat()}] ===")
    
    # 1. 加载历史去重库
    history_keys = load_history()
    print(f"[*] 已加载历史去重记录库，共 {len(history_keys)} 条记录")

    # 2. 多源抓取
    all_fetched = []
    sources = [
        ("TechCrunch AI", fetch_techcrunch_ai),
        ("The Verge AI", fetch_verge_ai),
        ("Hacker News AI", fetch_hn_ai),
        ("Hugging Face Daily Papers", fetch_hf_papers),
        ("arXiv cs.AI", fetch_arxiv_ai),
        ("X (Twitter) AI", fetch_x_ai),
        ("Reddit AI", fetch_reddit_ai),
        ("OpenAI Official News", fetch_openai_news),
        ("GitHub Trending AI", fetch_github_trending_ai),
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

    # 4. 智能挑选多元资讯进行完整播报
    selected_news = select_diverse_news(fresh_news, max_count=2)
    print(f"[*] 已选定 {len(selected_news)} 条多元资讯进行完整全文读取与语音播报:")
    for it in selected_news:
        print(f"    - [{it['category']} · {it['source']}] {it['title']}")

    # 5. 生成完整全文播报稿件与文字速览
    broadcast_text, summary_text = build_broadcast_and_summary(selected_news)
    SUMMARY_FILE.write_text(summary_text, encoding="utf-8")
    print(f"[+] 播报文案准备完成，完整语音稿共 {len(broadcast_text)} 字")

    # 6. TTS 语音合成
    synthesize_audio(broadcast_text, AUDIO_FILE)

    # 7. 推送音频至 QQ 机器人
    send_qq_audio(AUDIO_FILE, f"AI完整动态播报_{datetime.now().strftime('%H%M')}.mp3")

    # 8. 推送完整文字内容至 QQ 机器人
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
