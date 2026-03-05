#!/usr/bin/env python3
"""
高级转录脚本 - 支持更强模型和说话人识别

功能：
1. 使用 Whisper large-v3（最强模型）
2. 支持说话人识别（pyannote.audio）
3. 输出带说话人标记的转录

依赖安装：
    pip install openai-whisper pyannote.audio

使用方法：
    python transcribe_advanced.py <audio_file> [model_size] [output_file]

    model_size: base, small, medium, large-v3 (default: medium 或 WHISPER_MODEL)

说明：
    - large-v3: 最准确，但最慢（约 4-5 倍于 base）
    - 说话人识别需要额外的 Hugging Face token（可选）

环境变量：
    WHISPER_MODEL=medium|small|large-v3 (默认 medium)
    WHISPER_DEVICE=cpu|mps|cuda (默认自动选择)
    WHISPER_FP16=true|false (默认 cuda=true 其他=false)
"""

import json
import sys
import os
import torch
import subprocess
from transcript_utils import format_timestamp, match_speakers_to_segments, save_transcript

def preprocess_audio(audio_file):
    """
    预处理音频：转换为 16kHz 单声道 WAV
    这样可以提升 Whisper 和 pyannote 的性能和准确度

    Args:
        audio_file: 原始音频文件路径

    Returns:
        预处理后的 WAV 文件路径
    """
    # 如果已经是处理过的 WAV，直接返回
    if audio_file.endswith('_16k.wav'):
        return audio_file

    base_name = os.path.splitext(audio_file)[0]
    output_file = f"{base_name}_16k.wav"

    # 如果已经存在，直接使用
    if os.path.exists(output_file):
        print(f"✓ 使用已存在的预处理音频: {output_file}")
        return output_file

    print(f"🔄 预处理音频: {audio_file}")
    print(f"   转换为 16kHz 单声道 WAV...")

    try:
        # 使用 ffmpeg 转换
        cmd = [
            'ffmpeg',
            '-i', audio_file,
            '-ar', '16000',  # 采样率 16kHz
            '-ac', '1',       # 单声道
            '-y',             # 覆盖已存在的文件
            output_file
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )

        print(f"✓ 预处理完成: {output_file}")
        return output_file

    except subprocess.CalledProcessError as e:
        print(f"⚠️  音频预处理失败，使用原文件")
        print(f"   错误: {e.stderr.decode()}")
        return audio_file
    except FileNotFoundError:
        print(f"⚠️  未找到 ffmpeg，使用原文件")
        print(f"   安装: brew install ffmpeg (macOS) 或 apt install ffmpeg (Linux)")
        return audio_file

def _select_whisper_device():
    device = os.getenv("WHISPER_DEVICE")
    if device:
        device = device.strip().lower()
        if device == "mps":
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() and torch.backends.mps.is_built():
                return "mps"
            print("⚠️  WHISPER_DEVICE=mps 但当前环境不支持，回退到 CPU")
            return "cpu"
        if device == "cuda":
            if torch.cuda.is_available():
                return "cuda"
            print("⚠️  WHISPER_DEVICE=cuda 但当前环境无 CUDA，回退到 CPU")
            return "cpu"
        if device == "cpu":
            return "cpu"
        print(f"⚠️  WHISPER_DEVICE={device} 无效，回退自动选择")

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() and torch.backends.mps.is_built():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _select_whisper_fp16(device):
    env_val = os.getenv("WHISPER_FP16")
    if env_val is not None:
        return env_val.strip().lower() in ("1", "true", "yes", "y")
    return device == "cuda"


