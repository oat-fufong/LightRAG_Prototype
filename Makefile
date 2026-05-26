HOST_PORT=9126
PORT=9126
CONTAINER_NAME=lightrag:test

# load .env as environment variable
ifneq (,$(wildcard .env))
    include .env
    export $(shell sed -n 's/^\([^#][^=]*\)=.*/\1/p' .env)
endif

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

build:
	docker build -t $(CONTAINER_NAME)  .

run:
	envsubst < .env.poc.template > .env.temp
	docker run --rm --env-file .env.temp -p $(HOST_PORT):$(PORT) $(CONTAINER_NAME) 

clean:
	@rm .env.temp


	

