#!/usr/bin/env bash

set -euo pipefail

: "${MTG_HOME:=$HOME/.cardkingdom}"
: "${PYTHON_3:=$(command -v python3.11)}"
: "${VENV_DIR:=$(dirname "$0" )/env}"

function _venv {
	[[ -d "$VENV_DIR" ]] || "$PYTHON_3" -m venv "$VENV_DIR"

	# shellcheck disable=SC1091
	source "$VENV_DIR/bin/activate"
	pip3 install -U pip -r requirements.txt 1>&2 >/dev/null
}

function _main {
	local -r LOG_FILE="log/mtg_wishlist_$(date +%Y-%m-%dT%H_%M_%S).log"
	env MTG_COOKIE="$(./login.py)" ./mtg.py wishlist > "$LOG_FILE" 2>&1
}

( cd "$MTG_HOME" ; mkdir -p log && _venv && _main "$@" )
