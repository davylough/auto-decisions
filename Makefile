SHELL=/bin/bash
.DEFAULT_GOAL := info

# Variables from the cookiecutter template. You shouldn't change these... ever.
PROJECT := auto-decisions
REGISTRY := 492572841545.dkr.ecr.us-east-1.amazonaws.com
# Variables inffered by the environment
GIT_HASH := $(shell git rev-parse --short HEAD)
# These variables have defaults for local development, but can be overwritten using environment variables.
# For example, to push to the production domain, you can to `make DOMAIN=prod push`
VERSION ?= dev-$(GIT_HASH)
DOMAIN ?= dev
# A few other helpful variables
AWS_PROFILE:=$(shell if [[ -f ~/.aws/config ]] && grep -q "ml-platform-curalate-prod" ~/.aws/config ; then echo "--profile ml-platform-curalate-prod" ; else echo "" ; fi)
AWS_REGION := --region us-east-1
PROJECT_DESCRIPTION := $(if $(PROJECT_DESCRIPTION),$(PROJECT_DESCRIPTION),Project $(PROJECT) created via cookiecutter)
IMG:=$(REGISTRY)/$(PROJECT):$(VERSION)
BUILDER_NAME := $(PROJECT)-builder

#
# ------------  Useful Helper Targets --------
# These shouldn't be called directly but help optimize some use cases below.
#

# We use code artifact in the curalate-prod account for python packages that we write. 
# The .codeartifact-token file is phony here so that it is always re-created -- we want the latest token each time.
.PHONY: .codeartifact-token
.codeartifact-token:
	@aws $(AWS_REGION) $(AWS_PROFILE) codeartifact get-authorization-token --domain curalate-ml --domain-owner 492572841545 --query authorizationToken --output text > .codeartifact-token

# We'll version your container using the git hash -- so we need to ensure you commit all changes before sending it up to flyte.
# This target will fail if there are un committed changes.
.PHONY: .check-version
.check-version:
	@git diff-index --quiet HEAD || ( >&2 echo "❗️❗️ There are unsaved commits -- please commit your changes before building"; exit 1)

# Target for the packaged file.
flyte-package.tgz: build
	pyflyte --config flytekit.config package --image $(IMG) -f
	@echo "✅ Packaged project into $@"


# Builds the docker image. The .dockerbuild- is used to mark the image as complete.
.dockertrack/dockerbuild-%: Dockerfile Pipfile src $(shell find src -type f -name "*.py")
	mkdir -p .dockertrack
	DOCKER_BUILDKIT=1 docker build --platform linux/amd64 --secret id=codeartifact-token,src=$(shell pwd)/.codeartifact-token -t $(IMG) .
	@touch $@
	@echo "✅ Image $(IMG) built."

# Pushes a docker image to the ecr repo
.dockertrack/dockerpush-%: .dockertrack/dockerbuild-%
	mkdir -p .dockertrack
	AWS_PROFILE=ml-platform-curalate-prod docker push $(IMG)
	@touch $@
	@echo "✅ Image $(IMG) pushed to ECR."

# Builds the multi-arch docker image.
.dockertrack/multi-dockerbuild-%: Dockerfile Pipfile src $(shell find src -type f -name "*.py")
	mkdir -p .multi-dockertrack
	DOCKER_BUILDKIT=1 docker buildx use $(BUILDER_NAME)
	DOCKER_BUILDKIT=1 docker buildx build --platform linux/arm64/v8,linux/amd64 --secret id=codeartifact-token,src=$(shell pwd)/.codeartifact-token -t $(IMG) --push .
	@touch $@
	@echo "✅ Multi-arch image $(IMG) built and pushed."

#
# ------------ User Commands --------
# Each command below is provided for the user. They should all be phony, but may have side effects 
#

.PHONY: info init build push package register runcmd test code_style promote clean


# Prints info about this project
info:
	$(info Project: $(PROJECT))
	$(info Description: $(PROJECT_DESCRIPTION))
	$(info Version: $(VERSION))
	$(info Domain: $(DOMAIN))
	flytectl get launchplan --project $(PROJECT) --domain $(DOMAIN)  --latest


# sets up your project in flyte and creates the ecr repository for your project's docker container.
init:
	$(info Creating initial flyte project....)
	flytectl create project --name $(PROJECT) --id $(PROJECT)  --description "$(PROJECT_DESCRIPTION)"
	$(info Creating docker repository AWS Curalate Prod....)
	aws $(AWS_REGION) $(AWS_PROFILE) ecr create-repository --repository-name $(PROJECT)
	$(info Creating docker builder....)
	docker buildx create --name $(BUILDER_NAME)
	@echo "✅ Project $(PROJECT) initialized."


# Builds the docker image for the current version
build: .codeartifact-token .check-version .dockertrack/dockerbuild-$(VERSION)

# Builds the mult-arch docker image for the current version
build_multi: .codeartifact-token .check-version .dockertrack/multi-dockerbuild-$(VERSION)

# Push your docker image to ECR
push: build .dockertrack/dockerpush-$(VERSION)


# Creates the flyte package for this project
package: flyte-package.tgz


# Registers this project with flyte
register: flyte-package.tgz
	flytectl register files --archive flyte-package.tgz --version $(VERSION) --project $(PROJECT) --domain $(DOMAIN)
	@echo "✅ Project $(PROJECT) version $(VERSION) registered in domain $(DOMAIN)"


# This target generates a run command to be used for remote execution (it specifies the domain and the project)
runcmd: push
	@echo pyflyte --config flytekit.config run -p $(PROJECT) -d $(DOMAIN) -i $(IMG)

# Runs any tests for the code
test:
	pytest tests

# Updates the code with our style conventions
code_style:
	@echo Applying Black formatting....
	black src tests
	@echo Applying Flake8 style check....
	flake8
	@echo "✅ Code linting complete"


# removes make-related marker files to force a rebuild
clean:
	rm -rf .dockertrack
