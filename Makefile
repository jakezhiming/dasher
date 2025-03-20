.PHONY: run proxy build run-web install clean format

run:
	python main.py

proxy:
	python web/proxy_server.py

build:
	python web/pygbag_build.py

run-web:
	python -m http.server --directory build/web

install:
	pip install -r requirements.txt

clean:
	rm -rf build/ logs/ leaderboard.db
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

format:
	black .