.PHONY: install install-dev run-api run-frontend run-all test lint format clean

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

run-api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	streamlit run frontend/app.py --server.port 8501

run-all:
	make run-api & make run-frontend

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

lint:
	black app/ frontend/ tests/ --check
	isort app/ frontend/ tests/ --check-only
	flake8 app/ frontend/ tests/

format:
	black app/ frontend/ tests/
	isort app/ frontend/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov