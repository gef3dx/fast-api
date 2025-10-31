help alembic

alembic revision --autogenerate -m "Create users table"
alembic upgrade head
alembic history
alembic downgrade 8ac14e223d1e