.SUFFIXES:
SITE_PACKAGES := $(shell pip show pip | grep '^Location' | cut -d' ' -f2-)

# read and include .devcontainer/.env exporting all variables
ifneq (,$(wildcard .devcontainer/.env))
	include .devcontainer/.env
	export
endif

.PHONY: run reqs ansible
run: $(SITE_PACKAGES)
	python3 app/app.py

reqs:	$(SITE_PACKAGES)

$(SITE_PACKAGES): requirements.txt
	pip install -r requirements.txt
	-sudo touch $(SITE_PACKAGES)

ansible:
	sudo chown -R ${USER}:${USER} ~/
	-LC_ALL=C.UTF-8 ansible-playbook --inventory 127.0.0.1 --connection=local .devcontainer/ansible/setup-container.yml

build-image:
	docker build --target production -t ghcr.io/traefikturkey/onboard:latest .

push-image: build-image
	docker push ghcr.io/traefikturkey/onboard

run-image: build-image
	docker run -it --rm -p 9830:9830 -v /var/run/docker.sock:/var/run/docker.sock ghcr.io/traefikturkey/onboard:latest

bash-image: build-image
	docker run -it --rm -p 9830:9830 -v /var/run/docker.sock:/var/run/docker.sock ghcr.io/traefikturkey/onboard:latest bash