def transcribe_with_whisper(audio_file, model_size=None):
    """
    使用 Whisper 转录音频

    Args:
        audio_file: 音频文件路径
        model_size: 模型大小 (base, small, medium, large, large-v3)

    Returns:
        转录结果（JSON 格式）
    """
    import whisper
    if not model_size:
        model_size = os.getenv("WHISPER_MODEL", "medium")

    device = _select_whisper_device()
    fp16 = _select_whisper_fp16(device)

    print(f"🎙️  加载 Whisper 模型: {model_size}")
    print(f"   设备: {device}, fp16: {fp16}")
    print(f"   注意：large-v3 模型下载较大（约 3GB），首次使用需要时间")

    try:
        model = whisper.load_model(model_size, device=device)
    except Exception as e:
        print(f"❌ 加载模型失败: {e}")
        print(f"   尝试使用 base 模型...")
        model = whisper.load_model("base", device=device)
        model_size = "base"

    print(f"\n🔊 转录音频: {audio_file}")
    print(f"   使用模型: {model_size}")
    print(f"   预计时间: {'10-15 分钟' if model_size == 'large-v3' else '2-3 分钟'}")

    word_timestamps_env = os.getenv("WHISPER_WORD_TIMESTAMPS")
    if word_timestamps_env is not None:
        word_timestamps = word_timestamps_env.strip().lower() in ("1", "true", "yes", "y")
    else:
        # MPS 不支持 float64，word_timestamps 会触发 dtw float64
        word_timestamps = device != "mps"

    result = model.transcribe(
        audio_file,
        language=os.getenv("WHISPER_LANGUAGE", "zh"),
        verbose=True,
        word_timestamps=word_timestamps,  # 获取词级时间戳（用于后续说话人分离）
        fp16=fp16
    )

    return result

def _infer_speaker_count(audio_file):
    """
    尝试从同目录的 metadata/participants 文件推断说话人数
    规则：hosts + guests 数量
    """
    import glob
    import json
    audio_dir = os.path.dirname(os.path.abspath(audio_file))
    # 优先 metadata，其次 participants
    candidates = []
    candidates += glob.glob(os.path.join(audio_dir, "*_metadata.json"))
    candidates += glob.glob(os.path.join(audio_dir, "*_participants.json"))
    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            hosts = data.get("hosts", data.get("host", [])) or []
            if isinstance(hosts, str):
                hosts = [hosts]
            guests = data.get("guests", []) or []
            count = len(hosts) + len(guests)
            if count > 0:
                return count, path
        except Exception:
            continue
    return None, None

