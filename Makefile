HTTP_PROXY  ?=
HTTPS_PROXY ?=
NO_PROXY    ?=

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
		-p $(HOST_PORT):$(PORT) \
		--name $(CONTAINER_NAME) \
		$(IMAGE_NAME):$(IMAGE_TAG) \

stop:
	docker stop $(CONTAINER_NAME)

python:
	python3 main.py


clean:
	@rm -f .env.temp


	

