#!/usr/bin/env bash
# Epic loop: fresh Claude Code session per Handoff step until done/halt.
# Default: headless auto-chain (claude -p, стрим в терминал). --interactive: полный UI.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export EPIC_LOOP=1

RESOLVE=(python3 .claude/hooks/epic_resolve.py --cwd "$ROOT")
STATE_DIR="$ROOT/.claude/runtime/epic"
mkdir -p "$STATE_DIR"
STREAM_FILTER="$ROOT/.claude/hooks/epic_stream_filter.py"

usage() {
  cat <<'EOF'
Usage: ./scripts/epic-loop.sh [options] [decompose-id|path] [MODEL]

  MODEL — точное имя для `claude --model` (полный id / gateway alias).

Examples:
  ./scripts/epic-loop.sh decompose-v1-p1-pipeline-db-e2e provider/your-model-id
  ./scripts/epic-loop.sh --interactive decompose-… provider/your-model-id

Modes (default = headless auto-chain):
  headless     — claude -p; стрим в терминал + лог session-N.log; шаги s01→s02→… без /exit
  --interactive — полный UI Claude Code; после FINISH нужен /exit вручную

Options:
  -m, --model NAME
      --permission-mode MODE    dontAsk|bypassPermissions|acceptEdits|… (default: dontAsk)
      --role PREFIX             BACK|FRONT|INTEG (default: BACK)
      --max N                   (default: 40)
      --interactive             полный UI (не автоцепочка)
      --headless                явный headless (default, для совместимости)
      --verbose                 полный JSON resolve/status
  -h, --help

Env: CLAUDE_BIN, EPIC_CLAUDE_ARGS, EPIC_PERMISSION_MODE, EPIC_ROLE, EPIC_MAX, EPIC_VERBOSE=1
EOF
}

find_claude() {
  if [[ -n "${CLAUDE_BIN:-}" && -x "$CLAUDE_BIN" ]]; then
    echo "$CLAUDE_BIN"
    return
  fi
  if command -v claude >/dev/null 2>&1; then
    command -v claude
    return
  fi
  local cand
  cand="$(ls -1d "$HOME"/.cursor/extensions/anthropic.claude-code-*/resources/native-binary/claude 2>/dev/null | sort -V | tail -1 || true)"
  if [[ -n "$cand" && -x "$cand" ]]; then
    echo "$cand"
    return
  fi
  echo "claude binary not found; set CLAUDE_BIN" >&2
  exit 127
}

is_decompose_ref() {
  local ref="$1"
  [[ "$ref" == decompose-* ]] && return 0
  [[ "$ref" == memory-bank/*decompose* ]] && return 0
  [[ -f "$ROOT/$ref/index.md" ]] && return 0
  [[ -f "$ROOT/$ref" && "$ref" == */index.md ]] && return 0
  return 1
}

print_resolve_summary() {
  local json="$1"
  if [[ "${EPIC_VERBOSE:-0}" == "1" || "${VERBOSE:-0}" == "1" ]]; then
    echo "$json"
    return
  fi
  echo "$json" | python3 -c '
import json, sys
r = json.load(sys.stdin)
print("==> next command:", r.get("command"))
if r.get("pending_steps") is not None:
    print("==> pending steps:", r.get("pending_steps"))
if r.get("reason"):
    print("==> reason:", r.get("reason"))
' 2>/dev/null || echo "$json"
}

MODEL=""
PERM_MODE="${EPIC_PERMISSION_MODE:-dontAsk}"
ROLE="${EPIC_ROLE:-BACK}"
MAX_ITER="${EPIC_MAX:-40}"
DECOMPOSE=""
HEADLESS=1
INTERACTIVE=0
VERBOSE=0
EXTRA_ARGS=()
POSITIONAL=()
# shellcheck disable=SC2206
[[ -n "${EPIC_CLAUDE_ARGS:-}" ]] && EXTRA_ARGS=( ${EPIC_CLAUDE_ARGS} )

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    -m|--model)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      MODEL="$2"
      shift 2
      ;;
    --permission-mode)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      PERM_MODE="$2"
      shift 2
      ;;
    --role)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      ROLE="$2"
      shift 2
      ;;
    --max)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      MAX_ITER="$2"
      shift 2
      ;;
    --headless)
      HEADLESS=1
      INTERACTIVE=0
      shift
      ;;
    --interactive)
      INTERACTIVE=1
      HEADLESS=0
      shift
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --)
      shift
      EXTRA_ARGS+=("$@")
      break
      ;;
    -*)
      echo "unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [[ ${#POSITIONAL[@]} -ge 2 ]]; then
  DECOMPOSE="${POSITIONAL[0]}"
  if [[ -z "$MODEL" ]]; then
    MODEL="${POSITIONAL[1]}"
  fi
