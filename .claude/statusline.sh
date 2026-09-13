#!/bin/bash
# ============================================================================
# Claude Code Statusline — Small (2-line) Edition
# ============================================================================
# Line 1: 🧠 Model ⚡effort 💡 │ 🌿branch🚧 │ 📂 ~/path
# Line 2: 📝 ████░░░░░░ 44% │ 🚀 5H ███░░░░░░░ 31% (2h10m) · 7D ██████░░░░ 58% (Mon)
# Derived from awesome-statusline.sh v1.0.3 (same parsing/gradients, compact)
# ============================================================================

export PATH="$(dirname "$0"):$PATH"

input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name // "Unknown"')
CURRENT_DIR=$(echo "$input" | jq -r '.workspace.current_dir // "."')
CONTEXT_SIZE=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')
CURRENT_USAGE=$(echo "$input" | jq -r '.context_window.current_usage // null')
FIVE_HOUR_PCT=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
FIVE_HOUR_RESET=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
SEVEN_DAY_PCT=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
SEVEN_DAY_RESET=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

RESET="\033[0m"
BOLD="\033[1m"
CLR="\033[K"
C_PINK="\033[38;2;245;194;231m"
C_LAVENDER="\033[38;2;180;190;254m"
C_SKY="\033[38;2;137;220;235m"
C_TEXT="\033[38;2;205;214;244m"
C_PEACH="\033[38;2;250;179;135m"
C_OVERLAY="\033[38;2;108;112;134m"

# Context gradient: Latte Yellow(0%) → Latte Red(50%) → Mauve(100%)
get_context_gradient_color() {
    local pct=$1 r g b
    if [[ $pct -lt 50 ]]; then
        local t=$((pct * 2))
        r=$((223 + (210 - 223) * t / 100)); g=$((142 + (15 - 142) * t / 100)); b=$((29 + (57 - 29) * t / 100))
    else
        local t=$(((pct - 50) * 2))
        r=$((210 + (136 - 210) * t / 100)); g=$((15 + (57 - 15) * t / 100)); b=$((57 + (239 - 57) * t / 100))
    fi
    echo "$r;$g;$b"
}

# Usage gradient: Mocha Green → Latte Teal → Latte Blue
get_usage_gradient_color() {
    local pct=$1 r g b
    if [[ $pct -lt 50 ]]; then
        local t=$((pct * 2))
        r=$((166 + (23 - 166) * t / 100)); g=$((227 + (146 - 227) * t / 100)); b=$((161 + (153 - 161) * t / 100))
    else
        local t=$(((pct - 50) * 2))
        r=$((23 + (30 - 23) * t / 100)); g=$((146 + (102 - 146) * t / 100)); b=$((153 + (245 - 153) * t / 100))
    fi
    echo "$r;$g;$b"
}

# Gradient progress bar (same as big version)
generate_progress_bar() {
    local pct=$1 width=$2 gradient_type=$3 bar=""
    local filled=$(( (pct * width + 50) / 100 ))
    [[ $filled -gt $width ]] && filled=$width
    local end_color
    if [[ "$gradient_type" == "context" ]]; then
        end_color=$(get_context_gradient_color "$pct")
    else
        end_color=$(get_usage_gradient_color "$pct")
    fi
    for ((i=0; i<filled; i++)); do
        local block_pct=$((i * 100 / width))
        local color
        if [[ "$gradient_type" == "context" ]]; then
            color=$(get_context_gradient_color "$block_pct")
        else
            color=$(get_usage_gradient_color "$block_pct")
        fi
        bar+="\033[38;2;${color}m█"
    done
    local empty=$((width - filled))
    for ((i=0; i<empty; i++)); do
        bar+="\033[38;2;${end_color}m░"
    done
    bar+="$RESET"
    printf "%b" "$bar"
}

# Model with emoji
case "$MODEL" in
    *Opus*) MODEL_DISPLAY="🧠 ${C_PINK}${MODEL}${RESET}" ;;
    *Sonnet*) MODEL_DISPLAY="🎵 ${C_LAVENDER}${MODEL}${RESET}" ;;
    *Haiku*) MODEL_DISPLAY="⚡️ ${C_SKY}${MODEL}${RESET}" ;;
    *) MODEL_DISPLAY="🤖 ${C_TEXT}${MODEL}${RESET}" ;;
esac
EFFORT=$(echo "$input" | jq -r '.effort.level // empty')
THINKING=$(echo "$input" | jq -r '.thinking.enabled // empty')
[ -n "$EFFORT" ] && MODEL_DISPLAY="${MODEL_DISPLAY} ${C_PEACH}⚡${EFFORT}${RESET}"
[ "$THINKING" = "true" ] && MODEL_DISPLAY="${MODEL_DISPLAY} \033[38;2;249;226;175m💡${RESET}"

