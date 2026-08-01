#!/usr/bin/env bash
# Единая точка входа автоцикла (BACK/FRONT/INTEG).
# Треки: epic (одна роль × decompose) | program (journey + GAP fanout).
# Канон: loop/loop-state.yaml + transitions.yaml
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export EPIC_LOOP=1
export PROGRAM_LOOP=1

EPIC_RESOLVE=(python3 .claude/hooks/epic_resolve.py --cwd "$ROOT")
PROG_RESOLVE=(python3 .claude/hooks/program_resolve.py --cwd "$ROOT")
EPIC_STATE_DIR="$ROOT/.claude/runtime/epic"
PROG_STATE_DIR="$ROOT/.claude/runtime/program"
STREAM_FILTER="$ROOT/.claude/hooks/epic_stream_filter.py"
mkdir -p "$EPIC_STATE_DIR" "$PROG_STATE_DIR"

# Smoke: compile all hooks before any session. A broken module (untracked file,
# mid-edit) would otherwise surface as a cryptic IndentationError deep in the
# resolve→epic_lib import chain. Fail fast with the exact file instead.
hook_fail=""
for _hf in "$ROOT"/.claude/hooks/*.py; do
  if ! python3 -m py_compile "$_hf" >/dev/null 2>&1; then
    hook_fail="$(python3 -m py_compile "$_hf" 2>&1 | rg -o '\S+\.py' | head -1 || basename "$_hf")"
    break
  fi
done
if [[ -n "$hook_fail" ]]; then
  echo "==> loop smoke FAIL: hook does not compile: $hook_fail" >&2
  echo "    Fix syntax or remove the file before running the loop." >&2
  exit 2
fi

usage() {
  cat <<'EOF'
Usage: ./loop/loop.sh [options] [decompose-id|path] [MODEL]

Единый runner. По умолчанию — epic (decompose). Journey/GAP — флаги --id/--gap
или автоматически, если decompose лежит в memory-bank/integration/.

Examples:
  # BACK/FRONT — роль из пути
  ./loop/loop.sh decompose-v1-p2-ship gpt
  ./loop/loop.sh gpt                    # продолжить armed epic

  # INTEG — достаточно id/path под integration/; track=program сам
  ./loop/loop.sh decompose-portal gpt
  ./loop/loop.sh decompose-v1-portal gpt --force-implement
  ./loop/loop.sh decompose-v1-portal gpt --from-step e01
  ./loop/loop.sh memory-bank/integration/plan/decompose-portal gpt

  # Явный program / GAP fanout (если нужно переопределить)
  ./loop/loop.sh --id INTEG-JOURNEY-demo \
      --phase GAP_FANOUT \
      --gap memory-bank/integration/gap/…/gap-….md \
      --resume-implement memory-bank/integration/implement/…/e03.md \
      -m gpt

Options:
  -m, --model NAME
      --track epic|program|auto   (default: auto by path)
      --role PREFIX               BACK|FRONT|INTEG (default: infer from path)
      --id NAME                   arm program journey
      --phase PHASE               program phase (default INTEG_STEPS)
      --integ-decompose PATH
      --integ-plan PATH
      --gap PATH
      --resume-implement PATH
      --from-step ID          start at sNN/eNN (e.g. e01)
      --force-implement       force IMPLEMENT mode on arm (ignore stale Handoff)
      --max N
      --permission-mode MODE
      --interactive | --headless
      --verbose
  -h, --help

Канон: .claude/instructions/loop-state.md · loop/
Канон runner: ./loop/loop.sh  (scripts/loop.sh — DEPRECATED redirect)
Legacy wrappers: loop/epic-loop.sh / loop/program-loop.sh → этот файл.
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

detect_track() {
  if [[ "$TRACK_OPT" == "epic" || "$TRACK_OPT" == "program" ]]; then
    echo "$TRACK_OPT"
    return
  fi
  if [[ -n "$PROGRAM_ID" || -n "$GAP" || -n "$INTEG_DECOMPOSE" || -n "$INTEG_PLAN" ]]; then
    echo program
    return
  fi
  if [[ -n "$RESOLVED_TRACK" ]]; then
    echo "$RESOLVED_TRACK"
    return
  fi
  if [[ -n "$DECOMPOSE" ]]; then
    echo epic
    return
  fi
  local active
  active="$(
    "${PROG_RESOLVE[@]}" status 2>/dev/null | python3 -c 'import json,sys; s=json.load(sys.stdin); print("1" if s.get("active") else "0")' 2>/dev/null || echo 0
  )"
  if [[ "$active" == "1" ]]; then
    echo program
    return
  fi
  active="$(
    "${EPIC_RESOLVE[@]}" status 2>/dev/null | python3 -c 'import json,sys; s=json.load(sys.stdin); print("1" if s.get("active") else "0")' 2>/dev/null || echo 0
  )"
  if [[ "$active" == "1" ]]; then
    echo epic
    return
  fi
  local hint
  hint="$(
    python3 - <<'PY' 2>/dev/null || true
import sys
sys.path.insert(0, ".claude/hooks")
from loop_engine import load_loop_state
st = load_loop_state(".")
phase = ((st.get("journey") or {}).get("phase") or "").upper()
if phase.startswith("GAP") or phase.startswith("INTEG_"):
    print("program")
elif st.get("active") and (st.get("epic") or {}).get("decompose"):
    print("epic")
PY
  )"
  if [[ -n "$hint" ]]; then
    echo "$hint"
    return
  fi
  echo ""
}

MODEL=""
PERM_MODE="${EPIC_PERMISSION_MODE:-dontAsk}"
# Empty = infer from decompose path (memory-bank/{back|front|integration}/…)
ROLE="${EPIC_ROLE:-}"
MAX_ITER=""
DECOMPOSE=""
TRACK_OPT="auto"
RESOLVED_TRACK=""
PROGRAM_ID=""
PHASE="INTEG_STEPS"
INTEG_DECOMPOSE=""
INTEG_PLAN=""
GAP=""
RESUME_IMPL=""
FROM_STEP=""
FORCE_IMPLEMENT=0
HEADLESS=1
INTERACTIVE=0
VERBOSE=0
EXTRA_ARGS=()
POSITIONAL=()
# shellcheck disable=SC2206
[[ -n "${EPIC_CLAUDE_ARGS:-}" ]] && EXTRA_ARGS=( ${EPIC_CLAUDE_ARGS} )

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    -m|--model)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      MODEL="$2"; shift 2 ;;
    --permission-mode)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      PERM_MODE="$2"; shift 2 ;;
    --role)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      ROLE="$2"; shift 2 ;;
    --track)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      TRACK_OPT="$2"; shift 2 ;;
    --id)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      PROGRAM_ID="$2"; shift 2 ;;
    --phase)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      PHASE="$2"; shift 2 ;;
    --integ-decompose)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      INTEG_DECOMPOSE="$2"; shift 2 ;;
    --integ-plan)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      INTEG_PLAN="$2"; shift 2 ;;
    --gap)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      GAP="$2"; shift 2 ;;
    --resume-implement)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      RESUME_IMPL="$2"; shift 2 ;;
    --from-step)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      FROM_STEP="$2"; shift 2 ;;
    --force-implement) FORCE_IMPLEMENT=1; shift ;;
    --max)
      [[ $# -ge 2 ]] || { echo "missing value for $1" >&2; exit 2; }
      MAX_ITER="$2"; shift 2 ;;
    --headless) HEADLESS=1; INTERACTIVE=0; shift ;;
    --interactive) INTERACTIVE=1; HEADLESS=0; shift ;;
    --verbose) VERBOSE=1; shift ;;
    --)
      shift; EXTRA_ARGS+=("$@"); break ;;
    -*)
      echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
    *)
      POSITIONAL+=("$1"); shift ;;
  esac
done

# positionals: decompose and/or model (epic style)
if [[ ${#POSITIONAL[@]} -ge 2 ]]; then
  if is_decompose_ref "${POSITIONAL[0]}"; then
    DECOMPOSE="${POSITIONAL[0]}"
    [[ -z "$MODEL" ]] && MODEL="${POSITIONAL[1]}"
  else
    [[ -z "$MODEL" ]] && MODEL="${POSITIONAL[0]}"
    DECOMPOSE="${POSITIONAL[1]}"
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

# Path-based role/track: memory-bank/{back|front|integration}/…
if [[ -n "$DECOMPOSE" ]]; then
  resolve_args=(resolve-arm "$DECOMPOSE")
  [[ -n "$ROLE" ]] && resolve_args+=(--role "$ROLE")
  [[ "$TRACK_OPT" == "epic" || "$TRACK_OPT" == "program" ]] && resolve_args+=(--track "$TRACK_OPT")
  RESOLVE_JSON="$("${EPIC_RESOLVE[@]}" "${resolve_args[@]}")"
  ROLE="$(echo "$RESOLVE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["role"])')"
  RESOLVED_TRACK="$(echo "$RESOLVE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["track"])')"
  DECOMPOSE="$(echo "$RESOLVE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["decompose"])')"
  if [[ "$RESOLVED_TRACK" == "program" ]]; then
    [[ -z "$INTEG_DECOMPOSE" ]] && INTEG_DECOMPOSE="$(echo "$RESOLVE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("integ_decompose") or "")')"
    [[ -z "$PROGRAM_ID" ]] && PROGRAM_ID="$(echo "$RESOLVE_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["program_id"])')"
  fi
  echo "==> resolve path: role=$ROLE track=$RESOLVED_TRACK decompose=$DECOMPOSE"
  [[ -n "$PROGRAM_ID" ]] && echo "==> program id: $PROGRAM_ID"
fi

TRACK="$(detect_track)"
if [[ -z "$TRACK" ]]; then
  echo "cannot detect track — pass decompose id or --id / --gap" >&2
  usage >&2
  exit 2
fi
echo "==> track=$TRACK"

# epic needs a concrete role even when continuing an armed session
[[ -z "$ROLE" ]] && ROLE="BACK"

CLAUDE="$(find_claude)"
PERM_ARGS=(--permission-mode "$PERM_MODE")
MODEL_ARGS=()
[[ -n "$MODEL" ]] && MODEL_ARGS=(--model "$MODEL")

run_claude_session() {
  local state_dir="$1"
  local iter="$2"
  local prompt_file="$3"
  local log_file="$state_dir/session-${iter}.log"
  local prompt
  prompt="$(cat "$prompt_file")"

  if [[ "$HEADLESS" == "1" ]]; then
    echo "==> headless → $log_file"
    set +e
    "$CLAUDE" -p \
      --output-format stream-json \
      --include-partial-messages \
      --verbose \
      "$prompt" \
      "${PERM_ARGS[@]}" "${MODEL_ARGS[@]}" "${EXTRA_ARGS[@]}" \
      2>&1 | tee "$log_file" | python3 "$STREAM_FILTER"
    local rc=${PIPESTATUS[0]}
    set -e
    return "$rc"
  fi
  echo "==> interactive — /exit after FINISH"
  set +e
  "$CLAUDE" "$prompt" "${PERM_ARGS[@]}" "${MODEL_ARGS[@]}" "${EXTRA_ARGS[@]}"
  local rc=$?
  set -e
  return "$rc"
}

# ---------- EPIC TRACK ----------
run_epic_track() {
  local max_n="${MAX_ITER:-${EPIC_MAX:-40}}"
  local arm_args=()
  [[ -n "$MODEL" ]] && arm_args+=(--model "$MODEL")
  [[ -n "$FROM_STEP" ]] && arm_args+=(--from-step "$FROM_STEP")
  [[ "$FORCE_IMPLEMENT" == "1" ]] && arm_args+=(--force-implement)

  if [[ -n "$DECOMPOSE" ]]; then
    echo "==> arm epic: $DECOMPOSE (role=$ROLE max=$max_n model=${MODEL:-unset})"
    "${EPIC_RESOLVE[@]}" arm "$DECOMPOSE" --role "$ROLE" --max "$max_n" "${arm_args[@]}"
  fi

  local status
  status="$("${EPIC_RESOLVE[@]}" status)"
  if [[ "${VERBOSE}" == "1" || "${EPIC_VERBOSE:-0}" == "1" ]]; then
    echo "$status"
  else
    echo "$status" | python3 -c 'import json,sys; s=json.load(sys.stdin); print("==> epic active:", s.get("active"), "status:", s.get("status"), "model:", s.get("model"))'
  fi
  echo "$status" | python3 -c 'import json,sys; s=json.load(sys.stdin); assert s.get("active"), "epic not armed — pass decompose id"'

  if [[ -z "$MODEL" ]]; then
    MODEL="$(echo "$status" | python3 -c 'import json,sys; s=json.load(sys.stdin); print(s.get("model") or "")')"
    [[ -n "$MODEL" ]] && MODEL_ARGS=(--model "$MODEL")
  fi
  echo "==> claude=$CLAUDE epic model=${MODEL:-default}"

  local iter=0
  while true; do
    iter=$((iter + 1))
    echo ""
    echo "======== EPIC SESSION $iter ========"
    set +e
    local resolve_json rc
    resolve_json="$("${EPIC_RESOLVE[@]}" resolve 2>&1)"
    rc=$?
    set -e
    if [[ "${VERBOSE}" == "1" || "${EPIC_VERBOSE:-0}" == "1" ]]; then
      echo "$resolve_json"
    else
      echo "$resolve_json" | python3 -c '
import json,sys
r=json.load(sys.stdin)
print("==> next command:", r.get("command"))
if r.get("pending_steps") is not None: print("==> pending steps:", r.get("pending_steps"))
if r.get("reason"): print("==> reason:", r.get("reason"))
' 2>/dev/null || echo "$resolve_json"
    fi
    if [[ $rc -eq 3 ]]; then
      echo "==> EPIC COMPLETE"
      return 0
    fi
    if [[ $rc -ne 0 ]]; then
      echo "==> EPIC HALTED (resolve rc=$rc)"
      "${EPIC_RESOLVE[@]}" status
      return "$rc"
    fi

    local prompt_file="$EPIC_STATE_DIR/next-prompt.txt"
    [[ -f "$prompt_file" ]] || { echo "missing $prompt_file" >&2; return 1; }
    echo "==> prompt (first lines):"
    sed -n '1,8p' "$prompt_file"
    echo "..."

    set +e
    run_claude_session "$EPIC_STATE_DIR" "$iter" "$prompt_file"
    local claude_rc=$?
    set -e
    echo "==> claude exit=$claude_rc"
    local session_log="$EPIC_STATE_DIR/session-${iter}.log"
    set +e
    local rec_json rec_rc
    rec_json="$("${EPIC_RESOLVE[@]}" record-session --log "$session_log" --exit-code "$claude_rc" --track epic 2>&1)"
    rec_rc=$?
    set -e
    if [[ $rec_rc -ne 0 ]]; then
      echo "==> SESSION ABORTED (record-session rc=$rec_rc) — skip after"
      echo "$rec_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print("==> abort:", r.get("reason"), "halted=", r.get("halted"))' 2>/dev/null || echo "$rec_json"
      "${EPIC_RESOLVE[@]}" status
      return "$rec_rc"
    fi

    set +e
    local after_json after_rc
    after_json="$("${EPIC_RESOLVE[@]}" after 2>&1)"
    after_rc=$?
    set -e
    if [[ "${VERBOSE}" == "1" ]]; then
      echo "$after_json"
    else
      echo "$after_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print("==> after:", r.get("status"), r.get("reason"))' 2>/dev/null || echo "$after_json"
    fi

    # Up to EPIC_RESULT_REPAIR_MAX_ATTEMPTS repair sessions for fixable result.yaml / step-format failures
    while [[ $after_rc -ne 0 && $after_rc -ne 3 ]]; do
      local repairable
      repairable="$(echo "$after_json" | python3 -c '
import json,sys
try:
    r=json.load(sys.stdin)
except Exception:
    print("0"); raise SystemExit(0)
print("1" if r.get("repairable") else "0")
' 2>/dev/null || echo 0)"
      [[ "$repairable" == "1" ]] || break

      local reason
      reason="$(echo "$after_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r.get("reason") or "")' 2>/dev/null || true)"
      local attempt_hint
      attempt_hint="$(echo "$after_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r.get("repair_attempt") or 0)' 2>/dev/null || echo 0)"
      echo "==> after repairable — RESULT REPAIR session (next attempt after ${attempt_hint})"
      set +e
      local repair_json repair_rc
      repair_json="$("${EPIC_RESOLVE[@]}" prepare-repair --reason "$reason" 2>&1)"
      repair_rc=$?
      set -e
      echo "$repair_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print("==> prepare-repair:", r.get("ok"), "attempt=", r.get("repair_attempt"), r.get("reason"))' 2>/dev/null || echo "$repair_json"
      [[ $repair_rc -eq 0 ]] || break

      local repair_prompt="$EPIC_STATE_DIR/next-prompt.txt"
      set +e
      run_claude_session "$EPIC_STATE_DIR" "${iter}-repair-${attempt_hint}" "$repair_prompt"
      local repair_claude_rc=$?
      set -e
      echo "==> repair claude exit=$repair_claude_rc"
      local repair_log="$EPIC_STATE_DIR/session-${iter}-repair-${attempt_hint}.log"
      set +e
      local repair_rec_json repair_rec_rc
      repair_rec_json="$("${EPIC_RESOLVE[@]}" record-session --log "$repair_log" --exit-code "$repair_claude_rc" --track epic 2>&1)"
      repair_rec_rc=$?
      set -e
      if [[ $repair_rec_rc -ne 0 ]]; then
        echo "==> REPAIR SESSION ABORTED"
        echo "$repair_rec_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print("==> abort:", r.get("reason"))' 2>/dev/null || echo "$repair_rec_json"
        "${EPIC_RESOLVE[@]}" status
        return "$repair_rec_rc"
      fi
      set +e
      after_json="$("${EPIC_RESOLVE[@]}" after 2>&1)"
      after_rc=$?
      set -e
      if [[ "${VERBOSE}" == "1" ]]; then
        echo "$after_json"
      else
        echo "$after_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print("==> after(repair):", r.get("status"), r.get("reason"))' 2>/dev/null || echo "$after_json"
      fi
    done

    if [[ $after_rc -eq 3 ]]; then
      echo "==> EPIC COMPLETE"
      return 0
    fi
    if [[ $after_rc -ne 0 ]]; then
      echo "==> EPIC HALTED (after rc=$after_rc)"
      "${EPIC_RESOLVE[@]}" status
      return "$after_rc"
    fi
  done
}

# ---------- PROGRAM TRACK ----------
run_program_track() {
  local max_n="${MAX_ITER:-80}"
  if [[ -n "$PROGRAM_ID" ]]; then
    local arm_args=(arm --id "$PROGRAM_ID" --phase "$PHASE" --max "$max_n")
    [[ -n "$INTEG_DECOMPOSE" ]] && arm_args+=(--integ-decompose "$INTEG_DECOMPOSE")
    [[ -n "$INTEG_PLAN" ]] && arm_args+=(--integ-plan "$INTEG_PLAN")
    [[ -n "$GAP" ]] && arm_args+=(--gap "$GAP")
    [[ -n "$RESUME_IMPL" ]] && arm_args+=(--resume-implement "$RESUME_IMPL")
    [[ -n "$MODEL" ]] && arm_args+=(--model "$MODEL")
    echo "==> arm program: $PROGRAM_ID phase=$PHASE"
    "${PROG_RESOLVE[@]}" "${arm_args[@]}"
  fi

  local status
  status="$("${PROG_RESOLVE[@]}" status)"
  echo "$status" | python3 -c 'import json,sys; s=json.load(sys.stdin); print("==> program active:", s.get("active"), "status:", s.get("status"), "phase:", s.get("phase")); assert s.get("active"), "program not armed — pass --id …"'

  if [[ -z "$MODEL" ]]; then
    MODEL="$(echo "$status" | python3 -c 'import json,sys; s=json.load(sys.stdin); print(s.get("model") or "")')"
    [[ -n "$MODEL" ]] && MODEL_ARGS=(--model "$MODEL")
  fi
  echo "==> claude=$CLAUDE program model=${MODEL:-default}"

  local iter=0
  while true; do
    iter=$((iter + 1))
    echo ""
    echo "======== PROGRAM SESSION $iter ========"
    set +e
    local resolve_json rc
    resolve_json="$("${PROG_RESOLVE[@]}" resolve 2>&1)"
    rc=$?
    set -e
    if [[ "${VERBOSE}" == "1" ]]; then
      echo "$resolve_json"
    else
      echo "$resolve_json" | python3 -c '
import json,sys
r=json.load(sys.stdin)
a=r.get("action") or {}
print("==> phase:", r.get("phase"))
print("==> action:", a.get("kind"), a.get("command"), a.get("reason"))
if a.get("decompose"): print("==> decompose:", a.get("decompose"))
if a.get("gap_id"): print("==> gap_id:", a.get("gap_id"))
' 2>/dev/null || echo "$resolve_json"
    fi
    if [[ $rc -eq 3 ]]; then
      echo "==> PROGRAM COMPLETE"
      return 0
    fi
    if [[ $rc -ne 0 ]]; then
      echo "==> PROGRAM HALTED (resolve rc=$rc)"
      "${PROG_RESOLVE[@]}" status
      return "$rc"
    fi

    local kind role_n dec
    kind="$(echo "$resolve_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print((r.get("action") or {}).get("kind") or "")')"
    role_n="$(echo "$resolve_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print((r.get("action") or {}).get("role") or "BACK")')"
    dec="$(echo "$resolve_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print((r.get("action") or {}).get("decompose") or "")')"

    local after_json after_rc
    if [[ "$kind" == "epic" ]]; then
      [[ -n "$dec" ]] || { echo "epic action without decompose" >&2; return 1; }
      echo "==> nested epic track role=$role_n decompose=$dec"
      # nested: temporarily set DECOMPOSE/ROLE and run epic until complete
      local saved_dec="$DECOMPOSE" saved_role="$ROLE"
      DECOMPOSE="$dec"
      ROLE="$role_n"
      set +e
      run_epic_track
      local epic_rc=$?
      set -e
      DECOMPOSE="$saved_dec"
      ROLE="$saved_role"
      echo "==> nested epic exit=$epic_rc"
      if [[ $epic_rc -eq 130 ]] || [[ $epic_rc -eq 143 ]]; then
        "${PROG_RESOLVE[@]}" halt --reason 'user interrupt (Ctrl+C)'
        return "$epic_rc"
      fi
      local epic_status=complete
      [[ $epic_rc -ne 0 ]] && epic_status=halted
      set +e
      after_json="$("${PROG_RESOLVE[@]}" after --epic-status "$epic_status" 2>&1)"
      after_rc=$?
      set -e
    else
      local prompt_file="$PROG_STATE_DIR/next-prompt.txt"
      [[ -f "$prompt_file" ]] || { echo "missing $prompt_file" >&2; return 1; }
      echo "==> prompt (first lines):"
      sed -n '1,8p' "$prompt_file"
      echo "..."
      set +e
      run_claude_session "$PROG_STATE_DIR" "$iter" "$prompt_file"
      local mode_rc=$?
      set -e
      echo "==> mode exit=$mode_rc"
      local prog_log="$PROG_STATE_DIR/session-${iter}.log"
      set +e
      local prog_rec_json prog_rec_rc
      prog_rec_json="$("${EPIC_RESOLVE[@]}" record-session --log "$prog_log" --exit-code "$mode_rc" --track program 2>&1)"
      prog_rec_rc=$?
      set -e
      if [[ $prog_rec_rc -ne 0 ]]; then
        echo "==> PROGRAM SESSION ABORTED"
        echo "$prog_rec_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print("==> abort:", r.get("reason"))' 2>/dev/null || echo "$prog_rec_json"
        "${PROG_RESOLVE[@]}" halt --reason "session aborted (see last-session.json)"
        return "$prog_rec_rc"
      fi
      set +e
      after_json="$("${PROG_RESOLVE[@]}" after 2>&1)"
      after_rc=$?
      set -e
    fi

    if [[ "${VERBOSE}" == "1" ]]; then
      echo "$after_json"
    else
      echo "$after_json" | python3 -c 'import json,sys; r=json.load(sys.stdin); print("==> after:", r.get("status"), "phase=", r.get("phase"), r.get("reason"))' 2>/dev/null || echo "$after_json"
    fi
    if [[ $after_rc -eq 3 ]]; then
      echo "==> PROGRAM COMPLETE"
      return 0
    fi
    if [[ $after_rc -ne 0 ]]; then
      echo "==> PROGRAM HALTED (after rc=$after_rc)"
      "${PROG_RESOLVE[@]}" status
      return "$after_rc"
    fi
  done
}

if [[ "$TRACK" == "program" ]]; then
  run_program_track
else
  run_epic_track
fi
