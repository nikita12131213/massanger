.PHONY: up down backend frontend migrate seed

up:
	docker compose up -d postgres redis

down:
	docker compose down -v

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python seed.py

backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev
