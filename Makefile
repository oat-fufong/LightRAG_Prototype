HOST_PORT=9126
PORT=9126
CONTAINER_NAME=lightrag:test

help:
	@echo make build        - Build docker image
	@echo make run        	- Start docker container
	@echo make env 					- Check if .env exists 
	@echo make clean				- Clean repository

env:
	@if [ -f .env ]; then \
			echo ".env file found: $$(pwd)/.env"; \
	else \
			echo "No .env file found"; \
			echo "Create one: cp .env.example .env"; \
	fi

build-%:
	docker build -t $* .

run:
	@printenv > ./.env.override
	docker run --rm --env-file .env --env-file .env.override -p $(HOST_PORT):$(PORT) $(CONTAINER_NAME) 
	@rm .env.override

clean:
	@echo "Cleaning"

