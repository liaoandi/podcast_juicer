#!/bin/bash
# Phase 3: 有 MP3 从 step1 重跑 (断点续传)
# 每个 step 完成后写文件，重跑自动跳过已完成的 step
# 用法: bash run_phase3.sh [从第几集开始，如 ep186]

set -euo pipefail

SCRIPTS="/Users/antonio/Desktop/podcast_juicer/scripts"
OUTPUT="/Users/antonio/Desktop/podcast_juicer/output"
NOTES_DIR="$OUTPUT/notes"
PYTHON="/Users/antonio/Desktop/podcast_juicer/venv/bin/python3"
PROGRESS_MD="/Users/antonio/Desktop/podcast_juicer/batch_progress.md"

EPISODES=(184 185 186 187 188 189 191 194 196 197)

# 支持从指定 ep 开始（断点续传）
START_EP="${1:-}"
SKIP=true
if [ -z "$START_EP" ]; then
    SKIP=false
fi

TOTAL=${#EPISODES[@]}
SUCCESS=0
FAIL=0
IDX=0

for ep in "${EPISODES[@]}"; do
    IDX=$((IDX + 1))

    # 跳过直到指定 ep
    if $SKIP; then
        if [ "ep${ep}" = "$START_EP" ] || [ "${ep}" = "$START_EP" ]; then
            SKIP=false
        else
            echo "[$IDX/$TOTAL] ep${ep}: 跳过 (未到起始集)"
            continue
        fi
    fi

    dir="$OUTPUT/sv101_ep${ep}"
    mp3="$dir/${ep}.mp3"
    parti="$dir/sv101_ep${ep}_participants.json"
    transcript="$dir/${ep}_transcript_gemini.json"
    signals="$dir/sv101_ep${ep}_signals.json"
    verified="$dir/sv101_ep${ep}_verified_signals.json"
    notes="$NOTES_DIR/sv101_ep${ep}_investment_notes.md"

    echo ""
    echo "============================================================"
    echo "[$IDX/$TOTAL] ep${ep}"
    echo "============================================================"

    if [ ! -f "$mp3" ]; then
        echo "  SKIP: MP3 不存在"
        continue
    fi

    # Step 1: 转录
    if [ -f "$transcript" ]; then
        echo "  Step 1: 跳过 (转录已存在)"
    else
        echo "  Step 1: 转录中..."
        if $PYTHON "$SCRIPTS/step1_transcribe_gemini.py" "$mp3" "$parti" "$transcript" 2>&1; then
            echo "  Step 1: done"
        else
            echo "  Step 1: FAILED"
            sed -i '' "s/- \[ \] ep${ep}$/- [ ] ep${ep} (step1 FAILED)/" "$PROGRESS_MD"
            FAIL=$((FAIL + 1))
            continue
        fi
    fi

    # Step 2: 信号提取
    if [ -f "$signals" ]; then
        echo "  Step 2: 跳过 (信号已存在)"
    else
        echo "  Step 2: 提取信号..."
        if $PYTHON "$SCRIPTS/step2_extract_signals.py" "$transcript" "$signals" 2>&1; then
            echo "  Step 2: done"
        else
            echo "  Step 2: FAILED"
            sed -i '' "s/- \[ \] ep${ep}$/- [ ] ep${ep} (step2 FAILED)/" "$PROGRESS_MD"
            FAIL=$((FAIL + 1))
            continue
        fi
    fi

    # Step 3: 验证
    if [ -f "$verified" ]; then
        echo "  Step 3: 跳过 (验证已存在)"
    else
        echo "  Step 3: 验证信号..."
        if $PYTHON "$SCRIPTS/step3_verify_signals.py" "$signals" "$verified" 2>&1; then
            echo "  Step 3: done"
        else
            echo "  Step 3: FAILED"
            sed -i '' "s/- \[ \] ep${ep}$/- [ ] ep${ep} (step3 FAILED)/" "$PROGRESS_MD"
            FAIL=$((FAIL + 1))
            continue
        fi
    fi

    # Step 4: 笔记
    if [ -f "$notes" ]; then
        echo "  Step 4: 跳过 (笔记已存在)"
    else
        echo "  Step 4: 生成笔记..."
        if $PYTHON "$SCRIPTS/step4_generate_notes.py" "$transcript" "$signals" "$verified" "$notes" 2>&1; then
            echo "  Step 4: done"
        else
            echo "  Step 4: FAILED"
            sed -i '' "s/- \[ \] ep${ep}$/- [ ] ep${ep} (step4 FAILED)/" "$PROGRESS_MD"
            FAIL=$((FAIL + 1))
            continue
        fi
    fi

    # 更新进度
    sig_count=$($PYTHON -c "import json; print(len(json.load(open('$signals'))['signals']))" 2>/dev/null || echo "?")
    sed -i '' "s/- \[ \] ep${ep}$/- [x] ep${ep} (done, ${sig_count} signals)/" "$PROGRESS_MD"
    SUCCESS=$((SUCCESS + 1))
    echo "  ep${ep}: COMPLETE ($sig_count signals)"
done

echo ""
echo "============================================================"
echo "Phase 3 结果: $SUCCESS succeeded, $FAIL failed (共 $TOTAL)"
echo "============================================================"
