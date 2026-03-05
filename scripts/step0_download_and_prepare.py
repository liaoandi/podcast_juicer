#!/usr/bin/env python3
"""
从播客 URL 下载音频并提取参与者信息（一站式准备脚本）

功能：
1. 从播客 URL 下载音频文件
2. 同时提取参与者信息（主持人、嘉宾、节目信息）
3. 保存为标准格式，供后续流程使用

使用方法：
    python step0_download_and_prepare.py <podcast_url> [output_name]

示例：
    python step0_download_and_prepare.py https://sv101.fireside.fm/233 sv101_ep233
"""

import json
import sys
import os
import subprocess
from google.genai import types
from gemini_utils import get_gemini_client, DEFAULT_MODEL, clean_json

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Gemini 配置
GEMINI_MODEL = DEFAULT_MODEL
LOCATION = "global"

def download_audio(url, output_name):
    """
    从 URL 下载音频文件

    Args:
        url: 播客 URL
        output_name: 输出文件名（不含扩展名）

    Returns:
        音频文件路径
    """
    print(f"\n📥 下载音频...")
    print(f"   URL: {url}")

    audio_file = f"{output_name}.mp3"

    # 尝试使用 yt-dlp（支持多种网站）
    try:
        cmd = [
            'yt-dlp',
            '-x',  # 仅提取音频
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # 最高质量
            '-o', audio_file,
            url
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file) / (1024 * 1024)  # MB
            print(f"   ✓ 下载成功: {audio_file} ({file_size:.1f} MB)")
            return audio_file
        else:
            print(f"   ⚠️ yt-dlp 下载失败: {result.stderr}")

    except FileNotFoundError:
        print("   ⚠️ 未找到 yt-dlp，尝试使用其他方法...")

    # 如果 yt-dlp 不可用，尝试直接下载（适用于直接音频链接）
    try:
        import requests
        print("   尝试直接下载音频...")

        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        # 检查是否是音频文件
        content_type = response.headers.get('content-type', '')
        if 'audio' not in content_type:
            print(f"   ⚠️ URL 不是直接的音频链接 (content-type: {content_type})")
            print("   提示：请安装 yt-dlp 以支持播客网站: pip install yt-dlp")
            return None

        with open(audio_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(audio_file) / (1024 * 1024)
        print(f"   ✓ 下载成功: {audio_file} ({file_size:.1f} MB)")
        return audio_file

    except Exception as e:
        print(f"   ⚠️ 下载失败: {e}")
        return None

def extract_structured_show_notes(soup, url):
    """
    结构化提取 show notes（针对主流播客平台）

    Returns:
        dict with show_notes, guests, hosts (if found)
    """
    result = {
        'show_notes': '',
        'guests': [],
        'hosts': [],
        'extraction_method': 'none'
    }

    # 1. 尝试 JSON-LD structured data (最准确)
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    for script in json_ld_scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and data.get('@type') in ['PodcastEpisode', 'RadioEpisode']:
                result['show_notes'] = data.get('description', '')
                result['extraction_method'] = 'json-ld'
                print(f"   ✓ JSON-LD: 找到结构化数据")
                break
        except Exception:
            continue

    # 2. 尝试平台特定的 CSS selectors
    # 即使 JSON-LD 有内容，如果太短（<300字）也尝试 CSS 获取更完整的 show notes
    if not result['show_notes'] or len(result['show_notes']) < 300:
        platform_selectors = {
            # Fireside (sv101.fireside.fm)
            'fireside': [
                'div.episode-description',
                'div.episode_description',
                'div#episode-description',
            ],
            # Spotify
            'spotify': [
                'div[data-testid="episode-description"]',
                'div.Type__TypeElement-goli3j-0.fZDcWX',
            ],
            # Apple Podcasts
            'apple': [
                'div.episode-description__text',
                'div.we-truncate',
            ],
            # 通用
            'generic': [
                'div.show-notes',
                'section.show-notes',
                'div.description',
                'article.episode',
                '[itemprop="description"]',
            ]
        }

        # 按域名选择合适的 selectors
        domain = url.lower()
        if 'fireside.fm' in domain:
            selectors = platform_selectors['fireside'] + platform_selectors['generic']
        elif 'spotify.com' in domain:
            selectors = platform_selectors['spotify'] + platform_selectors['generic']
        elif 'apple.com' in domain:
            selectors = platform_selectors['apple'] + platform_selectors['generic']
        else:
            selectors = platform_selectors['generic']

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                result['show_notes'] = element.get_text(separator='\n').strip()
                result['extraction_method'] = f'css: {selector}'
                print(f"   ✓ CSS Selector: {selector} ({len(result['show_notes'])} 字)")
                break

    # 3. 尝试从 show notes 中提取嘉宾/主持人
    if result['show_notes']:
        import re

        # 匹配常见格式
        patterns = {
            'guests': [
                r'嘉宾[：:]\s*([^\n]+)',
                r'Guest[s]?[：:]\s*([^\n]+)',
                r'特邀[：:]\s*([^\n]+)',
            ],
            'hosts': [
                r'主持人?[：:]\s*([^\n]+)',
                r'Host[s]?[：:]\s*([^\n]+)',
                r'主播[：:]\s*([^\n]+)',
            ]
        }

        for role, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, result['show_notes'])
                if match:
                    # 分割多个名字
                    names_str = match.group(1)
                    names = re.split(r'[,，、&和]', names_str)
                    result[role] = [n.strip() for n in names if n.strip()]
                    if result[role]:
                        print(f"   ✓ 正则提取 {role}: {result[role]}")
                        break

    # 4. Fallback: 使用 main/article（如果 show notes 仍然太短）
    if not result['show_notes'] or len(result['show_notes']) < 300:
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_=lambda x: x and ('content' in x or 'description' in x))
        )

        if main_content:
            result['show_notes'] = main_content.get_text(separator='\n')[:2000]
            result['extraction_method'] = 'fallback: main/article'
        else:
            # 最后的 fallback
            result['show_notes'] = soup.get_text(separator='\n')[:2000]
            result['extraction_method'] = 'fallback:全文'

    return result

