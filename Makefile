PYTHON_3 ?= $(shell command -v python3)
VENV_DIR ?= $(shell pwd)/env

test:
	@[[ -d '$(VENV_DIR)' ]] || make venv
	@echo 1>&2 '--- new Card Kingdom session...'
	@source '$(VENV_DIR)/bin/activate' ; ./login.py
	@echo 1>&2 '--- now try: ./wish.sh and check logs'
.PHONY: test

venv:
	'$(PYTHON_3)' -m venv '$(VENV_DIR)'
	source '$(VENV_DIR)/bin/activate' ; pip3 install -U pip -r requirements.txt
.PHONY: venv
