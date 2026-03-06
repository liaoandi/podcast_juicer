# 播客榨汁机 (Podcast Juicer)

从播客音频中自动提取投资信号、验证真实性、生成结构化投资研究笔记。

## 处理流程

```
音频 → Gemini 转录(含说话人标注) → 提取投资信号 → Google Search 验证 → 生成研究笔记
```

5 步完成，每集约 15 分钟：

| Step | 内容 | 模型 | 耗时 |
|------|------|------|------|
| 0 | 下载音频 + 提取参与者 | gemini-3.1-pro | ~1min |
| 1 | 音频转录（含说话人标注 + 书面化） | gemini-3.1-pro | ~10min |
| 2 | 提取投资信号 | gemini-3.1-pro | ~2min |
| 3 | 验证信号（Google Search + 市场数据） | gemini-3.1-pro | ~3min |
| 4 | 生成投资笔记 | 无 LLM | <1s |

## 快速开始

```bash
# 安装
git clone https://github.com/liaoandi/podcast_juicer.git
cd podcast_juicer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置
cp .env.example .env
# 编辑 .env，填入 GOOGLE_APPLICATION_CREDENTIALS 路径
```

## 使用

```bash
# 单集处理
python scripts/process_utils.py https://sv101.fireside.fm/240

# 批量处理（从 RSS）
python scripts/process_utils.py --rss https://sv101.fireside.fm/rss --limit 10

# 批量处理（从 URL 列表）
python scripts/process_utils.py --file urls.txt --skip-existing

# 强制重跑
python scripts/process_utils.py https://sv101.fireside.fm/240 --force
```

## 输出

```
output/
├── notes/                          # 所有投资笔记（Markdown）
│   ├── sv101_ep240_investment_notes.md
│   └── ...
└── sv101_ep240/                    # 每集的中间数据
    ├── 240.mp3                     # 音频
    ├── 240_transcript_gemini.json  # Gemini 转录
    ├── sv101_ep240_signals.json    # 投资信号
    ├── sv101_ep240_verified_signals.json  # 验证结果
    ├── sv101_ep240_metadata.json   # 元数据
    └── sv101_ep240_participants.json # 参与者信息
```

## 项目结构

```
scripts/
├── gemini_utils.py           # Gemini API 共享基础设施
├── data_utils.py             # Yahoo Finance 数据源
├── process_utils.py          # 主入口（单集/批量处理）
├── step0_download_and_prepare.py  # 下载音频 + 提取参与者
├── step1_transcribe_gemini.py     # Gemini 音频转录
├── step2_extract_signals.py       # 提取投资信号
├── step3_verify_signals.py        # 验证信号
└── step4_generate_notes.py        # 生成投资笔记

config/
├── podcasts.json                  # 播客配置（URL 匹配规则）
└── default_featured_companies.json # 关注公司列表
```

## 配置

环境变量（`.env`）：
```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

添加新播客：编辑 `config/podcasts.json`。

## 依赖

- Python 3.10+
- Google Vertex AI（Gemini 3.1 Pro）
- ffmpeg（音频分割）
- yt-dlp（音频下载）
