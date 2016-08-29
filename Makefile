VERSION=$(shell cat slouch/_version.py | cut -d'"' -f2)

init:
	pip install -r requirements.txt

test:
	py.test tests

release:
	python setup.py sdist upload
	git tag -a $(VERSION)
	git push origin $(VERSION)
	git push
