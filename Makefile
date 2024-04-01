.PHONY: run
SITE_PACKAGES := $(shell pip show pip | grep '^Location' | cut -d' ' -f2-)
run: $(SITE_PACKAGES)
	python3 app/app.py

$(SITE_PACKAGES): requirements.txt
	pip install -r requirements.txt
	touch requirements.txt


build-image:
	docker build --target production -t ghcr.io/traefikturkey/onboard:latest .

push-image: build-image
	docker push ghcr.io/traefikturkey/onboard

run-image: build-image
	docker run -it --rm -p 9830:9830 ghcr.io/traefikturkey/onboard:latest

ansible:
	LC_ALL=C.UTF-8 ansible-playbook --inventory 127.0.0.1 --connection=local .devcontainer/ansible/requirements.yml
	LC_ALL=C.UTF-8 ansible-playbook --inventory 127.0.0.1 --connection=local .devcontainer/ansible/setup-container.yml