.PHONY: run
SITE_PACKAGES := $(shell pip show pip | grep '^Location' | cut -d' ' -f2-)
run: $(SITE_PACKAGES)
	python3 app/app.py

$(SITE_PACKAGES): requirements.txt
	pip install -r requirements.txt
	touch requirements.txt

build_image:
	docker build -t ghcr.io/traefikturkey/onboard:latest .

push_image:
	docker push ghcr.io/traefikturkey/onboard