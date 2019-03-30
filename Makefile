FLAKE8?=	flake8
MYPY?=		mypy

MYPY_ARGS+=	--strict --ignore-missing-imports

lint:: flake8 mypy

flake8:
	${FLAKE8} repology-linkchecker.py linkchecker

mypy:
	${MYPY} ${MYPY_ARGS} repology-linkchecker.py
