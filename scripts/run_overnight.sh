#!/bin/bash
# 一夜跑完: Phase 3 补跑 + Phase 4 + Phase 5
# 用法: nohup bash scripts/run_overnight.sh > overnight.log 2>&1 &

set -uo pipefail
# 注意: 不用 set -e，单集失败不应阻止后续集数

export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/secrets/liaoandi_vertex_ai_key.json"

SCRIPTS="/Users/antonio/Desktop/podcast_juicer/scripts"
OUTPUT="/Users/antonio/Desktop/podcast_juicer/output"
NOTES_DIR="$OUTPUT/notes"
PYTHON="/Users/antonio/Desktop/podcast_juicer/venv/bin/python3"
PROGRESS_MD="/Users/antonio/Desktop/podcast_juicer/batch_progress.md"

TRASH="/Users/antonio/Desktop/podcast_juicer/output/_trash"
mkdir -p "$TRASH"

TOTAL=0
SUCCESS=0
FAIL=0
SKIP=0

log() {
    echo "[$(date '+%H:%M:%S')] $*"
}

# 安全删除: mv 到 _trash 目录
safe_rm() {
    local f="$1"
    if [ -f "$f" ]; then
        mv "$f" "$TRASH/$(basename "$f").$(date +%s)" 2>/dev/null || true
    fi
}

# 单集全流程: step1 → step2 → step3 → step4
# 要求 step1 无缺失 chunk 才继续
run_pipeline() {
    local ep=$1
    local dir="$OUTPUT/sv101_ep${ep}"
    local mp3="$dir/${ep}.mp3"
    local parti="$dir/sv101_ep${ep}_participants.json"
    local transcript="$dir/${ep}_transcript_gemini.json"
    local progress_file="${transcript}.progress"
    local signals="$dir/sv101_ep${ep}_signals.json"
    local verified="$dir/sv101_ep${ep}_verified_signals.json"
    local notes="$NOTES_DIR/sv101_ep${ep}_investment_notes.md"

    TOTAL=$((TOTAL + 1))

    if [ ! -f "$mp3" ]; then
        log "  ep${ep}: SKIP (无 MP3)"
        SKIP=$((SKIP + 1))
        return 1
    fi

    # Step 1: 转录（支持断点续传，会自动补缺失 chunk）
    log "  Step 1: 转录..."
    if ! $PYTHON "$SCRIPTS/step1_transcribe_gemini.py" "$mp3" "$parti" "$transcript" 2>&1; then
        log "  Step 1: FAILED (有缺失 chunk，不继续)"
        FAIL=$((FAIL + 1))
        return 1
    fi
    log "  Step 1: done"

    # Step 2: 信号提取（总是重跑，因为转录可能更新了）
    log "  Step 2: 提取信号..."
    if ! $PYTHON "$SCRIPTS/step2_extract_signals.py" "$transcript" "$signals" 2>&1; then
        log "  Step 2: FAILED"
        FAIL=$((FAIL + 1))
        return 1
    fi
    log "  Step 2: done"

    # Step 3: 验证
    log "  Step 3: 验证信号..."
    if ! $PYTHON "$SCRIPTS/step3_verify_signals.py" "$signals" "$verified" 2>&1; then
        log "  Step 3: FAILED"
        FAIL=$((FAIL + 1))
        return 1
    fi
    log "  Step 3: done"

    # Step 4: 笔记
    log "  Step 4: 生成笔记..."
    if ! $PYTHON "$SCRIPTS/step4_generate_notes.py" "$transcript" "$signals" "$verified" "$notes" 2>&1; then
        log "  Step 4: FAILED"
        FAIL=$((FAIL + 1))
        return 1
    fi
    log "  Step 4: done"

    # 统计信号数
    local sig_count
    sig_count=$($PYTHON -c "import json; print(len(json.load(open('$signals'))['signals']))" 2>/dev/null || echo "?")
    log "  ep${ep}: COMPLETE ($sig_count signals)"
    SUCCESS=$((SUCCESS + 1))
    return 0
}

# Step0 下载 + 全流程
run_download_and_pipeline() {
    local ep=$1
    local url="https://sv101.fireside.fm/${ep}"
    local dir="$OUTPUT/sv101_ep${ep}"
    local mp3="$dir/${ep}.mp3"

    mkdir -p "$dir"

    # 如果已有 MP3 就跳过下载
    if [ -f "$mp3" ]; then
        log "  ep${ep}: MP3 已存在，跳过下载"
    else
        log "  Step 0: 下载 ep${ep}..."
        cd "$dir"
        if ! $PYTHON "$SCRIPTS/step0_download_and_prepare.py" "$url" "${ep}" 2>&1; then
            log "  Step 0: FAILED"
            cd "$OUTPUT/.."
            TOTAL=$((TOTAL + 1))
            FAIL=$((FAIL + 1))
            return 1
        fi
        # step0 输出 participants.json 到当前目录，重命名
        if [ -f "participants.json" ]; then
            mv participants.json "sv101_ep${ep}_participants.json"
        fi
        cd "$OUTPUT/.."
    fi

    run_pipeline "$ep"
}

log "============================================================"
log "Overnight Pipeline Start"
log "============================================================"

