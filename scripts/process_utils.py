#!/usr/bin/env python3
"""
播客处理 - 单集或批量

使用方法：
    # 单集处理
    python process_utils.py <url>

    # 批量处理（从 RSS）
    python process_utils.py --rss <rss_url> [--limit N] [--start N]

    # 批量处理（从文件）
    python process_utils.py --file <url_list.txt>

    # 强制重跑（忽略已有文件）
    python process_utils.py <url> --force
"""

import os
import sys
import re
import json
import subprocess
import shutil
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from google.genai import types
from gemini_utils import get_gemini_client, DEFAULT_MODEL, clean_json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')
PROGRESS_FILE = os.path.join(PROJECT_ROOT, 'batch_progress.json')

# 虚拟环境
VENV_BIN = os.path.join(PROJECT_ROOT, 'venv', 'bin')
PYTHON_BIN = os.path.join(VENV_BIN, 'python3') if os.path.exists(VENV_BIN) else 'python3'
def _build_env():
    """Build subprocess environment with venv paths."""
    env = os.environ.copy()
    if os.path.exists(VENV_BIN):
        env['PATH'] = f"{VENV_BIN}:{env.get('PATH', '')}"
        env['VIRTUAL_ENV'] = os.path.join(PROJECT_ROOT, 'venv')
    return env


# =============================================================================
# 依赖链检查
# =============================================================================

def _needs_rerun(source_files, target_file):
    """检查目标文件是否需要重跑（源文件比目标文件新，或目标不存在）"""
    if not os.path.exists(target_file):
        return True
    target_mtime = os.path.getmtime(target_file)
    for src in source_files:
        if isinstance(src, str) and os.path.exists(src):
            if os.path.getmtime(src) > target_mtime:
                return True
    return False


# =============================================================================
# Sanity checks
# =============================================================================

