# Anti-FOMO Docker Makefile

.PHONY: help build up down restart logs logs-api logs-web clean

help:
	@echo "Anti-FOMO Docker Commands"
	@echo ""
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart   - Restart all services"
	@echo "  make logs       - View all logs"
	@echo "  make logs-api   - View API logs"
	@echo "  make logs-web   - View Web logs"
	@echo "  make clean      - Remove all containers and volumes"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo ""
	@echo "Services started:"
	@echo "  - API:  http://localhost:8000"
	@echo "  - Web:  http://localhost:3000"
	@echo "  - Docs: http://localhost:8000/docs"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-web:
	docker-compose logs -f web

clean:
	docker-compose down -v
	@echo "All containers and volumes removed"
