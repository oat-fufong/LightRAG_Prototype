HTTP_PROXY ?= 'http://10.0.0.3:3128'
HTTPS_PROXY ?= 'http://10.0.0.3:3128'
NO_PROXY ?= 'localhost,127.0.0.1,metadata.google.internal'
LIGHTRAG_HOST_PORT ?= '9621'
LIGHTRAG_PORT ?= '9621'
CONTAINER_NAME ?= 'lightrag'
IMAGE_NAME ?= 'lightrag'
IMAGE_TAG ?= 'test'
HOST_INPUT_DIR ?= '/oat/home'
HOST_OUTPUT_DIR ?= '/oat/home'
CONTAINER_INPUT_DIR ?= '/workspace/input'

# load .env as environment variable
ifneq (,$(wildcard .env))
    include .env
    export $(shell sed -n 's/^\([^#][^=]*\)=.*/\1/p' .env)
endif

help:
	@echo make build        - Build docker image
	@echo make run        	- Start docker container
	@echo make env 					- Check if .env exists 
	@echo make clean				- Remove .env.temp

env:
	@if [ -f .env ]; then \
			echo ".env file found: $$(pwd)/.env"; \
	else \
			echo "No .env file found"; \
			echo "Create one: cp .env.example .env"; \
	fi

build:
	docker build \
		--build-arg HTTP_PROXY="$(HTTP_PROXY)" \
		--build-arg HTTPS_PROXY="$(HTTPS_PROXY)" \
		--build-arg NO_PROXY="$(NO_PROXY)" \
		-t $(IMAGE_NAME) .

run:
	envsubst < .env.poc.template > .env.temp

	# -d run docker in detached mode.
	# -rm automatically delete the container as soon as it stops running.
	docker run -d --rm \
		--env-file .env.temp \
		-v $(HOST_INPUT_DIR):$(CONTAINER_INPUT_DIR) \
		-v $(HOST_OUTPUT_DIR):$(CONTAINER_OUTPUT_DIR) \
		-p $(LIGHTRAG_HOST_PORT):$(LIGHTRAG_PORT) \
		--name $(CONTAINER_NAME) \
		$(IMAGE_NAME):$(IMAGE_TAG) \

stop:
	docker stop $(CONTAINER_NAME) || true

python:
	python3 main.py $(LIGHTRAG_HOST_PORT) 

clean: stop
	@rm -f .env.temp

copy:
	docker cp $(CONTAINER_NAME):/data $(HOST_OUTPUT_DIR)/$(IMAGE_TAG)
	


	