def _check_transcript(transcript_file):
    """检查转录结果质量"""
    with open(transcript_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    segments = data.get('segments', [])
    if not segments:
        print(f"  ❌ Sanity check 失败: 转录为空")
        return False
    speakers = {}
    for seg in segments:
        sp = seg.get('speaker', 'Unknown')
        speakers[sp] = speakers.get(sp, 0) + 1
    total = sum(speakers.values())
    unknown = speakers.get('Unknown', 0) + speakers.get('SPEAKER_00', 0)
    if total > 0 and unknown / total > 0.5:
        print(f"  ❌ Sanity check 失败: {unknown}/{total} 段未识别说话人")
        return False
    print(f"  ✓ 转录: {len(segments)} 段, 说话人: {speakers}")
    return True


def _check_signals(signals_file):
    """检查信号提取结果"""
    with open(signals_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    signals = data.get('signals', [])
    if not signals:
        print(f"  ⚠️ 信号为空（可能是正常的，取决于播客内容）")
    else:
        print(f"  ✓ 信号: {len(signals)} 个")
    return True


# =============================================================================
# 播客配置
# =============================================================================

def load_podcast_config():
    config_file = os.path.join(CONFIG_DIR, 'podcasts.json')
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"podcasts": {}}


def match_podcast(url):
    config = load_podcast_config()
    for podcast_id, podcast_config in config['podcasts'].items():
        for pattern in podcast_config.get('url_patterns', []):
            match = re.search(pattern, url)
            if match:
                episode_id = match.group(1)
                return podcast_id, episode_id, podcast_config

    generic_patterns = [
        r'([^/]+)\.(fireside\.fm|podbean\.com|transistor\.fm|anchor\.fm)/(\d+)',
        r'([^/]+)\.(fireside\.fm|podbean\.com|transistor\.fm|anchor\.fm)/episodes?/([^/]+)',
        r'youtube\.com/watch\?v=([^&]+)',
        r'youtu\.be/([^?]+)',
    ]
    for pattern in generic_patterns:
        match = re.search(pattern, url)
        if match:
            groups = match.groups()
            if len(groups) >= 3:
                podcast_id = groups[0].replace('-', '_')
                episode_id = groups[2]
            else:
                podcast_id = 'unknown'
                episode_id = groups[0]
            return podcast_id, episode_id, {
                'name': podcast_id,
                'base_url': urllib.parse.urlparse(url)._replace(path='', params='', query='', fragment='').geturl(),
                'hosts': [],
                'language': 'en'
            }
    return None, None, None


# =============================================================================
# 步骤执行
# =============================================================================

def run_step(step_name, cmd):
    """运行单个步骤"""
    print(f"\n{'='*60}")
    print(f"  {step_name}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, cwd=SCRIPTS_DIR, capture_output=True, text=True, env=_build_env())

    if result.returncode != 0:
        print(f"  [失败]")
        if result.stderr:
            print(f"  错误: {result.stderr[:500]}")
        if result.stdout:
            print(f"  输出: {result.stdout[:500]}")
        return False

    print(f"  [完成]")
    return True


# =============================================================================
# 单集处理（含依赖链检查 + sanity check）
# =============================================================================

def process_single(url, audio_url=None, force=False):
    """处理单个播客的完整流程（4 步）

    Step 0: 下载音频 + 提取参与者
    Step 1: Gemini 音频转录（转录 + 说话人标注 + 书面化）
    Step 2: 提取投资信号（含公司识别）
    Step 3: 验证信号（Google Search + 市场数据）
    Step 4: 生成投资笔记
    """

    podcast_id, episode_id, podcast_config = match_podcast(url)
    if not podcast_id:
        print(f"无法识别播客 URL: {url}")
        return False

    prefix = f"{podcast_id}_ep{episode_id}"
    episode_dir = os.path.join(OUTPUT_DIR, prefix)
    os.makedirs(episode_dir, exist_ok=True)

    print(f"\n处理播客: {podcast_config.get('name', podcast_id)}")
    print(f"Episode: {episode_id}")
    print(f"URL: {url}")
    print(f"输出目录: {episode_dir}")

    # 文件路径
    metadata_file = os.path.join(episode_dir, f'{prefix}_metadata.json')
    audio_file = os.path.join(episode_dir, f'{episode_id}.mp3')
    participants_file = os.path.join(episode_dir, f'{prefix}_participants.json')
    transcript_file = os.path.join(episode_dir, f'{episode_id}_transcript_gemini.json')
    signals_file = os.path.join(episode_dir, f'{prefix}_signals.json')
    verified_file = os.path.join(episode_dir, f'{prefix}_verified_signals.json')
    notes_dir = os.path.join(OUTPUT_DIR, 'notes')
    os.makedirs(notes_dir, exist_ok=True)
    notes_file = os.path.join(notes_dir, f'{prefix}_investment_notes.md')

    # 加载已有 metadata 或创建新的
    metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    metadata['podcast_id'] = podcast_id
    metadata['podcast_name'] = podcast_config.get('name', podcast_id)
    metadata['episode_id'] = episode_id
    metadata['url'] = url
    metadata['base_url'] = podcast_config.get('base_url', '')
    metadata['hosts'] = podcast_config.get('hosts', [])
    metadata['language'] = podcast_config.get('language', 'en')
    metadata.setdefault('publish_date', None)
    metadata.setdefault('record_date', None)
    metadata.setdefault('date_notes', None)
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # ── Step 0: 下载音频 + 提取参与者 ──
    if force or not os.path.exists(audio_file) or not os.path.exists(participants_file):
        audio_base = os.path.join(episode_dir, episode_id)
        download_url = audio_url if audio_url else url
        if os.path.exists(audio_file):
            print(f"\n  [跳过] 音频已存在")
            print(f"  [继续] 提取参与者信息...")
        if not run_step("Step 0: 下载音频 + 提取参与者",
                       [PYTHON_BIN, 'step0_download_and_prepare.py', download_url, audio_base]):
            if not os.path.exists(audio_file):
                return False
    else:
        print(f"\n  [跳过] 音频和参与者已存在")

    # 移动 participants.json
    temp_participants = os.path.join(SCRIPTS_DIR, 'participants.json')
    temp_participants_safe = os.path.join(SCRIPTS_DIR, f'participants_{episode_id}.json')
    if os.path.exists(temp_participants):
        shutil.move(temp_participants, temp_participants_safe)
    if os.path.exists(temp_participants_safe):
        shutil.move(temp_participants_safe, participants_file)
        print(f"  [移动] participants.json -> {participants_file}")

    # 合并日期到 metadata
    if os.path.exists(participants_file):
        with open(participants_file, 'r', encoding='utf-8') as f:
            participants = json.load(f)
        metadata['publish_date'] = participants.get('publish_date')
        metadata['record_date'] = participants.get('record_date')
        metadata['date_notes'] = participants.get('date_notes')
        metadata['guests'] = participants.get('guests', [])
        metadata['guest_background'] = participants.get('guest_background', {})
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"  [更新] metadata: publish={metadata['publish_date']}")

    # ── Step 1: Gemini 音频转录（一步到位：转录 + 说话人 + 书面化）──
    if force or _needs_rerun([audio_file, participants_file], transcript_file):
        if not run_step("Step 1: Gemini 音频转录",
                       [PYTHON_BIN, 'step1_transcribe_gemini.py', audio_file, participants_file, transcript_file]):
            # 检查文件是否生成（进程可能非零退出但文件已生成）
            if not os.path.exists(transcript_file):
                print(f"  ❌ 转录文件未生成")
                return False
        # Sanity check
        if not _check_transcript(transcript_file):
            return False
    else:
        print(f"\n  [跳过] 转录已存在")

    # ── Step 2: 提取投资信号（合并公司提取，依赖: transcript）──
    if force or _needs_rerun([transcript_file], signals_file):
        if not run_step("Step 2: 提取投资信号",
                       [PYTHON_BIN, 'step2_extract_signals.py', transcript_file, signals_file]):
            return False
        _check_signals(signals_file)
    else:
        print(f"\n  [跳过] 信号已存在")

    # ── Step 3: 验证信号（依赖: signals）──
    if force or _needs_rerun([signals_file], verified_file):
        if not run_step("Step 3: 验证信号",
                       [PYTHON_BIN, 'step3_verify_signals.py', signals_file, verified_file]):
            return False
    else:
        print(f"\n  [跳过] 验证已存在")

    # ── Step 4: 生成投资笔记（依赖: transcript + signals + verified）──
    if force or _needs_rerun([transcript_file, signals_file, verified_file], notes_file):
        if not run_step("Step 4: 生成投资笔记",
                       [PYTHON_BIN, 'step4_generate_notes.py', transcript_file, signals_file, verified_file, notes_file]):
            return False
    else:
        print(f"\n  [跳过] 笔记已存在")

    print(f"\n{'='*60}")
    print(f"  处理完成!")
    print(f"{'='*60}")
    print(f"  投资笔记: {notes_file}")

    return True


# =============================================================================
# 批量处理
# =============================================================================

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'processed': [], 'failed': [], 'last_updated': None}


