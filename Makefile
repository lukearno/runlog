pyversion=2.7
export
clean:
	rm coverage.xml -f
	rm .coverage -f
	rm full-test-coverage-html -rf
	rm .virts -rf
	rm -f *.pyc */*.pyc
develop:
	mkdir -p .virts/
	virtualenv .virts/dev
	. .virts/dev/bin/activate && pip install -i 'http://pypi.python.org/simple' -r dev-requirements.txt > /dev/null
	. .virts/dev/bin/activate && pip install -e '.' > /dev/null
test-python:
	virtualenv .virts/$(pyversion) --python=python$(pyversion)
	. .virts/$(pyversion)/bin/activate && pip install -i 'http://pypi.python.org/simple' -r dev-requirements.txt > /dev/null
	. .virts/$(pyversion)/bin/activate && pip install -e '.' > /dev/null
	. .virts/$(pyversion)/bin/activate && nosetests -xs tests/
stylecheck:
	. .virts/dev/bin/activate && flake8 runlog tests --max-complexity=12 && echo "\nStyle checks passed.\n"
test:
	PYTHONWARNINGS=d . .virts/dev/bin/activate && nosetests -xs \
	--with-coverage --cover-package runlog \
	--cover-html --cover-html-dir coverage-html tests/
viewcoverage:
	. .virts/dev/bin/activate && static localhost 6897 coverage-html
fulltest: clean develop test stylecheck
