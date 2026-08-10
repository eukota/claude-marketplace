#!/usr/bin/env bash

input=$(cat)
now=$(date +%s)

# One jq pass for every field. The status line re-renders constantly, so each
# extra subprocess is paid on every keystroke-driven redraw. `// ""` (not
# `// empty`) keeps absent fields as empty strings so the @tsv column
# positions stay fixed.
IFS=$'\t' read -r cwd used_pct remaining_pct input_tokens output_tokens \
  cache_read cache_write five_pct five_reset week_pct week_reset <<< "$(
  printf '%s' "$input" | jq -r '[
    .workspace.current_dir // .cwd // "",
    .context_window.used_percentage // "",
    .context_window.remaining_percentage // "",
    .context_window.total_input_tokens // 0,
    .context_window.total_output_tokens // 0,
    .context_window.current_usage.cache_read_input_tokens // 0,
    .context_window.current_usage.cache_creation_input_tokens // 0,
    .rate_limits.five_hour.used_percentage // "",
    .rate_limits.five_hour.resets_at // "",
    .rate_limits.seven_day.used_percentage // "",
    .rate_limits.seven_day.resets_at // ""
  ] | @tsv')"

# Pricing for claude-sonnet-4-6 (per million tokens)
# Input: $3.00, Output: $15.00, Cache read: $0.30, Cache write: $3.75
cost=$(awk -v i="$input_tokens" -v o="$output_tokens" -v cr="$cache_read" -v cw="$cache_write" \
  'BEGIN { printf "%.4f", (i * 3.00 + o * 15.00 + cr * 0.30 + cw * 3.75) / 1000000 }')

# Build a compact 10-char progress bar from a percentage (0-100)
# $1 = percentage (integer), $2 = filled char, $3 = empty char
make_bar() {
  local pct=$1
  local filled_char=$2
  local empty_char=$3
  local bar_width=10
  local filled=$(awk -v p="$pct" -v w="$bar_width" 'BEGIN { printf "%d", int(p * w / 100 + 0.5) }')
  local empty=$(( bar_width - filled ))
  local bar=""
  local i
  for (( i=0; i<filled; i++ )); do bar="${bar}${filled_char}"; done
  for (( i=0; i<empty; i++ )); do bar="${bar}${empty_char}"; done
  echo "$bar"
}

# Pick ANSI color based on remaining percentage
# >50% remaining = green, 25-50% = yellow, <25% = red
color_for_remaining() {
  local rem=$1
  if awk -v r="$rem" 'BEGIN { exit !(r > 50) }'; then
    echo "32"   # green
  elif awk -v r="$rem" 'BEGIN { exit !(r > 25) }'; then
    echo "33"   # yellow
  else
    echo "31"   # red
  fi
}

# Pick ANSI color based on used percentage (inverse of remaining)
color_for_used() {
  local used=$1
  if awk -v u="$used" 'BEGIN { exit !(u < 50) }'; then
    echo "32"   # green
  elif awk -v u="$used" 'BEGIN { exit !(u < 75) }'; then
    echo "33"   # yellow
  else
    echo "31"   # red
  fi
}

# Format a unix epoch as a short "time until reset" string, e.g. 2h13m or 3d4h
time_until() {
  local target=$1
  awk -v t="$target" -v n="$now" 'BEGIN {
    d = t - n
    if (d <= 0) { print "now"; exit }
    days = int(d / 86400)
    hours = int((d % 86400) / 3600)
    mins = int((d % 3600) / 60)
    if (days > 0)       printf "%dd%dh", days, hours
    else if (hours > 0) printf "%dh%dm", hours, mins
    else                printf "%dm", mins
  }'
}

# Shorten cwd: replace $HOME with ~
home_dir="$HOME"
tilde="~"
short_cwd="${cwd/#$home_dir/$tilde}"

# Cost part
cost_part="\$${cost}"

# Build bar sections only when context data is available
if [ -n "$used_pct" ] && [ -n "$remaining_pct" ]; then
  used_int=$(printf "%.0f" "$used_pct")
  rem_int=$(printf "%.0f" "$remaining_pct")

  color=$(color_for_remaining "$rem_int")

  used_bar=$(make_bar "$used_int" "▓" "░")
  rem_bar=$(make_bar "$rem_int" "▓" "░")

  printf '\033[0;36m%s\033[0m  ' "$short_cwd"
  printf '\033[0;37mused \033[%sm%s\033[0m \033[0;37m%s%%\033[0m  ' "$color" "$used_bar" "$used_int"
  printf '\033[0;37mleft \033[%sm%s\033[0m \033[0;37m%s%%\033[0m  ' "$color" "$rem_bar" "$rem_int"
  printf '\033[0;32m%s\033[0m' "$cost_part"
else
  printf '\033[0;36m%s\033[0m  \033[0;32m%s\033[0m' "$short_cwd" "$cost_part"
fi

# Log account usage to a JSONL history, one row per observed change.
# Window identity is the resets_at epoch, so the report can group by window.
usage_log="${CLAUDE_USAGE_LOG:-$HOME/.claude/usage-log.jsonl}"
usage_state="${usage_log%.jsonl}.last"
if [ -n "$five_pct" ] || [ -n "$week_pct" ]; then
  sig="${five_pct}|${five_reset}|${week_pct}|${week_reset}"
  last=$(cat "$usage_state" 2>/dev/null)
  if [ "$sig" != "$last" ]; then
    printf '{"ts":%s,"five_pct":%s,"five_reset":%s,"week_pct":%s,"week_reset":%s}\n' \
      "$now" "${five_pct:-null}" "${five_reset:-null}" \
      "${week_pct:-null}" "${week_reset:-null}" >> "$usage_log"
    printf '%s' "$sig" > "$usage_state"
  fi
fi

# Second line: account-level subscription usage (5-hour session + 7-day weekly)
if [ -n "$five_pct" ] || [ -n "$week_pct" ]; then
  printf '\n'
  printf '\033[0;35macct\033[0m  '

  if [ -n "$five_pct" ]; then
    five_used=$(printf "%.0f" "$five_pct")
    five_left=$(( 100 - five_used ))
    five_color=$(color_for_used "$five_used")
    five_bar=$(make_bar "$five_used" "▓" "░")
    printf '\033[0;37m5h \033[%sm%s\033[0m \033[0;37m%s%% used, %s%% left\033[0m' \
      "$five_color" "$five_bar" "$five_used" "$five_left"
    if [ -n "$five_reset" ]; then
      printf '\033[0;90m (resets %s)\033[0m' "$(time_until "$five_reset")"
    fi
  fi

  if [ -n "$five_pct" ] && [ -n "$week_pct" ]; then
    printf '  \033[0;90m|\033[0m  '
  fi

  if [ -n "$week_pct" ]; then
    week_used=$(printf "%.0f" "$week_pct")
    week_left=$(( 100 - week_used ))
    week_color=$(color_for_used "$week_used")
    week_bar=$(make_bar "$week_used" "▓" "░")
    printf '\033[0;37m7d \033[%sm%s\033[0m \033[0;37m%s%% used, %s%% left\033[0m' \
      "$week_color" "$week_bar" "$week_used" "$week_left"
    if [ -n "$week_reset" ]; then
      printf '\033[0;90m (resets %s)\033[0m' "$(time_until "$week_reset")"
    fi
  fi
fi