# =============================================
# Phase 3 补跑: ep194, ep196 (有缺失 chunk)
# =============================================
log ""
log "=== Phase 3 补跑: 补齐缺失 chunk ==="

for ep in 194 196; do
    dir="$OUTPUT/sv101_ep${ep}"
    transcript="$dir/${ep}_transcript_gemini.json"
    signals="$dir/sv101_ep${ep}_signals.json"
    verified="$dir/sv101_ep${ep}_verified_signals.json"
    notes="$NOTES_DIR/sv101_ep${ep}_investment_notes.md"

    log ""
    log "--- ep${ep} ---"

    # 清理旧的不完整 step2-4 产出
    for f in "$signals" "$verified" "$notes"; do
        if [ -f "$f" ]; then
            log "  清理旧文件: $(basename $f)"
            safe_rm "$f"
        fi
    done

    # 移走旧的（不完整的）transcript，让 step1 从 .progress 断点续传
    if [ -f "$transcript" ]; then
        log "  清理不完整 transcript"
        safe_rm "$transcript"
    fi

    run_pipeline "$ep"
done

# =============================================
# Phase 4: 下载 + 全流程 (ep193, ep219, ep221)
# =============================================
log ""
log "=== Phase 4: 下载 + 全流程 ==="

for ep in 193 219 221; do
    log ""
    log "--- ep${ep} ---"
    run_download_and_pipeline "$ep"
done

# =============================================
# Phase 3 重试: ep194, ep196 (最多 3 轮)
# =============================================
log ""
log "=== Phase 3 重试: ep194, ep196 (最多 3 轮) ==="

RETRY_EPS=(194 196)
for round in 1 2 3; do
    STILL_FAILED=()
    for ep in "${RETRY_EPS[@]}"; do
        dir="$OUTPUT/sv101_ep${ep}"
        transcript="$dir/${ep}_transcript_gemini.json"
        progress_file="${transcript}.progress"

        # 如果 progress 文件不存在说明已经全部成功
        if [ ! -f "$progress_file" ]; then
            log "  ep${ep}: 已完成，跳过"
            continue
        fi

        log ""
        log "  [轮次 $round/3] ep${ep}"

        # 清理旧 transcript（让 step1 从 .progress 续传）
        safe_rm "$transcript"
        # 清理旧 step2-4 产出
        safe_rm "$dir/sv101_ep${ep}_signals.json"
        safe_rm "$dir/sv101_ep${ep}_verified_signals.json"
        safe_rm "$NOTES_DIR/sv101_ep${ep}_investment_notes.md"

        if run_pipeline "$ep"; then
            log "  ep${ep}: 第 $round 轮成功!"
        else
            STILL_FAILED+=("$ep")
            log "  ep${ep}: 第 $round 轮仍有缺失 chunk"
        fi
    done

    if [ ${#STILL_FAILED[@]} -eq 0 ]; then
        log "  所有补跑集已完成!"
        break
    fi
    RETRY_EPS=("${STILL_FAILED[@]}")
    log "  第 $round 轮结束，仍需重试: ${RETRY_EPS[*]}"
done

# =============================================
# Phase 5: 重下 + 全流程 (10 集)
# =============================================
log ""
log "=== Phase 5: 重下 + 全流程 ==="

for ep in 190 195 198 199 200 201 203 204 205 206; do
    log ""
    log "--- ep${ep} ---"
    run_download_and_pipeline "$ep"
done

# =============================================
# 补跑 ep194, ep196 (缺失 chunk，最多 3 轮)
# =============================================
log ""
log "=== 补跑 ep194, ep196 (最多 3 轮) ==="

RETRY_EPS=(194 196)
for round in 1 2 3; do
    STILL_FAILED=()
    for ep in "${RETRY_EPS[@]}"; do
        dir="$OUTPUT/sv101_ep${ep}"
        transcript="$dir/${ep}_transcript_gemini.json"
        progress_file="${transcript}.progress"

        if [ ! -f "$progress_file" ]; then
            log "  ep${ep}: 已完成，跳过"
            continue
        fi

        log ""
        log "  [轮次 $round/3] ep${ep}"

        safe_rm "$transcript"
        safe_rm "$dir/sv101_ep${ep}_signals.json"
        safe_rm "$dir/sv101_ep${ep}_verified_signals.json"
        safe_rm "$NOTES_DIR/sv101_ep${ep}_investment_notes.md"

        if run_pipeline "$ep"; then
            log "  ep${ep}: 第 $round 轮成功!"
        else
            STILL_FAILED+=("$ep")
            log "  ep${ep}: 第 $round 轮仍有缺失 chunk"
        fi
    done

    if [ ${#STILL_FAILED[@]} -eq 0 ]; then
        log "  所有补跑集已完成!"
        break
    fi
    RETRY_EPS=("${STILL_FAILED[@]}")
    log "  第 $round 轮结束，仍需重试: ${RETRY_EPS[*]}"
done

# =============================================
# 总结
# =============================================
log ""
log "============================================================"
log "Overnight Pipeline 完成"
log "  成功: $SUCCESS"
log "  失败: $FAIL"
log "  跳过: $SKIP"
log "  总计: $TOTAL"
log "============================================================"
