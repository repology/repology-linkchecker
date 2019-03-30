FLAKE8?=	flake8
MYPY?=		mypy

FLAKE8_ARGS+=	--ignore=D10,E501
MYPY_ARGS+=	--strict --ignore-missing-imports

lint:: flake8 mypy

flake8:
	${FLAKE8} ${FLAKE8_ARGS} repology-linkchecker.py linkchecker

mypy:
	${MYPY} ${MYPY_ARGS} repology-linkchecker.py
