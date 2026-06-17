.PHONY: install dev lint typecheck test clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

lint:
	ruff check src/

typecheck:
	mypy src/

test:
	pytest tests/ -v

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache __pycache__
	find . -name "*.pyc" -delete
