FLAKE8?=	flake8
MYPY?=		mypy
BLACK?=		black

FLAKE8_ARGS+=	--ignore=D10,E501
FLAKE8_ARGS+=	--max-line-length 88  # same as black
MYPY_ARGS+=	--strict --ignore-missing-imports
BLACK_ARGS=	--skip-string-normalization

lint:: flake8 mypy black

flake8:
	${FLAKE8} ${FLAKE8_ARGS} repology-linkchecker.py linkchecker

mypy:
	${MYPY} ${MYPY_ARGS} repology-linkchecker.py

black:
	${BLACK} ${BLACK_ARGS} --check repology-linkchecker.py linkchecker/**/*.py

black-reformat:
	${BLACK} ${BLACK_ARGS} repology-linkchecker.py linkchecker/*.py linkchecker/*/*.py
