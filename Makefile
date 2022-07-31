# lets try the new docker build system
# https://docs.docker.com/develop/develop-images/build_enhancements/
# https://www.docker.com/blog/faster-builds-in-compose-thanks-to-buildkit-support/
export DOCKER_BUILDKIT := 1
export DOCKER_SCAN_SUGGEST := false
export COMPOSE_DOCKER_CLI_BUILD := 1
export BUILDKIT_PROGRESS=plain

# include .env if present
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# get current timestamp
export DATE := $(shell date '+%Y-%m-%d-%H.%M.%S')
export PUID := $(shell id -u)
export PGID := $(shell id -g)

# get the project name from the current directory
export COMPOSE_INSTANCE := $(notdir $(shell pwd))
export PROJECT_NAME := $(word 1,$(subst -, ,COMPOSE_INSTANCE))

# get context from directory name after the dash ex: /apps/pharis-staging = staging
# if no dash default to development context
DIRECTORY_ENV_CONTEXT = $(word 2,$(subst -, ,$(COMPOSE_INSTANCE)))

export PASSED_COMMAND := $(firstword $(MAKECMDGOALS))
PASSED_ENV_CONTEXT := $(filter-out $(PASSED_COMMAND), $(lastword $(MAKECMDGOALS)))

POSSIBLE_CONTEXT := $(strip $(or $(PASSED_ENV_CONTEXT), $(DIRECTORY_ENV_CONTEXT)))
ifneq ("$(wildcard ./compose/docker-compose.$(POSSIBLE_CONTEXT).yml)","")
  # we found a possible context that matches a docker-compose file
  # so it really is a context 
	ENV_CONTEXT := $(POSSIBLE_CONTEXT)
else
	ENV_CONTEXT := development
endif

export DEPLOY_STAGE := $(or $(word 2,$(MAKECMDGOALS)),development)

# if username not set we are in a drone environment
export USERNAME := $(or $(USERNAME), $(USER), drone)
export EMAIL := $(or $(GIT_COMMITTER_EMAIL), $(shell git config user.email))

ifdef DRONE_REPO_BRANCH
	local_branch := $(DRONE_REPO_BRANCH)
else
	local_branch = $(shell git rev-parse --abbrev-ref HEAD | tr -d '\n')
endif

COMPOSE_COMMAND = docker compose

# order is important since these files are concatinated together
COMPOSE_FILES := ./compose/docker-compose.common.yml
COMPOSE_FILES += ./compose/docker-compose.$(ENV_CONTEXT).yml

# get the app name from the current directory
export DOCKER_HOST_PATH := $(or $(CURDIR), $(shell pwd))
export APP_NAME := $(or $(APP_NAME), $(notdir $(DOCKER_HOST_PATH)))
export APP_DOMAIN := $(or $(APP_DOMAIN), $(shell hostname -d 2>/dev/null), $(or $(DOCKER_NAMESPACE), ilude).com)
ifeq ($(ENV_CONTEXT),production)
	APP_FQDN := $(APP_NAME).$(APP_DOMAIN)
else
#$(APP_NAME)-$(ENV_CONTEXT).$(APP_DOMAIN)
	APP_FQDN := $(APP_NAME).$(APP_DOMAIN)
endif
export APP_FQDN
ATTACH_HOST := app

# use the rest as arguments as empty targets
EMPTY_TARGETS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
$(eval $(EMPTY_TARGETS):;@:)


up: build 
	-$(COMPOSE_COMMAND) $(FLAGS) up --force-recreate --abort-on-container-exit --remove-orphans
	$(MAKE) down

down: 
		$(COMPOSE_COMMAND) $(FLAGS) down
	-docker volume ls --quiet --filter "label=${APP_NAME}_${DEPLOY_STAGE}_project_volume_cleanup=down" | xargs -r docker volume rm

start: build 
	$(COMPOSE_COMMAND) $(FLAGS) up -d

restart: down start

test: build
	$(COMPOSE_COMMAND) $(FLAGS) run --rm $(ATTACH_HOST) bundle exec rspec

bash-run: build
	$(COMPOSE_COMMAND) $(FLAGS) run --rm $(ATTACH_HOST) bash -l

bash-exec: build
	$(COMPOSE_COMMAND) $(FLAGS) exec $(ATTACH_HOST) bash -l

clean: 
	docker-compose $(COMPOSE_FLAGS) down --volumes --remove-orphans --rmi local
	docker-compose $(COMPOSE_FLAGS) rm -f
	# ignore errors when cleaning up images
	docker image rm -f $(shell docker image ls -q --filter label=npi-project=${APP_NAME}-${ENV_CONTEXT}) > /dev/null 2>&1 || true
	# clear the builder cache layers
	docker builder prune -af
	# clean up assets:precompile caching
	-rm -rf public/assets
	-rm -rf tmp/cache

build: prepare-environment
	$(COMPOSE_COMMAND) $(FLAGS) build

prepare-environment: .env 


logs: build
	$(COMPOSE_COMMAND)  $(FLAGS) logs -f



env: 
	env | sort