#!/bin/bash
# 分批流水线：step0(如需) → step1(串行) → step2+step3(后台)
# 用法: bash run_batch.sh 218 217 216 215 214 213
set -uo pipefail

BASE="/Users/antonio/Desktop/podcast_juicer"
SCRIPTS="$BASE/scripts"
OUTPUT="$BASE/output"
LOG="$BASE/output/batch_pipeline.log"

if [ $# -eq 0 ]; then
    echo "用法: bash run_batch.sh <ep1> <ep2> ..."
    exit 1
fi

TOTAL=$#
COUNT=0
FAILED=""
BG_PIDS=""

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"
}

# step2 + step3 后台
run_step2_step3_bg() {
    local ep=$1
    local dir="$OUTPUT/sv101_ep${ep}"
    local transcript="$dir/${ep}_transcript_gemini.json"
    local signals="$dir/sv101_ep${ep}_signals.json"
    local verified="$dir/sv101_ep${ep}_verified_signals.json"

    (
        log "ep${ep} step2 START"
        if python3 "$SCRIPTS/step2_extract_signals.py" "$transcript" "$signals" >> "$LOG" 2>&1; then
            log "ep${ep} step2 DONE"
        else
            log "ep${ep} step2 FAILED"
            exit 1
        fi

        log "ep${ep} step3 START"
        if python3 "$SCRIPTS/step3_verify_signals.py" "$signals" "$verified" >> "$LOG" 2>&1; then
            log "ep${ep} step3 DONE"
        else
            log "ep${ep} step3 FAILED"
            exit 1
        fi
        log "ep${ep} COMPLETE ✓"
    ) &
    BG_PIDS="$BG_PIDS $!"
}

log "=========================================="
log "批次开始: $* (共 ${TOTAL} 集)"
log "=========================================="

for ep in "$@"; do
    COUNT=$((COUNT + 1))
    dir="$OUTPUT/sv101_ep${ep}"
    mkdir -p "$dir"

    log "──── [$COUNT/$TOTAL] ep${ep} ────"

    # step0: 下载 mp3（如需）
    mp3=$(ls "$dir"/*.mp3 2>/dev/null | head -1)
    if [ -z "$mp3" ]; then
        log "ep${ep} step0 下载 START"
        cd "$dir"
        if python3 "$SCRIPTS/step0_download_and_prepare.py" "https://sv101.fireside.fm/${ep}" "sv101_ep${ep}" >> "$LOG" 2>&1; then
            # 统一文件名为 ${ep}.mp3
            if [ -f "sv101_ep${ep}.mp3" ] && [ ! -f "${ep}.mp3" ]; then
                mv "sv101_ep${ep}.mp3" "${ep}.mp3"
            fi
            mp3=$(ls "$dir"/*.mp3 2>/dev/null | head -1)
            if [ -n "$mp3" ]; then
                log "ep${ep} step0 DONE ($(du -h "$mp3" | cut -f1))"
            else
                log "ep${ep} step0 FAILED: mp3 未生成"
                FAILED="$FAILED ep${ep}(step0)"
                continue
            fi
        else
            log "ep${ep} step0 FAILED"
            FAILED="$FAILED ep${ep}(step0)"
            continue
        fi
    else
        log "ep${ep} mp3 已存在，跳过下载"
    fi

    # participants
    parti="$dir/sv101_ep${ep}_participants.json"
    parti_arg=""
    if [ -f "$parti" ]; then
        parti_arg="$parti"
    fi

    # step1: 转录（串行）
    transcript="$dir/${ep}_transcript_gemini.json"
    if [ -f "$transcript" ]; then
        log "ep${ep} step1 已存在，跳过转录"
    else
        log "ep${ep} step1 转录 START"
        cd "$dir"
        if python3 "$SCRIPTS/step1_transcribe_gemini.py" "$mp3" $parti_arg "$transcript" 2>&1 | tee -a "$LOG"; then
            if [ -f "$transcript" ]; then
                log "ep${ep} step1 DONE ($(du -h "$transcript" | cut -f1))"
            else
                log "ep${ep} step1 FAILED: transcript 未生成"
                FAILED="$FAILED ep${ep}(step1)"
                continue
            fi
        else
            log "ep${ep} step1 FAILED"
            FAILED="$FAILED ep${ep}(step1)"
            continue
        fi
    fi

    # step2+step3 后台
    signals="$dir/sv101_ep${ep}_signals.json"
    verified="$dir/sv101_ep${ep}_verified_signals.json"
    if [ -f "$verified" ]; then
        log "ep${ep} step2+step3 已存在，跳过"
    elif [ -f "$transcript" ]; then
        run_step2_step3_bg "$ep"
        log "ep${ep} step2+step3 已启动后台"
    fi
done

log "──────────────────────────────────────"
log "所有 step1 完成，等待后台 step2+step3..."
wait

log "=========================================="
log "批次完成！成功: $((TOTAL - $(echo "$FAILED" | wc -w)))"
if [ -n "$FAILED" ]; then
    log "失败:$FAILED"
else
    log "全部成功 ✓"
fi
log "=========================================="
