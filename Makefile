run:
	uvicorn app.main:app --reload --port 8080

seed:
	python scripts/seed_synthetic.py

test:
	pytest -q