def extract_page_info(url):
    """
    从播客 URL 抓取页面信息（结构化提取）

    Returns:
        页面文本（标题 + 描述 + show notes）
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        print(f"\n📡 抓取播客页面信息...")
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. 提取标题（多来源）
        title_text = ""
        # 优先级：og:title > title tag
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title and og_title.get('content'):
            title_text = og_title.get('content').strip()
        else:
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""

        # 2. 提取描述
        description = ""
        for tag in ['og:description', 'description', 'twitter:description']:
            meta = soup.find('meta', attrs={'name': tag}) or soup.find('meta', attrs={'property': tag})
            if meta and meta.get('content'):
                description = meta.get('content').strip()
                break

        # 3. **结构化提取 show notes**
        structured = extract_structured_show_notes(soup, url)

        # 4. **提取发布日期**
        publish_date = None
        # 尝试多种来源
        date_sources = [
            # JSON-LD
            ('script[type="application/ld+json"]', 'datePublished'),
            # Meta tags
            ('meta[property="article:published_time"]', 'content'),
            ('meta[name="publish_date"]', 'content'),
            ('meta[name="date"]', 'content'),
            # Time tag
            ('time[datetime]', 'datetime'),
            ('time.published', 'datetime'),
        ]

        for selector, attr in date_sources:
            if publish_date:
                break
            elements = soup.select(selector)
            for el in elements:
                if attr == 'datePublished' and el.string:
                    # JSON-LD
                    try:
                        import json as json_module
                        data = json_module.loads(el.string)
                        if isinstance(data, dict):
                            publish_date = data.get('datePublished') or data.get('uploadDate')
                            if publish_date:
                                break
                    except Exception:
                        pass
                else:
                    publish_date = el.get(attr)
                    if publish_date:
                        break

        # 尝试从文本中提取日期
        if not publish_date:
            import re
            # 常见日期格式
            date_patterns = [
                r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',  # 2025-01-15
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',  # 01-15-2025
                r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})',  # Jan 15, 2025
            ]
            page_text = soup.get_text()[:2000]
            for pattern in date_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    publish_date = match.group(1)
                    break

        print(f"   ✓ 标题: {title_text[:80]}...")
        print(f"   ✓ 描述: {description[:100]}..." if description else "   - 未找到描述")
        print(f"   ✓ 发布日期: {publish_date}" if publish_date else "   - 未找到发布日期")
        print(f"   ✓ 提取方法: {structured['extraction_method']}")

        # 合并所有信息（结构化）
        combined = f"标题: {title_text}\n\n描述: {description}\n\n"

        if publish_date:
            combined += f"发布日期: {publish_date}\n"
        if structured['hosts']:
            combined += f"主持人: {', '.join(structured['hosts'])}\n"
        if structured['guests']:
            combined += f"嘉宾: {', '.join(structured['guests'])}\n"

        combined += f"\nShow Notes:\n{structured['show_notes']}"

        # 返回结构化数据（而不只是文本）
        return {
            'text': combined,
            'title': title_text,
            'description': description,
            'publish_date': publish_date,
            'hosts': structured['hosts'],
            'guests': structured['guests'],
            'show_notes': structured['show_notes']
        }

    except ImportError:
        print("   ⚠️ 需要安装 requests 和 beautifulsoup4:")
        print("      pip install requests beautifulsoup4")
        return None
    except Exception as e:
        print(f"   ⚠️ 抓取失败: {e}")
        return None

def extract_participants_with_llm(page_info):
    """
    使用 Gemini 从页面信息中提取参与者和时间信息

    Args:
        page_info: dict 或 str，页面信息

    Returns:
        参与者信息字典（包含日期）
    """
    # 兼容旧格式（纯文本）
    if isinstance(page_info, str):
        page_text = page_info
        publish_date = None
    else:
        page_text = page_info.get('text', '')
        publish_date = page_info.get('publish_date')

    system_prompt = """你是播客信息提取专家，负责从网页内容中提取参与者和时间信息。

