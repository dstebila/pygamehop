MYPY ?= 'mypy'
PYTEST ?= 'pytest'
PYTHON ?= 'python3.9'
all:


# eventually just replace this with
# env PYTHONPATH=. pytest -v --mypy
test: typecheck_library unittest_library test_examples

typecheck_library:
	$(MYPY) --ignore-missing-imports -p gamehop.inlining
	$(MYPY) --ignore-missing-imports -p gamehop.verification
	$(MYPY) --ignore-missing-imports -p gamehop.primitives

unittest_library:
	env PYTHONPATH=. $(PYTEST) -v tests/gamehop

test_examples:
	env PYTHONPATH=. $(PYTEST) -v tests/examples

devtest:
	env PYTHONPATH=. $(PYTEST) -v devtests/*
