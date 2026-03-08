.PHONY: up down down-all up-gpu down-gpu down-all-gpu build build-gpu logs ps

## CPU mode (default)
up:
	docker compose up -d --build

down:
	docker compose down

down-all:
	docker compose down -v

build:
	docker compose build

## GPU mode (requires NVIDIA GPU + nvidia-container-toolkit)
up-gpu:
	docker compose --env-file .env --env-file .env.gpu --profile gpu up -d --build

down-gpu:
	docker compose --profile gpu down

down-all-gpu:
	docker compose --profile gpu down -v

build-gpu:
	docker compose --env-file .env --env-file .env.gpu build

## Utilities
logs:
	docker compose logs -f

ps:
	docker compose ps -a