任务：识别播客的主持人、嘉宾、节目信息和时间

识别规则：
1. **主持人**：
   - 主持人、Host、主播
   - "我是XXX"、"欢迎收听XXX，我是XXX"
   - 通常在开场介绍节目

2. **嘉宾**：
   - 嘉宾、Guest、特邀
   - "今天请到了XXX"、"XXX是XXX的创始人"
   - 专业背景描述

3. **节目信息**：
   - 节目名称、期数（如 #233、EP233）
   - 话题/主题

4. **时间信息**：
   - 发布日期：从页面元数据提取
   - 录制日期：从 show notes 中寻找（如"录制于2025年1月15日"）

输出 JSON 格式：
{
  "host": ["主持人1", "主持人2"],
  "guests": ["嘉宾1", "嘉宾2"],
  "episode_info": "节目名称 #期数 - 话题",
  "guest_background": {
    "嘉宾1": "背景信息（职位、公司等）",
    "嘉宾2": "背景信息"
  },
  "publish_date": "2025-01-20",
  "record_date": "2025-01-15",
  "date_notes": "如果日期是推断的，说明推断依据"
}

注意：
- 中文名字用中文，英文名字用英文
- 日期格式统一为 YYYY-MM-DD
- 如果找不到录制日期，可以留空或用发布日期估算
- 严格输出 JSON，不要添加其他说明
"""

    try:
        client = get_gemini_client(location=LOCATION)
        print(f"\n🤖 使用 Gemini 3-Pro 分析参与者信息...")

        # 合并system prompt和user content
        full_prompt = f"{system_prompt}\n\n{page_text}"

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=65536
            )
        )

        # 提取JSON（Gemini可能返回带markdown的内容）
        response_text = response.text or ""
        if '```json' in response_text:
            start = response_text.find('```json') + 7
            end = response_text.find('```', start)
            response_text = response_text[start:end].strip()
        elif '{' in response_text:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            response_text = response_text[start:end]

        result = json.loads(response_text)

        # 如果 LLM 没提取到发布日期，用页面提取的
        if not result.get('publish_date') and publish_date:
            result['publish_date'] = publish_date

        print(f"   ✓ 主持人: {', '.join(result.get('host', []))}")
        print(f"   ✓ 嘉宾: {', '.join(result.get('guests', []))}")
        print(f"   ✓ 节目: {result.get('episode_info', '未知')}")
        print(f"   ✓ 发布日期: {result.get('publish_date', '未知')}")
        print(f"   ✓ 录制日期: {result.get('record_date', '未知')}")

        return result

    except Exception as e:
        print(f"   ⚠️ LLM 分析失败: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python step0_download_and_prepare.py <podcast_url> [output_name]")
        print("")
        print("参数:")
        print("  podcast_url  : 播客页面 URL")
        print("  output_name  : 输出文件名前缀（可选，默认为 podcast）")
        print("")
        print("示例:")
        print("  python step0_download_and_prepare.py https://sv101.fireside.fm/233 sv101_ep233")
        print("")
        print("输出文件:")
        print("  - {output_name}.mp3 : 音频文件")
        print("  - participants.json : 参与者信息")
        print("")
        print("依赖安装:")
        print("  pip install yt-dlp requests beautifulsoup4")
        sys.exit(1)

    url = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else "podcast"

    print("=" * 60)
    print("🎙️  播客下载与准备工具")
    print("=" * 60)

    # 步骤 1: 下载音频
    audio_file = download_audio(url, output_name)

    # 步骤 2: 提取页面信息
    page_text = extract_page_info(url)

    # 步骤 3: 分析参与者
    participants = None
    if page_text:
        participants = extract_participants_with_llm(page_text)

    # 如果 LLM 提取失败，退出（后续步骤依赖参与者信息）
    if not participants:
        print("\n❌ 无法从页面提取参与者信息，请检查 Gemini API 连接")
        sys.exit(1)

    # 保存参与者信息（始终保存，即使是默认结构）
    participants_file = "participants.json"
    print(f"\n💾 保存参与者信息: {participants_file}")
    with open(participants_file, 'w', encoding='utf-8') as f:
        json.dump(participants, f, ensure_ascii=False, indent=2)

    # 总结
    print("\n" + "=" * 60)
    print("✅ 准备完成！")
    print("=" * 60)

    if audio_file and os.path.exists(audio_file):
        file_size = os.path.getsize(audio_file) / (1024 * 1024)
        print(f"✓ 音频文件: {audio_file} ({file_size:.1f} MB)")
    else:
        print("✗ 音频下载失败")

    # 参与者信息始终会保存
    print(f"✓ 参与者信息: participants.json")

    print("\n下一步:")
    if audio_file:
        print(f"  python step1_transcribe_advanced.py {audio_file}")
    else:
        print("  请手动下载音频，然后运行:")
        print("  python step1_transcribe_advanced.py <audio_file>")

    if not audio_file:
        sys.exit(1)

if __name__ == "__main__":
    main()
