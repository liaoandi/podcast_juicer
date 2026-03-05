#!/usr/bin/env python3
"""
搜索播客官方文字稿

在转录之前，先尝试找官方文字稿：
1. 检查播客官网页面
2. Google 搜索 "播客名 + 期数 + 文字稿"
3. 搜狗微信搜索公众号文章

如果找到文字稿，可以跳过语音转录步骤。
"""

import os
import subprocess
import sys
import json
import re
import time
import requests
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}


def load_env():
    """加载环境变量"""
    env_file = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def check_podcast_page(url):
    """
    检查播客官网页面是否有文字稿

    Args:
        url: 播客单集页面 URL

    Returns:
        dict: {'found': bool, 'transcript': str, 'source': str} 或 None
    """
    print(f"   检查官网页面: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 查找常见的 transcript 容器
        transcript_selectors = [
            # 常见的 transcript 类名/ID
            {'class': re.compile(r'transcript', re.I)},
            {'id': re.compile(r'transcript', re.I)},
            {'class': re.compile(r'episode-transcript', re.I)},
            {'class': re.compile(r'show-notes', re.I)},
            # data 属性
            {'data-transcript': True},
        ]

        for selector in transcript_selectors:
            elements = soup.find_all(**selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                # 文字稿通常比较长（至少 1000 字）
                if len(text) > 1000:
                    print(f"   ✓ 在官网找到文字稿 ({len(text)} 字)")
                    return {
                        'found': True,
                        'transcript': text,
                        'source': url,
                        'source_type': 'podcast_page'
                    }

        # 检查是否有 transcript 链接
        transcript_links = soup.find_all('a', href=True, string=re.compile(r'transcript|文字稿|逐字稿', re.I))
        for link in transcript_links[:3]:
            transcript_url = urljoin(url, link['href'])
            print(f"   发现文字稿链接: {transcript_url}")
            # 递归获取
            result = fetch_transcript_page(transcript_url)
            if result:
                return result

    except Exception as e:
        print(f"   ⚠️ 检查官网失败: {e}")

    return None


def fetch_transcript_page(url):
    """获取文字稿页面内容"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 移除脚本和样式
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()

        # 获取主要内容
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
            if len(text) > 1000:
                return {
                    'found': True,
                    'transcript': text,
                    'source': url,
                    'source_type': 'transcript_page'
                }
    except Exception as e:
        print(f"   ⚠️ 获取文字稿页面失败: {e}")

    return None


def search_google(podcast_name, episode_id, episode_title=None):
    """
    通过 Google 搜索文字稿

    Args:
        podcast_name: 播客名称
        episode_id: 期数
        episode_title: 标题（可选）

    Returns:
        dict 或 None
    """
    # 构建搜索词
    queries = [
        f'"{podcast_name}" "{episode_id}" 文字稿',
        f'"{podcast_name}" {episode_id} transcript',
    ]
    if episode_title:
        queries.insert(0, f'"{podcast_name}" "{episode_title}" 文字稿')

    print(f"   Google 搜索文字稿...")

    for query in queries:
        try:
            # 使用 Google 搜索 API 或爬取
            # 这里用简化的方式：直接用 requests
            search_url = f"https://www.google.com/search?q={quote(query)}"

            response = requests.get(search_url, headers={
                **HEADERS,
                'Accept': 'text/html',
            }, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 查找搜索结果链接
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # 提取实际 URL
                    if '/url?q=' in href:
                        actual_url = href.split('/url?q=')[1].split('&')[0]
                        # 排除 Google 自己的链接
                        if 'google.com' not in actual_url and 'youtube.com' not in actual_url:
                            # 检查是否是文字稿页面
                            if any(kw in actual_url.lower() for kw in ['transcript', 'wenzi', '文字']):
                                print(f"   发现可能的文字稿: {actual_url}")
                                result = fetch_transcript_page(actual_url)
                                if result:
                                    result['source_type'] = 'google_search'
                                    return result

            time.sleep(1)  # 避免请求过快

        except Exception as e:
            print(f"   ⚠️ Google 搜索失败: {e}")

    return None


def search_bing(podcast_name, episode_id, episode_title=None):
    """
    通过 Bing 搜索文字稿

    Args:
        podcast_name: 播客名称
        episode_id: 期数
        episode_title: 标题（可选）

    Returns:
        dict 或 None
    """
    print(f"   Bing 搜索...")

    # 构建搜索词
    queries = [
        f'{podcast_name} {episode_id} 文字稿',
        f'{podcast_name} {episode_id} transcript',
        f'site:mp.weixin.qq.com {podcast_name} {episode_id}',  # 直接搜微信公众号
    ]
    if episode_title:
        queries.insert(0, f'{podcast_name} {episode_title} 文字稿')

    for query in queries:
        try:
            search_url = f"https://www.bing.com/search?q={quote(query)}"

            response = requests.get(search_url, headers={
                **HEADERS,
                'Accept-Language': 'zh-CN,zh;q=0.9',
            }, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Bing 搜索结果
                results = soup.find_all('li', class_='b_algo')

                for result in results[:5]:
                    link = result.find('a', href=True)
                    if link:
                        href = link.get('href', '')
                        title = link.get_text(strip=True)

                        # 检查是否是微信文章或文字稿页面
                        if 'mp.weixin.qq.com' in href:
                            print(f"   发现微信文章: {title[:40]}...")
                            article_result = fetch_weixin_article_direct(href)
                            if article_result:
                                article_result['title'] = title
                                article_result['source_type'] = 'bing_weixin'
                                return article_result

                        # 其他可能的文字稿页面
                        if any(kw in href.lower() or kw in title.lower() for kw in ['文字稿', 'transcript', '逐字稿']):
                            print(f"   发现可能的文字稿: {title[:40]}...")
                            page_result = fetch_transcript_page(href)
                            if page_result:
                                page_result['source_type'] = 'bing_search'
                                return page_result

            time.sleep(1)

        except Exception as e:
            print(f"   ⚠️ Bing 搜索失败: {e}")

    return None


def search_sogou_weixin(podcast_name, episode_id, episode_title=None):
    """
    通过搜狗微信搜索公众号文章（备用，有反爬虫限制）

    Args:
        podcast_name: 播客名称（也是公众号名）
        episode_id: 期数
        episode_title: 标题（可选）

    Returns:
        dict 或 None
    """
    print(f"   搜狗微信搜索...")

    # 构建搜索词
    queries = [
        f'{podcast_name} {episode_id}',
    ]
    if episode_title:
        queries.insert(0, f'{podcast_name} {episode_title}')

    for query in queries:
        try:
            search_url = f"https://weixin.sogou.com/weixin?type=2&query={quote(query)}"

            response = requests.get(search_url, headers={
                **HEADERS,
                'Referer': 'https://weixin.sogou.com/',
            }, timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # 查找搜索结果
                results = soup.find_all('div', class_='txt-box')

                for result in results[:5]:  # 只看前5个结果
                    title_elem = result.find('a')
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        href = title_elem.get('href')

                        # 检查标题是否匹配
                        if podcast_name in title or (episode_title and episode_title[:10] in title):
                            print(f"   发现公众号文章: {title}")

                            # 获取文章内容
                            if href:
                                # 搜狗返回的是相对路径，需要拼接完整 URL
                                if href.startswith('/'):
                                    href = f"https://weixin.sogou.com{href}"
                                article_result = fetch_weixin_article(href)
                                if article_result:
                                    article_result['title'] = title
                                    return article_result

            time.sleep(1)

        except Exception as e:
            print(f"   ⚠️ 搜狗微信搜索失败: {e}")

    return None


def fetch_weixin_article(url):
    """
    获取微信公众号文章内容

    注意：微信文章有反爬虫机制，可能需要处理
    搜狗微信的链接会先跳转到中间页，需要提取真实的微信 URL
    """
    try:
        print(f"   尝试获取: {url[:80]}...")
        response = requests.get(url, headers={
            **HEADERS,
            'Referer': 'https://weixin.sogou.com/',
        }, timeout=30, allow_redirects=True)

        print(f"   响应状态: {response.status_code}, 最终URL: {response.url[:60]}...")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 检查是否是跳转页面（搜狗中间页）
            # 搜狗会返回一个 JS 跳转页面，需要提取真实 URL
            script_tags = soup.find_all('script')
            for script in script_tags:
                script_text = script.string or ''
                # 查找 location.replace 或类似的跳转
                if 'mp.weixin.qq.com' in script_text:
                    url_match = re.search(r"(https?://mp\.weixin\.qq\.com[^'\"]+)", script_text)
                    if url_match:
                        real_url = url_match.group(1)
                        print(f"   发现微信文章真实URL: {real_url[:60]}...")
                        # 递归获取真实文章
                        return fetch_weixin_article_direct(real_url)

            # 直接尝试解析（可能已经是微信页面）
            content_elem = soup.find('div', id='js_content') or soup.find('div', class_='rich_media_content')

            if content_elem:
                text = content_elem.get_text(separator='\n', strip=True)
                if len(text) > 500:
                    print(f"   ✓ 获取到公众号文章 ({len(text)} 字)")
                    return {
                        'found': True,
                        'transcript': text,
                        'source': response.url,
                        'source_type': 'weixin_article'
                    }
                else:
                    print(f"   文章内容太短: {len(text)} 字")
            else:
                print(f"   未找到文章内容元素")

    except Exception as e:
        print(f"   ⚠️ 获取微信文章失败: {e}")

    return None


def fetch_weixin_article_direct(url):
    """直接获取微信文章内容"""
    try:
        response = requests.get(url, headers={
            **HEADERS,
            'Referer': 'https://mp.weixin.qq.com/',
        }, timeout=30, allow_redirects=True)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            content_elem = soup.find('div', id='js_content') or soup.find('div', class_='rich_media_content')

            if content_elem:
                text = content_elem.get_text(separator='\n', strip=True)
                if len(text) > 500:
                    print(f"   ✓ 获取到公众号文章 ({len(text)} 字)")
                    return {
                        'found': True,
                        'transcript': text,
                        'source': response.url,
                        'source_type': 'weixin_article'
                    }
    except Exception as e:
        print(f"   ⚠️ 直接获取微信文章失败: {e}")

    return None


def search_transcript(podcast_url, podcast_name, episode_id, episode_title=None):
    """
    综合搜索文字稿

    Args:
        podcast_url: 播客单集页面 URL
        podcast_name: 播客名称
        episode_id: 期数（如 "235" 或 "ep235"）
        episode_title: 标题（可选）

    Returns:
        dict: {'found': bool, 'transcript': str, 'source': str, 'source_type': str}
    """
    print(f"\n🔍 搜索文字稿: {podcast_name} {episode_id}")

    # 1. 检查官网页面
    if podcast_url:
        result = check_podcast_page(podcast_url)
        if result:
            return result

    # 2. Google 搜索
    result = search_google(podcast_name, episode_id, episode_title)
    if result:
        return result

    # 3. Bing 搜索（包括 site:mp.weixin.qq.com）
    result = search_bing(podcast_name, episode_id, episode_title)
    if result:
        return result

    # 4. 搜狗微信搜索（备用，有反爬虫限制）
    # result = search_sogou_weixin(podcast_name, episode_id, episode_title)
    # if result:
    #     return result

    print(f"   ✗ 未找到官方文字稿")
    return {'found': False}


def _format_timestamp(seconds):
    seconds = max(0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def _get_audio_duration(audio_path):
    if not audio_path or not os.path.exists(audio_path):
        return None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True,
            text=True,
            check=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return None

def convert_to_segments(transcript_text, output_file, audio_path=None):
    """
    将文字稿转换为分段格式

    简单按段落分割，后续可以用 LLM 更精细地分割
    """
    paragraphs = [p.strip() for p in transcript_text.split('\n') if p.strip()]

    segments = []
    # 估算时间轴（优先使用音频时长，否则按字符数估计）
    total_chars = sum(len(p) for p in paragraphs) or 1
    audio_duration = _get_audio_duration(audio_path)
    chars_per_sec = float(os.getenv("TRANSCRIPT_CHARS_PER_SEC", "3.6"))
    total_duration = audio_duration if audio_duration else (total_chars / max(chars_per_sec, 1e-3))

    current_time = 0.0
    seg_count = 0
    for i, para in enumerate(paragraphs):
        if len(para) > 10:  # 过滤太短的段落
            # 分配该段时长（按字数比例）
            seg_duration = total_duration * (len(para) / total_chars)
            seg_duration = max(seg_duration, 2.0)  # 最小 2 秒
            start_sec = current_time
            end_sec = current_time + seg_duration
            current_time = end_sec
            segments.append({
                'id': seg_count,
                'seg_id': seg_count,
                'start': _format_timestamp(start_sec),
                'end': _format_timestamp(end_sec),
                'start_seconds': round(start_sec, 3),
                'end_seconds': round(end_sec, 3),
                'text': para,
                'speaker': 'Unknown'
            })
            seg_count += 1

    output = {
        'source_type': 'official_transcript',
        'is_official_transcript': True,
        'timing_estimated': True,
        'audio_duration_seconds': audio_duration,
        'language': 'zh',
        'segments': segments
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"   ✓ 已转换为 {len(segments)} 个段落")
    return output_file


# =============================================================================
# 主函数
# =============================================================================

def main():
    """命令行入口"""
    if len(sys.argv) < 4:
        print("用法: python step0b_search_transcript.py <podcast_url> <podcast_name> <episode_id> [output_file] [audio_file]")
        print("")
        print("参数:")
        print("  podcast_url  : 播客单集页面 URL")
        print("  podcast_name : 播客名称（如 '硅谷101'）")
        print("  episode_id   : 期数（如 '235'）")
        print("  output_file  : 输出文件路径（可选）")
        print("")
        print("示例:")
        print("  python step0b_search_transcript.py https://sv101.fireside.fm/235 硅谷101 235")
        sys.exit(1)

    load_env()

    podcast_url = sys.argv[1]
    podcast_name = sys.argv[2]
    episode_id = sys.argv[3]
    output_file = sys.argv[4] if len(sys.argv) > 4 else f'{episode_id}_official_transcript.json'
    audio_file = sys.argv[5] if len(sys.argv) > 5 else None

    # 搜索文字稿
    result = search_transcript(podcast_url, podcast_name, episode_id)

    if result.get('found'):
        # 转换并保存
        convert_to_segments(result['transcript'], output_file, audio_path=audio_file)
        print(f"\n✅ 找到官方文字稿！")
        print(f"   来源: {result.get('source_type')}")
        print(f"   URL: {result.get('source')}")
        sys.exit(0)
    else:
        print(f"\n❌ 未找到官方文字稿，需要使用语音转录")
        sys.exit(1)


if __name__ == "__main__":
    main()
