#!/bin/bash
# 跑完所有剩余集的全流程 (step1 → step2 → step3 → step4)
# 用法: nohup bash scripts/run_remaining.sh > remaining.log 2>&1 &

set -uo pipefail

export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/secrets/liaoandi_vertex_ai_key.json"

SCRIPTS="/Users/antonio/Desktop/podcast_juicer/scripts"
OUTPUT="/Users/antonio/Desktop/podcast_juicer/output"
NOTES_DIR="$OUTPUT/notes"
PYTHON="/Users/antonio/Desktop/podcast_juicer/venv/bin/python3"
PROGRESS_MD="/Users/antonio/Desktop/podcast_juicer/batch_progress.md"

TOTAL=0
SUCCESS=0
FAIL=0
SKIP=0

log() {
    echo "[$(date '+%H:%M:%S')] $*"
}

run_full_pipeline() {
    local ep=$1
    local dir="$OUTPUT/sv101_ep${ep}"
    local mp3="$dir/${ep}.mp3"
    local parti="$dir/sv101_ep${ep}_participants.json"
    local transcript="$dir/${ep}_transcript_gemini.json"
    local signals="$dir/sv101_ep${ep}_signals.json"
    local verified="$dir/sv101_ep${ep}_verified_signals.json"
    local notes="$NOTES_DIR/sv101_ep${ep}_investment_notes.md"

    TOTAL=$((TOTAL + 1))

    if [ ! -f "$mp3" ]; then
        log "  ep${ep}: SKIP (无 MP3)"
        SKIP=$((SKIP + 1))
        return 1
    fi

    # 如果已有笔记，跳过
    if [ -f "$notes" ]; then
        log "  ep${ep}: SKIP (已有笔记)"
        SUCCESS=$((SUCCESS + 1))
        return 0
    fi

    # Step 1: 转录（跳过如果已有 transcript 且无 .progress 残留）
    if [ -f "$transcript" ] && [ ! -f "${transcript}.progress" ]; then
        log "  Step 1: 跳过 (转录已完成)"
    else
        log "  Step 1: 转录中..."
        if ! $PYTHON "$SCRIPTS/step1_transcribe_gemini.py" "$mp3" "$parti" "$transcript" 2>&1; then
            log "  Step 1: FAILED"
            FAIL=$((FAIL + 1))
            return 1
        fi
        log "  Step 1: done"
    fi

    # Step 2: 信号提取
    if [ -f "$signals" ]; then
        log "  Step 2: 跳过 (信号已存在)"
    else
        log "  Step 2: 提取信号..."
        if ! $PYTHON "$SCRIPTS/step2_extract_signals.py" "$transcript" "$signals" 2>&1; then
            log "  Step 2: FAILED"
            FAIL=$((FAIL + 1))
            return 1
        fi
        log "  Step 2: done"
    fi

    # Step 3: 验证
    if [ -f "$verified" ]; then
        log "  Step 3: 跳过 (验证已存在)"
    else
        log "  Step 3: 验证信号..."
        if ! $PYTHON "$SCRIPTS/step3_verify_signals.py" "$signals" "$verified" 2>&1; then
            log "  Step 3: FAILED"
            FAIL=$((FAIL + 1))
            return 1
        fi
        log "  Step 3: done"
    fi

    # Step 4: 笔记
    log "  Step 4: 生成笔记..."
    if ! $PYTHON "$SCRIPTS/step4_generate_notes.py" "$transcript" "$signals" "$verified" "$notes" 2>&1; then
        log "  Step 4: FAILED"
        FAIL=$((FAIL + 1))
        return 1
    fi
    log "  Step 4: done"

    # 统计
    local sig_count
    sig_count=$($PYTHON -c "import json; print(len(json.load(open('$signals'))['signals']))" 2>/dev/null || echo "?")
    log "  ep${ep}: COMPLETE ($sig_count signals)"
    SUCCESS=$((SUCCESS + 1))
    return 0
}

log "============================================================"
log "剩余集全流程 Start"
log "============================================================"

# ep201 可能正在转录，脚本会自动检测断点续传
for ep in 201 203 204 205 206 242; do
    log ""
    log "--- ep${ep} ---"
    run_full_pipeline "$ep"
done

log ""
log "============================================================"
log "完成: $SUCCESS succeeded, $FAIL failed, $SKIP skipped (共 $TOTAL)"
log "============================================================"
