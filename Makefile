MAVEN=mvn
DOCKER_IMAGE?=us.gcr.io/mvp-demo-301906/kfuse/synthetic-load-generator
BUILD_NUMBER?=latest

.PHONY: all build publish
all: build publish
build: java-jars docker-build

.PHONY: java-jars
java-jars: # Create jars without running tests.
	@echo "\n===== $@ ======"
	# Ensure required dependencies are met
	@$(call --check-dependencies,${MAVEN})
	$(MAVEN) package -DskipTests

.PHONY: docker-build
docker-build:
	@echo "\n===== $@ ======"
	envsubst < Dockerfile | docker build --platform linux/amd64 --pull -t ${DOCKER_IMAGE}:${BUILD_NUMBER} -f - .
	docker push ${DOCKER_IMAGE}:${BUILD_NUMBER}

