run: requirements
	python app/app.py

requirements:
	pip install -r requirements.txt

build:
	docker build -t onboard .