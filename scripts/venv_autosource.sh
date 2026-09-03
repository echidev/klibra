#!/usr/bin/env bash
# scripts/venv_autosource.sh
# Source this file from ~/.bashrc (or per-repo) to auto-activate KLIBRA venv
# when a shell lands in the repo tree. Idempotent, safe to source repeatedly,
# and short-circuits outside the repo.
#
# Recommended install:
#   echo "source /path/to/klibra/scripts/venv_autosource.sh" >> ~/.bashrc
#
# Behavior:
#   - If $PWD is inside the repo (or any descendant), activate venv/.
#   - If venv/ is missing, create it (no pip install) and then activate.
#   - Outside the repo: do nothing. Do not re-activate.
#   - Never prints venv contents; never sources .env.
#   - Never re-sources itself in a way that double-activates ($VIRTUAL_ENV guard).
#
# No secrets are read. No requirements.txt is installed by this script.

# Resolve the repo root from the location of THIS script.
_klibra_script_dir="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
_klibra_repo_root="$( cd -- "${_klibra_script_dir}/.." &> /dev/null && pwd )"
_klibra_venv_dir="${_klibra_repo_root}/venv"
_klibra_marker="${_klibra_repo_root}/.git"   # repo root signal
# Guard: only run if the script lives in the actual repo.
if [[ ! -e "${_klibra_marker}" ]]; then
    return 0 2>/dev/null || exit 0
fi

# Guard: only activate if PWD is inside (or equal to) the repo tree.
# This makes the script per-repo without manual editing of ~/.bashrc.
case "$PWD" in
    "${_klibra_repo_root}") ;;                # exact match
    "${_klibra_repo_root}"/*) ;;              # descendant
    *) return 0 2>/dev/null || exit 0 ;;     # outside the repo
esac

# Guard: avoid double-activation in the same shell.
if [[ "$VIRTUAL_ENV" == "${_klibra_venv_dir}" ]]; then
    return 0 2>/dev/null || exit 0
fi

# Create venv if missing. Do NOT install requirements.txt.
if [[ ! -d "${_klibra_venv_dir}" ]]; then
    if command -v python3 >/dev/null 2>&1; then
        python3 -m venv "${_klibra_venv_dir}" >/dev/null 2>&1 || {
            printf 'klibra: failed to create venv at %s\n' "${_klibra_venv_dir}" >&2
            return 0 2>/dev/null || exit 0
        }
    else
        printf 'klibra: python3 not found; cannot create venv\n' >&2
        return 0 2>/dev/null || exit 0
    fi
fi

# Activate venv if available. Never expose secret files.
if [[ -f "${_klibra_venv_dir}/bin/activate" ]]; then
    # shellcheck disable=SC1090
    source "${_klibra_venv_dir}/bin/activate"

    export KLIBRA_VENV="${_klibra_venv_dir}"
    export KLIBRA_REPO_ROOT="${_klibra_repo_root}"

    # Quiet confirmation. Comment out to silence.
    if [[ -n "${PS1:-}" ]]; then
        printf '🐍 klibra venv active: %s\n' "${_klibra_venv_dir}"
    fi
else
    printf 'klibra: venv found but activate script missing: %s\n' "${_klibra_venv_dir}" >&2
fi

unset _klibra_script_dir _klibra_repo_root _klibra_venv_dir _klibra_marker