elif [[ ${#POSITIONAL[@]} -eq 1 ]]; then
  ref="${POSITIONAL[0]}"
  if is_decompose_ref "$ref"; then
    DECOMPOSE="$ref"
  elif [[ -z "$MODEL" ]]; then
    MODEL="$ref"
  else
    DECOMPOSE="$ref"
  fi
fi

CLAUDE="$(find_claude)"
PERM_ARGS=(--permission-mode "$PERM_MODE")
MODEL_ARGS=()
if [[ -n "$MODEL" ]]; then
  MODEL_ARGS=(--model "$MODEL")
fi

ARM_ARGS=()
if [[ -n "$MODEL" ]]; then
  ARM_ARGS+=(--model "$MODEL")
fi

if [[ -n "$DECOMPOSE" ]]; then
  echo "==> arm epic: $DECOMPOSE (role=$ROLE max=$MAX_ITER model=${MODEL:-unset})"
  "${RESOLVE[@]}" arm "$DECOMPOSE" --role "$ROLE" --max "$MAX_ITER" "${ARM_ARGS[@]}"
fi

STATUS="$("${RESOLVE[@]}" status)"
if [[ "${VERBOSE}" == "1" || "${EPIC_VERBOSE:-0}" == "1" ]]; then
  echo "$STATUS"
else
  echo "$STATUS" | python3 -c '
import json,sys
s=json.load(sys.stdin)
print("==> epic active:", s.get("active"), "status:", s.get("status"), "model:", s.get("model"))
'
fi
echo "$STATUS" | python3 -c 'import json,sys; s=json.load(sys.stdin); assert s.get("active"), "epic not armed — pass decompose id"'

if [[ -z "$MODEL" ]]; then
  STORED_MODEL="$(echo "$STATUS" | python3 -c 'import json,sys; s=json.load(sys.stdin); print(s.get("model") or "")')"
  if [[ -n "$STORED_MODEL" ]]; then
    MODEL="$STORED_MODEL"
    MODEL_ARGS=(--model "$MODEL")
  fi
fi

if [[ "$INTERACTIVE" == "1" ]]; then
  MODE_LABEL="interactive UI (ручный /exit после FINISH)"
else
  MODE_LABEL="headless auto-chain (-p)"
fi
echo "==> claude=$CLAUDE mode=$MODE_LABEL model=${MODEL:-default} permission-mode=$PERM_MODE"

run_claude_session() {
  local iter="$1"
  local prompt_file="$2"
  local log_file="$STATE_DIR/session-${iter}.log"
  local prompt
  prompt="$(cat "$prompt_file")"

  if [[ "$HEADLESS" == "1" ]]; then
    echo "==> headless: стрим ниже (tools + text); полный JSON → $log_file"
    echo "==> параллельно: tail -f $log_file"
    set +e
  "$CLAUDE" -p \
      --output-format stream-json \
      --include-partial-messages \
      --verbose \
      "$prompt" \
      "${PERM_ARGS[@]}" "${MODEL_ARGS[@]}" "${EXTRA_ARGS[@]}" \
      2>&1 | tee "$log_file" | python3 "$STREAM_FILTER"
    claude_rc=${PIPESTATUS[0]}
    set -e
    return "$claude_rc"
  fi

  echo "==> interactive: полный UI Claude Code (видишь ответ модели)"
  echo "==> после FINISH+Handoff: /exit вручную — loop не перейдёт к следующему шагу без выхода"
  echo "==> для автоцепочки s01→s02→… без /exit: перезапусти без --interactive"
  echo "==> Ctrl+C в loop = halt epic (не жми, если шаг не закончен)"
  set +e
  "$CLAUDE" "$prompt" "${PERM_ARGS[@]}" "${MODEL_ARGS[@]}" "${EXTRA_ARGS[@]}"
  claude_rc=$?
  set -e
  return "$claude_rc"
}

iter=0
while true; do
  iter=$((iter + 1))
  echo ""
  echo "======== EPIC SESSION $iter ========"
  set +e
  RESOLVE_JSON="$("${RESOLVE[@]}" resolve 2>&1)"
  rc=$?
  set -e
  print_resolve_summary "$RESOLVE_JSON"
  if [[ $rc -eq 3 ]]; then
    echo "==> EPIC COMPLETE"
    exit 0
  fi
  if [[ $rc -ne 0 ]]; then
    echo "==> EPIC HALTED (resolve rc=$rc)"
    "${RESOLVE[@]}" status
    exit "$rc"
  fi

  PROMPT_FILE="$STATE_DIR/next-prompt.txt"
  if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "missing $PROMPT_FILE" >&2
    exit 1
  fi
  echo "==> prompt (first lines):"
  sed -n '1,8p' "$PROMPT_FILE"
  echo "..."

  set +e
  run_claude_session "$iter" "$PROMPT_FILE"
  claude_rc=$?
  set -e
  echo "==> claude exit=$claude_rc"

  if [[ $claude_rc -eq 130 ]] || [[ $claude_rc -eq 143 ]]; then
    echo "==> EPIC HALTED (Ctrl+C)"
    "${RESOLVE[@]}" halt --reason 'user interrupt (Ctrl+C)'
    exit "$claude_rc"
  fi

  set +e
  AFTER_JSON="$("${RESOLVE[@]}" after 2>&1)"
  after_rc=$?
  set -e
  if [[ "${VERBOSE}" == "1" ]]; then
    echo "$AFTER_JSON"
  else
    echo "$AFTER_JSON" | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("==> after:", r.get("status"), r.get("reason"))
' 2>/dev/null || echo "$AFTER_JSON"
  fi
  if [[ $after_rc -eq 3 ]]; then
    echo "==> EPIC COMPLETE"
    exit 0
  fi
  if [[ $after_rc -ne 0 ]]; then
    echo "==> EPIC HALTED (after rc=$after_rc)"
    "${RESOLVE[@]}" status
    exit "$after_rc"
  fi
done
