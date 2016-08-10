init:
	pip install -r requirements.txt

test:
	py.test tests

release:
	python setup.py sdist upload