def save_progress(progress):
    progress['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def extract_from_rss(rss_url):
    try:
        import feedparser
    except ImportError:
        print("需要安装 feedparser: pip install feedparser")
        sys.exit(1)

    print(f"\n📡 解析 RSS feed: {rss_url}")
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            print("   ⚠️ RSS feed 为空")
            return []

        episodes = []
        for entry in feed.entries:
            audio_url = None
            if hasattr(entry, 'enclosures') and entry.enclosures:
                for enc in entry.enclosures:
                    if enc.get('type', '').startswith('audio/'):
                        audio_url = enc.get('href') or enc.get('url')
                        break
            episode = {
                'title': entry.get('title', 'Unknown'),
                'url': entry.get('link', ''),
                'audio_url': audio_url,
                'date': entry.get('published', ''),
            }
            if episode['url'] or episode['audio_url']:
                episodes.append(episode)

        print(f"   ✓ 找到 {len(episodes)} 个播客")
        return episodes
    except Exception as e:
        print(f"   ✗ RSS 解析失败: {e}")
        return []


def read_url_file(file_path):
    urls = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append({'url': line, 'title': line})
    return urls


def process_batch(episodes, skip_existing=False, delay=5, force=False):
    progress = load_progress()
    success_count = 0
    fail_count = 0
    skip_count = 0

    for i, episode in enumerate(episodes, 1):
        url = episode['url']
        title = episode.get('title', url)

        if skip_existing and url in progress['processed']:
            print(f"\n[{i}/{len(episodes)}] ⏭️  跳过: {title}")
            skip_count += 1
            continue

        print(f"\n[{i}/{len(episodes)}] 处理中: {title}")

        audio_url = episode.get('audio_url')
        success = process_single(url, audio_url=audio_url, force=force)

        if success:
            success_count += 1
            if url not in progress['processed']:
                progress['processed'].append(url)
            if url in progress['failed']:
                progress['failed'].remove(url)
        else:
            fail_count += 1
            if url not in progress['failed']:
                progress['failed'].append(url)

        save_progress(progress)

        remaining = len(episodes) - i
        if remaining > 0 and delay > 0:
            print(f"\n⏸️  休息 {delay} 秒...")
            time.sleep(delay)

    print("\n" + "="*60)
    print("📊 批量处理完成")
    print("="*60)
    print(f"   成功: {success_count}")
    print(f"   跳过: {skip_count}")
    print(f"   失败: {fail_count}")

    if progress['failed']:
        print(f"\n⚠️  失败的播客:")
        for url in progress['failed'][-5:]:
            print(f"   - {url}")


# =============================================================================
# 主入口
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='播客处理 - 单集或批量',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python process_utils.py https://sv101.fireside.fm/233
  python process_utils.py --rss https://sv101.fireside.fm/rss --limit 5
  python process_utils.py --file urls.txt --skip-existing
  python process_utils.py https://sv101.fireside.fm/233 --force
        """
    )

    parser.add_argument('url', nargs='?', help='播客 URL（单集模式）')
    parser.add_argument('--rss', help='RSS feed URL（批量模式）')
    parser.add_argument('--file', help='URL 列表文件（批量模式）')
    parser.add_argument('--start', type=int, default=0, help='从第几个开始')
    parser.add_argument('--limit', type=int, help='处理几个')
    parser.add_argument('--skip-existing', action='store_true', help='跳过已处理的')
    parser.add_argument('--delay', type=int, default=5, help='批量延迟秒数')
    parser.add_argument('--force', action='store_true', help='强制重跑所有步骤')

    args = parser.parse_args()

    if args.rss:
        print("="*60)
        print("🚀 批量处理（RSS 模式）")
        print("="*60)
        episodes = extract_from_rss(args.rss)
        if not episodes:
            sys.exit(1)
        end = args.start + args.limit if args.limit else len(episodes)
        episodes = episodes[args.start:end]
        print(f"\n📊 待处理: {len(episodes)} 个")
        process_batch(episodes, args.skip_existing, args.delay, args.force)

    elif args.file:
        if not os.path.exists(args.file):
            print(f"❌ 文件不存在: {args.file}")
            sys.exit(1)
        print("="*60)
        print("🚀 批量处理（文件模式）")
        print("="*60)
        episodes = read_url_file(args.file)
        print(f"\n📊 找到 {len(episodes)} 个 URL")
        process_batch(episodes, args.skip_existing, args.delay, args.force)

    elif args.url:
        if not process_single(args.url, force=args.force):
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