# Git: branch + dirty marker in one token
GIT_DISPLAY="${C_OVERLAY}no git${RESET}"
cd "$CURRENT_DIR" 2>/dev/null
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    [[ -z "$BRANCH" ]] && BRANCH="detached"
    if git diff --quiet && git diff --cached --quiet 2>/dev/null; then
        GIT_DISPLAY="\033[38;2;64;160;43m🌿${BRANCH}${RESET}"
    else
        GIT_DISPLAY="\033[38;2;64;160;43m🌿${BRANCH}${RESET}${C_PEACH}🚧${RESET}"
    fi
fi

# Context percent + bar (10 cols, lives on line 2 with the usage bars)
CONTEXT_PERCENT=0
if [[ "$CURRENT_USAGE" != "null" && -n "$CURRENT_USAGE" ]]; then
    INPUT_TOKENS=$(echo "$CURRENT_USAGE" | jq -r '.input_tokens // 0')
    CACHE_CREATE=$(echo "$CURRENT_USAGE" | jq -r '.cache_creation_input_tokens // 0')
    CACHE_READ=$(echo "$CURRENT_USAGE" | jq -r '.cache_read_input_tokens // 0')
    CURRENT_TOKENS=$((INPUT_TOKENS + CACHE_CREATE + CACHE_READ))
    [[ "$CONTEXT_SIZE" -gt 0 ]] && CONTEXT_PERCENT=$((CURRENT_TOKENS * 100 / CONTEXT_SIZE))
fi
CTX_COLOR=$(get_context_gradient_color "$CONTEXT_PERCENT")
CTX_BAR=$(generate_progress_bar "$CONTEXT_PERCENT" 10 "context")
CTX_DISPLAY="📝 ${CTX_BAR} \033[38;2;${CTX_COLOR}m${CONTEXT_PERCENT}%${RESET}"

# Directory (home abbreviated to ~)
C_BLUE="\033[38;2;137;180;250m"
DIR_COMPACT="${CURRENT_DIR/#$HOME/~}"
DIR_DISPLAY="📂 ${C_BLUE}${DIR_COMPACT}${RESET}"

LINE1="${BOLD}${MODEL_DISPLAY}${RESET} │ ${GIT_DISPLAY} │ ${DIR_DISPLAY}"

# Usage reset formatting
format_time_remaining() {
    local reset_epoch="$1"
    [[ -z "$reset_epoch" || "$reset_epoch" == "null" ]] && return
    local now_epoch=$(date +%s)
    local remaining=$((reset_epoch - now_epoch))
    [[ $remaining -lt 0 ]] && remaining=0
    echo "$((remaining / 3600))h$(((remaining % 3600) / 60))m"
}
_date_fmt() {
    local epoch="$1" fmt="$2" out=""
    out=$(date -j -f "%s" "$epoch" "+$fmt" 2>/dev/null) && [[ -n "$out" ]] && { echo "$out"; return; }
    out=$(date -r "$epoch" "+$fmt" 2>/dev/null) && [[ -n "$out" ]] && { echo "$out"; return; }
    date -d "@$epoch" "+$fmt" 2>/dev/null
}

# LINE 2: usage bars (10 cols each)
if [[ -n "$FIVE_HOUR_PCT" ]]; then
    FIVE_HOUR=$(printf "%.0f" "$FIVE_HOUR_PCT")
    SEVEN_DAY=$(printf "%.0f" "${SEVEN_DAY_PCT:-0}")
    FIVE_RESET_FMT=$(format_time_remaining "$FIVE_HOUR_RESET")
    SEVEN_RESET_FMT=$(_date_fmt "$SEVEN_DAY_RESET" "%a")
    FIVE_BAR=$(generate_progress_bar "$FIVE_HOUR" 10 "usage")
    SEVEN_BAR=$(generate_progress_bar "$SEVEN_DAY" 10 "usage")
    FIVE_COLOR=$(get_usage_gradient_color "$FIVE_HOUR")
    SEVEN_COLOR=$(get_usage_gradient_color "$SEVEN_DAY")
    LINE2="${CTX_DISPLAY} │ 🚀 \033[38;2;${FIVE_COLOR}m5H${RESET} ${FIVE_BAR} \033[38;2;${FIVE_COLOR}m${FIVE_HOUR}%${RESET} ${C_OVERLAY}(${FIVE_RESET_FMT})${RESET} · \033[38;2;${SEVEN_COLOR}m7D${RESET} ${SEVEN_BAR} \033[38;2;${SEVEN_COLOR}m${SEVEN_DAY}%${RESET} ${C_OVERLAY}(${SEVEN_RESET_FMT})${RESET}"
else
    LINE2="${CTX_DISPLAY} │ ${C_OVERLAY}🚀 Usage: unavailable${RESET}"
fi

printf "%b%b\n" "$LINE1" "$CLR"
printf "%b%b\n" "$LINE2" "$CLR"
