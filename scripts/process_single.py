#!/usr/bin/env python3
"""
处理单个播客 - 完整流程

使用方法：
    python scripts/process_single.py <podcast_url>

示例：
    python scripts/process_single.py https://sv101.fireside.fm/233
"""

import os
import sys
import re
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')

# 虚拟环境
VENV_BIN = os.path.join(PROJECT_ROOT, 'venv', 'bin')
PYTHON_BIN = os.path.join(VENV_BIN, 'python3') if os.path.exists(VENV_BIN) else 'python3'
ENV = os.environ.copy()
if os.path.exists(VENV_BIN):
    ENV['PATH'] = f"{VENV_BIN}:{ENV.get('PATH', '')}"
    ENV['VIRTUAL_ENV'] = os.path.join(PROJECT_ROOT, 'venv')


def run_step(step_name, cmd):
    """运行单个步骤"""
    print(f"\n{'='*60}")
    print(f"  {step_name}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, cwd=SCRIPTS_DIR, capture_output=True, text=True, env=ENV)

    if result.returncode != 0:
        print(f"  [失败]")
        if result.stderr:
            print(f"  错误: {result.stderr[:500]}")
        return False

    print(f"  [完成]")
    return True


def process_podcast(url):
    """处理单个播客的完整流程"""

    # 提取 episode ID
    match = re.search(r'/(\d+)$', url)
    if not match:
        print(f"无法从URL提取episode ID: {url}")
        sys.exit(1)

    episode_id = match.group(1)
    episode_dir = os.path.join(OUTPUT_DIR, f'sv101_ep{episode_id}')
    os.makedirs(episode_dir, exist_ok=True)

    print(f"\n处理播客: {url}")
    print(f"输出目录: {episode_dir}")

    # 文件路径
    audio_file = os.path.join(episode_dir, f'{episode_id}.mp3')
    participants_file = os.path.join(episode_dir, f'sv101_ep{episode_id}_participants.json')
    transcript_file = os.path.join(episode_dir, f'{episode_id}_transcript_advanced.json')
    speakers_file = os.path.join(episode_dir, f'{episode_id}_transcript_advanced_with_speakers.json')
    polished_file = os.path.join(episode_dir, f'{episode_id}_transcript_polished.json')
    watchlist_file = os.path.join(episode_dir, f'sv101_ep{episode_id}_watchlist.json')
    signals_file = os.path.join(episode_dir, f'sv101_ep{episode_id}_signals.json')
    verified_file = os.path.join(episode_dir, f'sv101_ep{episode_id}_verified_signals.json')
    notes_file = os.path.join(episode_dir, f'sv101_ep{episode_id}_investment_notes.md')

    # Step 0: 下载音频
    if not os.path.exists(audio_file):
        audio_base = os.path.join(episode_dir, episode_id)
        if not run_step("Step 0: 下载音频",
                       [PYTHON_BIN, 'step0_download_and_prepare.py', url, audio_base]):
            return False
    else:
        print(f"\n  [跳过] 音频已存在: {audio_file}")

    # Step 1: 转录
    if not os.path.exists(transcript_file):
        if not run_step("Step 1: 转录音频",
                       [PYTHON_BIN, 'step1_transcribe_advanced.py', audio_file, transcript_file]):
            return False
    else:
        print(f"\n  [跳过] 转录已存在: {transcript_file}")

    # Step 2: 识别说话人
    if not os.path.exists(speakers_file):
        if not run_step("Step 2: 识别说话人",
                       [PYTHON_BIN, 'step2_identify_speakers.py', transcript_file, participants_file, speakers_file]):
            return False
    else:
        print(f"\n  [跳过] 说话人识别已存在: {speakers_file}")

    # Step 3: 润色转录
    if not os.path.exists(polished_file):
        if not run_step("Step 3: 润色转录",
                       [PYTHON_BIN, 'step3_polish_transcript.py', speakers_file, polished_file]):
            return False
    else:
        print(f"\n  [跳过] 润色已存在: {polished_file}")

    # Step 4: 提取关注清单
    if not os.path.exists(watchlist_file):
        if not run_step("Step 4: 提取关注清单",
                       [PYTHON_BIN, 'step4_extract_watchlist.py', polished_file, watchlist_file]):
            return False
    else:
        print(f"\n  [跳过] 关注清单已存在: {watchlist_file}")

    # Step 5: 提取信号
    if not os.path.exists(signals_file):
        if not run_step("Step 5: 提取投资信号",
                       [PYTHON_BIN, 'step5_extract_signals.py', polished_file, watchlist_file, signals_file]):
            return False
    else:
        print(f"\n  [跳过] 信号已存在: {signals_file}")

    # Step 6: 验证信号
    if not os.path.exists(verified_file):
        if not run_step("Step 6: 验证信号",
                       [PYTHON_BIN, 'step6_verify_signals.py', signals_file, verified_file]):
            return False
    else:
        print(f"\n  [跳过] 验证已存在: {verified_file}")

    # Step 7: 生成投资笔记
    if not os.path.exists(notes_file):
        if not run_step("Step 7: 生成投资笔记",
                       [PYTHON_BIN, 'step7_generate_notes.py', polished_file, verified_file, watchlist_file, notes_file]):
            return False
    else:
        print(f"\n  [跳过] 笔记已存在: {notes_file}")

    print(f"\n{'='*60}")
    print(f"  处理完成!")
    print(f"{'='*60}")
    print(f"  投资笔记: {notes_file}")

    return True


def main():
    if len(sys.argv) < 2:
        print("使用方法: python scripts/process_single.py <podcast_url>")
        print("示例: python scripts/process_single.py https://sv101.fireside.fm/233")
        sys.exit(1)

    url = sys.argv[1]

    if not process_podcast(url):
        print("\n处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
