# 播客榨汁机 Podcast Juicer

[中文](#中文) | [English](#english)

---

## 中文

从播客音频中自动提取投资信号、验证真实性、生成结构化投资研究笔记。

### 设计动机

在了解 AI 前沿动态的过程中，发现科技/投资播客里蕴含大量可行动的投资信号 -- 嘉宾在对话中透露的判断和逻辑链，往往是研报里不会写的一手信息。但这些信号散落在几十分钟的对话里，手动提取和验证成本很高。

这个项目把整个流程自动化，产出结构化的投资笔记。两个关键设计选择：

- **验证环节不可省略。** LLM 提取的信号可能存在幻觉或过度解读。通过 Google Search 交叉验证，给每条信号标注"已验证"或"与事实矛盾"，过滤掉不可靠的信息。
- **拆步骤而不是端到端。** 每步独立存储中间结果，支持断点续跑和单步重跑。转录是最耗时的环节，一旦完成不需要重复；后续信号提取和验证可以反复迭代。

### 产出示例

以下为一期播客投资笔记的节选，硅谷101 E212「AI数据中心的万亿大基建时代：美国GDP增长全靠它」，2025年10月30日发布，嘉宾为徐熠兴、王辰晟。

```markdown
## 2. GE Vernova ($GEV) vs xAI

> 为了绕开漫长的电网审批实现算力快速上线，xAI已扫清美国超70%的燃气涡轮发电机库存。同时GE Vernova的大型发电机订单已排至2028年，显示短期过渡性备用电源设备面临极端的供需失衡，具备强定价权。

置信度: HIGH | 新颖度: HIGH | 可行动性: HIGH

**验证**: 已验证 (2026-03-10)

**影响路径**

- 从AI算力需求到独立发电的传导。AI数据中心建设速度远超传统电网扩容周期，迫使科技巨头转向采购燃气轮机等分布式电源进行物理脱网供电，直接引爆了发电设备需求。
- 对产业链的具体影响。燃气轮机制造商迎来历史性订单潮，产能严重受限导致交货期大幅延长。供需极端失衡使得设备供应商获得了极强的议价能力，新订单利润率显著扩张。
- 对投资者的实际意义。电力基础设施和备用电源设备已成为AI算力扩张的硬瓶颈，具备燃气轮机产能和电网设备制造能力的标的在未来3-5年内具有极高的业绩确定性。

**来源**

- [Electrek](https://electrek.co/2026/03/03/elon-musks-xai-is-undoing-teslas-climate-work-all-in-the-name-of-ai-slop/): 马斯克的xAI绕过漫长的电网审批，在田纳西州和密西西比州部署了至少62台移动甲烷燃气轮机，总发电容量近1GW。
- [RMI](https://rmi.org/gas-turbine-supply-constraints-threaten-grid-reliability/): 三大制造商占据75%以上在建项目份额，其中GE Vernova宣布新涡轮机最早要到2028年底才能交货。
- [Utility Dive](https://www.utilitydive.com/news/ge-vernova-gas-turbine-backlog-2029-electrification-wind/735231/): GE Vernova预计到2025年底燃气轮机积压订单将达80GW，新订单定价远高于当前订单。

**原文摘录** [00:31:04 - 00:34:18] · [跳转音频](https://sv101.fireside.fm/220?t=1864)

> **王辰晟**: GE Vernova 过去十年增长非常平缓，峰值时一年大概70几台，每台30到50兆瓦。做个对比，飞机引擎一年近4000台下线，而涡轮发电机市场最大的 GE Vernova 只有小100台，一个数量级的差别。
>
> 比方说马斯克需要6个月就上线，而并入电网需要两年的审批时间，这一年半的 gap 只能使用短期的涡轮发电机。xAI 根据公开信息，横扫了美国将近70%以上的燃气涡轮发电机库存，用来给孟菲斯两个大型 data center 供电。
>
> GE 现在的订单已经排到2028年了。
```

每条信号笔记均包含以下结构化字段：

| 字段 | 说明 |
|------|------|
| 信号主张 | 一段话概括核心投资观点 |
| 置信度 / 新颖度 / 可行动性 | HIGH / MEDIUM / LOW 三级评分 |
| 验证状态 | 通过 Google Search 和市场数据交叉验证，标注已验证或与事实矛盾 |
| 影响路径 | 从技术/产品到产业链再到投资者的三层传导分析 |
| 来源 | 验证过程中引用的外部信息源，含链接和摘要 |
| 原文摘录 | 播客中与该信号相关的对话片段，含时间戳和音频跳转链接 |

批量处理后会生成 `quality_check_report.md`，汇总每集的转录质量、信号数、验证结果：

| 状态 | 剧集 | 信号 | 验证 | 说明 |
|------|------|------|------|------|
| 正常 | EP233 | 6 | verified:6 | 正常 |
| 正常 | EP234 | 3 | verified:3 | 正常 |
| 正常 | EP235 | 4 | verified:2, contradicted:2 | 正常 |
| 正常 | EP236 | 4 | verified:3, contradicted:1 | 正常 |
| 警告 | EP237 | 0 | - | 内容非投资主题，非技术故障 |
| 正常 | EP238 | 4 | verified:4 | 正常 |
| 警告 | EP239 | 2 | verified:2 | 内容偏观察，信号少属正常 |
| 正常 | EP240 | 4 | verified:3, contradicted:1 | 正常 |

### 设计迭代

这个项目从 7 步 pipeline 迭代到最终的 5 步，中间踩了不少坑：

**V1: 7 步流程 -- Whisper + GPT-4**

初版用 Whisper 转录 + Azure OpenAI GPT-4 做后续处理，共 7 步：转录 → 说话人识别 → 文本润色 → 提取关注公司 → 提取信号 → 验证 → 生成笔记。问题很多：
- Whisper 转录质量差，英文术语和人名错误多，还需要额外的说话人识别和文本润色步骤来补救
- 整个流程一集要跑很久，其中润色步骤即使并发优化后仍然是瓶颈
- 嘉宾画像步骤实际产出价值有限，白耗 4 次 Pro 调用
- 关注公司列表需要手动维护 config 文件，新公司出现时会漏提

**V2: 6 步流程 -- Gemini 音频直接转录**

用 Gemini 3.1 Pro 替换 Whisper，一步完成转录 + 说话人标注 + 书面化，砍掉了说话人识别和文本润色两个步骤。质量反而更好。

**V3: 5 步流程 -- 最终版**

进一步精简：
- 砍掉嘉宾画像步骤，价值不足以 justify 成本
- 砍掉独立的公司提取步骤，信号提取时 LLM 自然会识别相关公司
- 最后连 config 目录都删了 -- 预设的关注公司列表和播客配置文件都不需要，LLM 自己识别效果更好

**核心经验**：Gemini 这类多模态模型比想象中强大得多。最初按传统思路把 pipeline 拆成很多小步骤，本质上是在用工程手段弥补模型能力不足。但当模型足够强时，一步就能完成原来三四步的工作，而且质量更好 -- 因为模型在单次调用中能利用完整上下文做全局判断，拆开反而丢失了信息。最终 pipeline 从 7 步收敛到 5 步，代码量砍掉一半，速度快了一倍，效果反而更好。

### 处理流程

```
音频 → Gemini 转录 + 说话人标注 → 提取投资信号 → Google Search 验证 → 生成研究笔记
```

| Step | 内容 | 模型 |
|------|------|------|
| 0 | 下载音频 + 提取参与者 | gemini-3.1-pro |
| 1 | 音频转录，含说话人标注和书面化 | gemini-3.1-pro |
| 2 | 提取投资信号 | gemini-3.1-pro |
| 3 | 验证信号，Google Search + 市场数据 | gemini-3.1-pro |
| 4 | 生成投资笔记 | 无 LLM |

### 快速开始

```bash
git clone https://github.com/liaoandi/podcast_juicer_sv101.git
cd podcast_juicer_sv101
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# 公共密钥统一放在 ~/.config/api-keys.env，并由 shell 自动加载
# 如需 override，再单独传环境变量，不要新建项目级 .env
```

### 使用

```bash
# 单集处理
python scripts/process_utils.py https://sv101.fireside.fm/240

# 批量处理，从 RSS
python scripts/process_utils.py --rss https://sv101.fireside.fm/rss --limit 10

# 批量处理，从 URL 列表
python scripts/process_utils.py --file urls.txt --skip-existing

# 强制重跑
python scripts/process_utils.py https://sv101.fireside.fm/240 --force
```

### 自动化（每周定时运行）

通过 OpenClaw cron 每周日 21:00（上海时间）自动处理最新剧集：

```bash
# 注册在 ~/Desktop/projects/agent_toolkit/openclaw/scripts/weekly_invest_sync.py
python weekly_invest_sync.py --only sv101
```

每次最多处理 3 集新剧集（`--skip-existing` 跳过已完成的），单集超时 30 分钟。

### 项目结构

```
scripts/
├── gemini_utils.py                  # Gemini API 共享基础设施
├── data_utils.py                    # Yahoo Finance 数据源
├── process_utils.py                 # 主入口，单集/批量处理
├── step0_download_and_prepare.py    # 下载音频 + 提取参与者
├── step1_transcribe_gemini.py       # Gemini 音频转录
├── step2_extract_signals.py         # 提取投资信号
├── step3_verify_signals.py          # 验证信号
└── step4_generate_notes.py          # 生成投资笔记

output/
├── notes/                           # 所有投资笔记
└── sv101_ep240/                     # 每集的中间数据
    ├── 240.mp3                      # 音频
    ├── 240_transcript_gemini.json   # Gemini 转录
    ├── sv101_ep240_signals.json     # 投资信号
    ├── sv101_ep240_verified_signals.json  # 验证结果
    └── sv101_ep240_metadata.json    # 元数据
```

### 配置

公共密钥统一存放在 `~/.config/api-keys.env`：
```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GOOGLE_CLOUD_PROJECT=your-gcp-project
```

### 依赖

- Python 3.10+
- Google Vertex AI, Gemini 3.1 Pro
- ffmpeg
- yt-dlp

---

## English

Automatically extract investment signals from podcast audio, verify their accuracy, and generate structured investment research notes.

### Why This Project

While keeping up with AI developments, I noticed that cutting-edge tech/investment podcasts contain a wealth of actionable investment signals -- guests share judgments and reasoning chains in conversation that would never appear in formal research reports. But these signals are scattered across hours of dialogue, making manual extraction and verification costly.

This project automates the entire workflow, producing structured investment research notes. Two key design choices:

- **Verification is non-negotiable.** LLM-extracted signals may contain hallucinations or over-interpretations. Google Search cross-verification labels each signal as "verified" or "contradicted by evidence," filtering out unreliable information.
- **Stepped pipeline over end-to-end.** Each step stores intermediate results independently, supporting checkpoint resumption and single-step reruns. Transcription is the most time-consuming step; once complete, it never needs to repeat. Signal extraction and verification can be iterated independently.

### Sample Output

Below is an excerpt from a real investment note, SinoVision 101 E212 "The Trillion-Dollar AI Datacenter Buildout Era: US GDP Growth Depends on It," published October 30, 2025, featuring guests Xu Yixing and Wang Chensheng.

```markdown
## 2. GE Vernova ($GEV) vs xAI

> To bypass lengthy grid permits and bring compute online fast, xAI has swept over 70% of
> US gas turbine generator inventory. GE Vernova's large turbine orders are booked through
> 2028, indicating extreme supply-demand imbalance in transitional backup power equipment
> with strong pricing power.

Confidence: HIGH | Novelty: HIGH | Actionability: HIGH

**Verification**: Verified (2026-03-10)

**Impact Path**

- AI datacenter build speed far exceeds grid expansion cycles, forcing tech giants to procure
  gas turbines for off-grid power, directly igniting power equipment demand.
- Turbine manufacturers face historic order backlogs with severely constrained capacity,
  granting extreme pricing power on new orders.
- Power infrastructure has become a hard bottleneck for AI compute expansion; companies with
  gas turbine capacity have high earnings visibility for the next 3-5 years.

**Sources**

- [Electrek]: xAI deployed 62+ mobile methane gas turbines in Tennessee and Mississippi, ~1GW total.
- [RMI]: Top 3 manufacturers hold 75%+ of projects; GE Vernova's earliest new delivery is late 2028.
- [Utility Dive]: GE Vernova backlog expected to reach 80GW by end of 2025; new order pricing far above current.

**Original Transcript** [00:31:04 - 00:34:18] · [Jump to audio](https://sv101.fireside.fm/220?t=1864)
```

_(Output is in the original podcast language. See Chinese section above for the full unabridged excerpt.)_

Each signal note contains these structured fields:

| Field | Description |
|-------|-------------|
| Signal claim | One-paragraph summary of the core investment thesis |
| Confidence / Novelty / Actionability | Three-tier rating: HIGH / MEDIUM / LOW |
| Verification status | Cross-verified via Google Search and market data; marked as verified or contradicted |
| Impact path | Three-layer analysis: technology/product → industry chain → investor implications |
| Sources | External references cited during verification, with links and summaries |
| Original transcript | Relevant podcast dialogue excerpts, with timestamps and audio jump links |

### Design Iterations

The project evolved from a 7-step pipeline to the final 5-step version, with several hard-learned lessons along the way:

**V1: 7-step pipeline -- Whisper + GPT-4**

The initial version used Whisper for transcription + Azure OpenAI GPT-4 for downstream processing, with 7 steps: transcription → speaker identification → text polishing → company extraction → signal extraction → verification → note generation. Problems:
- Whisper transcription quality was poor with frequent errors on English terms and proper names, requiring separate speaker identification and text polishing steps as band-aids
- The full pipeline was slow, with the polishing step remaining a bottleneck even after parallelization
- Guest profiling step produced limited value while consuming 4 Pro API calls per episode
- Company watchlist required manually maintaining a config file; new companies were missed

**V2: 6-step pipeline -- Gemini direct audio transcription**

Replaced Whisper with Gemini 3.1 Pro, which handles transcription + speaker labeling + literary formatting in a single step. This eliminated the speaker identification and text polishing steps entirely, with better quality.

**V3: 5-step pipeline -- final**

Further simplification:
- Removed guest profiling: value didn't justify cost
- Removed standalone company extraction: the signal extraction step naturally identifies relevant companies
- Eventually deleted the entire config directory -- the preset company watchlist and podcast config files were unnecessary; the LLM identifies everything better on its own

**Key lesson**: Multimodal models like Gemini are far more capable than initially assumed. The original approach of splitting the pipeline into many small steps was essentially using engineering complexity to compensate for model limitations. But when the model is strong enough, one step replaces three or four -- and produces better results, because a single call can leverage full context for global reasoning, while splitting it up loses information. The final pipeline converged from 7 steps to 5, cut codebase size in half, doubled processing speed, and improved output quality.

### Pipeline

```
Audio → Gemini transcription + speaker labels → Extract investment signals → Google Search verification → Generate research notes
```

| Step | Description | Model |
|------|-------------|-------|
| 0 | Download audio + extract participants | gemini-3.1-pro |
| 1 | Audio transcription with speaker labels and literary formatting | gemini-3.1-pro |
| 2 | Extract investment signals | gemini-3.1-pro |
| 3 | Verify signals via Google Search + market data | gemini-3.1-pro |
| 4 | Generate investment notes | No LLM |

### Quick Start

```bash
git clone https://github.com/liaoandi/podcast_juicer_sv101.git
cd podcast_juicer_sv101
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Store shared credentials in ~/.config/api-keys.env and let the shell load them
# Do not create a project-level .env for common keys
```

### Usage

```bash
# Process a single episode
python scripts/process_utils.py https://sv101.fireside.fm/240

# Batch process from RSS
python scripts/process_utils.py --rss https://sv101.fireside.fm/rss --limit 10

# Batch process from URL list
python scripts/process_utils.py --file urls.txt --skip-existing

# Force reprocess
python scripts/process_utils.py https://sv101.fireside.fm/240 --force
```

### Automation (Weekly)

Runs automatically every Sunday at 21:00 Shanghai time via OpenClaw cron:

```bash
# Registered in ~/Desktop/projects/agent_toolkit/openclaw/scripts/weekly_invest_sync.py
python weekly_invest_sync.py --only sv101
```

Processes up to 3 new episodes per run, skipping already-completed ones. 30-minute timeout per episode.

### Project Structure

```
scripts/
├── gemini_utils.py                  # Gemini API shared infrastructure
├── data_utils.py                    # Yahoo Finance data source
├── process_utils.py                 # Main entry, single/batch processing
├── step0_download_and_prepare.py    # Download audio + extract participants
├── step1_transcribe_gemini.py       # Gemini audio transcription
├── step2_extract_signals.py         # Extract investment signals
├── step3_verify_signals.py          # Verify signals
└── step4_generate_notes.py          # Generate investment notes

output/
├── notes/                           # All investment notes
└── sv101_ep240/                     # Intermediate data per episode
    ├── 240.mp3                      # Audio
    ├── 240_transcript_gemini.json   # Gemini transcript
    ├── sv101_ep240_signals.json     # Investment signals
    ├── sv101_ep240_verified_signals.json  # Verification results
    └── sv101_ep240_metadata.json    # Metadata
```

### Configuration

Shared credentials live in `~/.config/api-keys.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GOOGLE_CLOUD_PROJECT=your-gcp-project
```

### Dependencies

- Python 3.10+
- Google Vertex AI, Gemini 3.1 Pro
- ffmpeg
- yt-dlp
