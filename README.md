# 播客榨汁机 (Podcast Juicer)

自动化播客转投资研究笔记的 AI 处理管线。

## 功能

从播客音频中自动提取投资信号，验证信息真实性，生成结构化的投资研究笔记。

处理流程：
```
音频 → 转录 → 说话人识别 → 文本润色 → 提取关注列表 → 提取投资信号 → 验证信息 → 生成研究笔记
```

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

```bash
python3 scripts/process_single.py <podcast_url>
```

示例：
```bash
python3 scripts/process_single.py https://sv101.fireside.fm/233
```

输出保存在 `output/sv101_ep233/` 目录。

## 项目结构

```
├── scripts/
│   ├── process_single.py       # 主入口：处理单集播客
│   └── step0 ~ step7           # 各处理步骤
├── config/
│   ├── default_watchlist.json  # 默认关注公司
│   └── participants.json       # 已知嘉宾
├── output/                     # 输出目录（gitignore）
└── .env.example                # 环境变量模板
```

## 依赖

- Python 3.10+
- Azure OpenAI API 或 Google Gemini API
- OpenAI Whisper