def try_speaker_diarization(audio_file):
    """
    尝试使用 pyannote.audio 进行说话人分离

    需要 Hugging Face token，从这里获取：
    https://huggingface.co/settings/tokens

    并接受模型许可：
    https://huggingface.co/pyannote/speaker-diarization

    Returns:
        说话人时间轴，或 None（如果不可用）
    """
    try:
        # 修复 torchaudio 在部分环境中缺失的 API（Python 3.14/某些构建）
        # speechbrain/pyannote 依赖 list_audio_backends、AudioMetaData、info
        import torchaudio
        if not hasattr(torchaudio, "list_audio_backends"):
            def _list_audio_backends():
                return ["soundfile"]
            torchaudio.list_audio_backends = _list_audio_backends
        if not hasattr(torchaudio, "set_audio_backend"):
            def _set_audio_backend(_name):
                return None
            torchaudio.set_audio_backend = _set_audio_backend
        if not hasattr(torchaudio, "AudioMetaData"):
            from dataclasses import dataclass
            @dataclass
            class AudioMetaData:
                sample_rate: int
                num_frames: int
                num_channels: int
                bits_per_sample: int
                encoding: str
            torchaudio.AudioMetaData = AudioMetaData
        if not hasattr(torchaudio, "info"):
            try:
                import soundfile as sf
            except Exception:
                sf = None

            def _info(path, backend=None):
                if sf is None:
                    raise RuntimeError("soundfile 不可用，无法提供 torchaudio.info")
                info = sf.info(path)
                # 从 subtype 提取位深（若无法提取则置 0）
                bits = 0
                try:
                    import re
                    m = re.search(r"(\d+)", info.subtype or "")
                    if m:
                        bits = int(m.group(1))
                except Exception:
                    bits = 0
                return torchaudio.AudioMetaData(
                    sample_rate=info.samplerate,
                    num_frames=info.frames,
                    num_channels=info.channels,
                    bits_per_sample=bits,
                    encoding=info.subtype or ""
                )

            torchaudio.info = _info

        # Monkey-patch torchaudio.load to use soundfile直接
        original_torchaudio_load = torchaudio.load if hasattr(torchaudio, "load") else None
        def _load(filepath, *args, backend=None, **kwargs):
            try:
                import soundfile as sf
                import torch
                data, sample_rate = sf.read(filepath, always_2d=True)
                waveform = torch.from_numpy(data.T).float()
                return waveform, sample_rate
            except Exception:
                if original_torchaudio_load:
                    return original_torchaudio_load(filepath, *args, backend=backend, **kwargs)
                raise
        torchaudio.load = _load

        from pyannote.audio import Pipeline

        # 检查环境变量中的 token
        hf_token = os.environ.get('HUGGINGFACE_TOKEN')

        # 也尝试从 .env 读取（项目根目录）
        if not hf_token:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env_file = os.path.join(project_root, '.env')
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('HUGGINGFACE_TOKEN='):
                            hf_token = line.split('=', 1)[1].strip()
                            break

        if not hf_token:
            print("\n⚠️  未找到 HUGGINGFACE_TOKEN 环境变量")
            print("   说话人识别需要 Hugging Face token")
            print("   获取方式：https://huggingface.co/settings/tokens")
            print("   使用: export HUGGINGFACE_TOKEN=your_token")
            print("   跳过说话人识别...\n")
            return None

        print("\n👥 加载说话人分离模型...")

        # 修复 PyTorch weights_only 安全限制（pyannote 模型需要）
        import torch
        original_torch_load = torch.load

        def patched_load(*args, **kwargs):
            kwargs["weights_only"] = False
            return original_torch_load(*args, **kwargs)

        # 兼容 huggingface_hub 新旧参数差异
        try:
            import inspect
            import huggingface_hub
            from huggingface_hub import hf_hub_download as _hf_hub_download

            if "use_auth_token" not in inspect.signature(_hf_hub_download).parameters:
                def _patched_hf_hub_download(*args, use_auth_token=None, token=None, **kwargs):
                    if token is None and use_auth_token is not None:
                        token = use_auth_token
                    return _hf_hub_download(*args, token=token, **kwargs)
                huggingface_hub.hf_hub_download = _patched_hf_hub_download
                try:
                    import pyannote.audio.core.pipeline as _pa_pipeline
                    _pa_pipeline.hf_hub_download = _patched_hf_hub_download
                except Exception:
                    pass
        except Exception:
            pass

        pipeline = None
        try:
            torch.load = patched_load
            # 兼容新版 huggingface_hub: use token= 而不是 use_auth_token=
            try:
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=hf_token
                )
            except TypeError:
                pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=hf_token
                )
        finally:
            # 确保恢复原始 torch.load
            torch.load = original_torch_load

        # 尝试使用 GPU / MPS 加速
        device = os.environ.get("PYANNOTE_DEVICE")
        if not device:
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() and torch.backends.mps.is_built():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
        device_used = None
        if device:
            try:
                pipeline.to(torch.device(device))
                print(f"   使用设备: {device}")
                device_used = device
            except Exception as e:
                print(f"   ⚠️ 无法切换到 {device}，继续使用 CPU: {e}")
                device_used = None

        # 可选：降低 batch size / 增大 step，减少内存占用与崩溃概率
        try:
            seg_bs = os.environ.get("PYANNOTE_SEG_BATCH_SIZE")
            emb_bs = os.environ.get("PYANNOTE_EMB_BATCH_SIZE")
            seg_step = os.environ.get("PYANNOTE_SEG_STEP")

            # 默认在 CPU 上适度降低 batch size
            if device_used in (None, "cpu"):
                if seg_bs is None:
                    seg_bs = "8"
                if emb_bs is None:
                    emb_bs = "8"

            if seg_bs is not None:
                pipeline.segmentation_batch_size = int(seg_bs)
                print(f"   segmentation_batch_size={pipeline.segmentation_batch_size}")
            if emb_bs is not None:
                pipeline.embedding_batch_size = int(emb_bs)
                print(f"   embedding_batch_size={pipeline.embedding_batch_size}")
            if seg_step is not None:
                pipeline.segmentation_step = float(seg_step)
                print(f"   segmentation_step={pipeline.segmentation_step}")
        except Exception as e:
            print(f"   ⚠️ 无法应用 batch/step 参数: {e}")

        # 说话人数约束（可选）
        # 1) 环境变量覆盖
        num_speakers_env = os.environ.get("PYANNOTE_NUM_SPEAKERS")
        min_speakers_env = os.environ.get("PYANNOTE_MIN_SPEAKERS")
        max_speakers_env = os.environ.get("PYANNOTE_MAX_SPEAKERS")

        num_speakers = int(num_speakers_env) if num_speakers_env else None
        min_speakers = int(min_speakers_env) if min_speakers_env else None
        max_speakers = int(max_speakers_env) if max_speakers_env else None

        if num_speakers is None and min_speakers is None and max_speakers is None:
            inferred, src = _infer_speaker_count(audio_file)
            if inferred:
                num_speakers = inferred
                print(f"   说话人数量推断: {num_speakers}（来自 {os.path.basename(src)}）")

        print("   分析说话人...")
        kwargs = {}
        if num_speakers is not None:
            kwargs["num_speakers"] = num_speakers
        if min_speakers is not None:
            kwargs["min_speakers"] = min_speakers
        if max_speakers is not None:
            kwargs["max_speakers"] = max_speakers

        try:
            result = pipeline(audio_file, **kwargs) if kwargs else pipeline(audio_file)
        except Exception as e:
            # 如果 GPU/MPS 失败，自动回退到 CPU 重试一次
            if device_used in ("mps", "cuda"):
                print(f"   ⚠️ {device_used} 推理失败，切换 CPU 重试: {e}")
                try:
                    pipeline.to(torch.device("cpu"))
                    result = pipeline(audio_file, **kwargs) if kwargs else pipeline(audio_file)
                except Exception:
                    raise
            else:
                raise

        # pyannote 4.0 返回 DiarizeOutput 对象，需要访问 .output 属性
        diarization = result.output if hasattr(result, 'output') else result

        # 转换为时间轴格式
        speaker_timeline = []
        for segment, track, label in diarization.itertracks(yield_label=True):
            speaker_timeline.append({
                'start': float(segment.start),
                'end': float(segment.end),
                'speaker': label
            })

        print(f"   识别到 {len(set([s['speaker'] for s in speaker_timeline]))} 位说话人")
        return speaker_timeline

    except ImportError as e:
        print("\n⚠️  pyannote.audio 未安装")
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        print("   安装: pip install pyannote.audio")
        print("   跳过说话人识别...\n")
        return None
    except Exception as e:
        print(f"\n⚠️  说话人识别失败: {e}")
        import traceback
        traceback.print_exc()
        print("   继续使用基础转录...\n")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python transcribe_advanced.py <audio_file> [model_size] [output_file]")
        print("模型: base (快), large-v3 (准确)")
        sys.exit(1)

    audio_file = sys.argv[1]
    model_size = os.getenv("WHISPER_MODEL", "medium")
    output_file = None

    if len(sys.argv) > 2:
        arg2 = sys.argv[2]
        # 如果第二个参数看起来像输出文件路径，则作为 output_file
        if arg2.endswith(".json") or "/" in arg2:
            output_file = arg2
        else:
            model_size = arg2

    if len(sys.argv) > 3:
        arg3 = sys.argv[3]
        if output_file is None and (arg3.endswith(".json") or "/" in arg3):
            output_file = arg3

    # 预处理音频（转换为 16kHz 单声道 WAV）
    processed_audio = preprocess_audio(audio_file)

    # 转录
    result = transcribe_with_whisper(processed_audio, model_size)

    # 先保存基础转录，避免说话人识别失败导致无输出
    if not output_file:
        base_name = os.path.splitext(audio_file)[0]
        output_file = f"{base_name}_transcript_advanced.json"
    save_transcript(result, output_file, speaker_timeline=None)

    # 说话人识别（可选）
    speaker_timeline = try_speaker_diarization(processed_audio)

    # 如有说话人结果，覆盖写入
    if speaker_timeline:
        save_transcript(result, output_file, speaker_timeline)
