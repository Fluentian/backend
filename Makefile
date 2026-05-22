install:
	pip install -e ".[dev]"

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

makemigration:
	alembic revision --autogenerate -m "$(msg)"

rollback:
	alembic downgrade -1

test:
	pytest tests/ -v --asyncio-mode=auto

lint:
	ruff check app/ && mypy app/

format:
	ruff format app/

shell:
	python -c "import asyncio; from app.database import engine; from sqlalchemy import select; from app.models import User; async def run(): async with engine.connect() as c: print((await c.execute(select(1))).scalar()); asyncio.run(run())"

docker-up:
	docker-compose up -d postgres redis

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
