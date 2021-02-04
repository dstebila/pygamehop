MYPY ?= 'mypy'
PYTEST ?= 'pytest'
all:


# eventually just replace this with
# env PYTHONPATH=. pytest -v --mypy
test: typecheck_library unittest_library

typecheck_library:
	$(MYPY) -p gamehop.inlining
	$(MYPY) -p gamehop.primitives

unittest_library:
	env PYTHONPATH=. $(PYTEST) -v

devtest:
	env PYTHONPATH=. $(PYTEST) -v devtests/*
