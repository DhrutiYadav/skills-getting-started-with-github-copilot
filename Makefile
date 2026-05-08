VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
UVICORN=$(VENV)/bin/uvicorn
APP_MODULE=src.app:app

.PHONY: help venv install run clean

help:
	@echo "Available targets:"
	@echo "  make venv      - create a Python virtual environment"
	@echo "  make install   - install dependencies from requirements.txt"
	@echo "  make run       - run the FastAPI app with uvicorn"
	@echo "  make clean     - remove the virtual environment"

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt

run: install
	$(UVICORN) $(APP_MODULE) --reload

clean:
	rm -rf $(VENV)
