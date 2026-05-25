# Default `make run` launches the Streamlit demo (the actual portfolio piece).
# The legacy FastAPI ICAM agent is preserved under `app/` and can be started
# with `make run-legacy`.

run:
	streamlit run cleared-identity-copilot/app.py

run-legacy:
	uvicorn app.main:app --reload --port 8080

seed:
	python scripts/seed_synthetic.py

test:
	pytest -q
