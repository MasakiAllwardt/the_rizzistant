# Makefile for The Rizzistant

IMAGE_NAME = the_rizzistant
CONTAINER_NAME = the_rizzistant-app
PORT = 8000

.PHONY: build start dev stop logs clean

# Build Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Start Docker container
start: build
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker run -d --name $(CONTAINER_NAME) -p $(PORT):$(PORT) --env-file .env $(IMAGE_NAME)
	@echo "App running at: http://localhost:$(PORT)"

# Run in development mode (foreground with live logs)
dev: build
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker run --rm --name $(CONTAINER_NAME) -p $(PORT):$(PORT) --env-file .env $(IMAGE_NAME)

# Stop container
stop:
	docker stop $(CONTAINER_NAME)

# View logs
logs:
	docker logs -f $(CONTAINER_NAME)

# Clean up
clean:
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@docker rmi $(IMAGE_NAME) 2>/dev/null || true
