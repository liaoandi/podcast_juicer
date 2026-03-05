# 播客榨汁机 (Podcast Juicer)

从投资播客中榨取投资信号的 Agent，是我自己平常会手动做的事情，这次试试用 Agent 来实现。

## 功能

从播客音频中提取投资信号，验证信息真实性，生成结构化的投资研究笔记。

处理流程：
```
音频 → 转录 → 说话人识别 → 文本润色 → 提取关注列表 → 提取投资信号 → 验证信息 → 生成研究笔记
```

## 支持的播客

| 播客 | 语言 | 类型 |
|------|------|------|
| 硅谷101 | 中文 | 科技投资 |
| Acquired | 英文 | 科技投资 |
| All-In Podcast | 英文 | 科技投资 |
| Invest Like the Best | 英文 | 投资 |
| Bankless | 英文 | 加密货币 |

可在 `config/podcasts.json` 中添加更多播客。

## 安装

```bash
git clone https://github.com/liaoandi/podcast-juicer.git
cd podcast-juicer

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 配置

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入 API 密钥：
```
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment
```

## 使用

### 单集处理
```bash
python scripts/process.py <podcast_url>
```

示例：
```bash
python scripts/process.py https://sv101.fireside.fm/233
python scripts/process.py https://www.acquired.fm/episodes/nvidia
python scripts/process.py https://www.youtube.com/watch?v=xxxxx
```

### 批量处理
```bash
# 从 RSS 批量处理
python scripts/process.py --rss https://sv101.fireside.fm/rss --limit 10

# 从 URL 列表批量处理
python scripts/process.py --file filtered_urls.txt --skip-existing
```

### 筛选播客
```bash
# 列出 RSS 中的播客
python scripts/podcasts.py list https://sv101.fireside.fm/rss

# 按规则筛选
python scripts/podcasts.py filter podcast_list.json --after 2025-01-01 --keywords "AI,芯片"

# LLM 智能筛选
python scripts/podcasts.py filter-smart podcast_list.json "AI技术投资"

# 处理筛选结果
python scripts/process.py --file smart_filtered.txt
```

输出保存在 `output/{podcast}_ep{episode}/` 目录。

## 项目结构

```
├── scripts/
│   ├── process.py              # 处理播客（单集 + 批量）
│   ├── podcasts.py             # 播客管理（list + filter）
│   └── step0 ~ step7           # 各处理步骤
├── config/
│   ├── podcasts.json           # 播客配置（URL 模式、主持人等）
│   ├── default_watchlist.json  # 默认关注公司
│   └── participants.json       # 已知嘉宾
├── output/                     # 输出目录（gitignore）
└── .env.example                # 环境变量模板
```

## 添加新播客

编辑 `config/podcasts.json`：

```json
{
  "your_podcast": {
    "name": "播客名称",
    "url_patterns": ["your-podcast\\.com/episodes?/(\\d+)"],
    "base_url": "https://your-podcast.com",
    "hosts": ["主持人1", "主持人2"],
    "language": "en",
    "category": "investment"
  }
}
```

## 依赖

- Python 3.10+
- Azure OpenAI API 或 Google Gemini API
- OpenAI Whisper
