test:
	pytest tests --cov

lint:
	mypy mailer
	pylint mailer tests

format:
	black mailer tests
	isort mailer tests

clean:
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -f .coverage

full: clean format lint test