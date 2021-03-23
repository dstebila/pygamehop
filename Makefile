MYPY ?= 'mypy'
PYTEST ?= 'pytest'
PYTHON ?= 'python3.9'
all:


# eventually just replace this with
# env PYTHONPATH=. pytest -v --mypy
test: typecheck_library unittest_library test_examples

typecheck_library:
	$(MYPY) -p gamehop.inlining
	$(MYPY) -p gamehop.verification
	# $(MYPY) -p gamehop.primitives

unittest_library:
	env PYTHONPATH=. $(PYTEST) -v

test_examples:
	env PYTHONPATH=. $(PYTHON) gamehop/app.py examples/KEMfromPKE
	env PYTHONPATH=. $(PYTHON) gamehop/app.py examples/stupiddoublePKE

devtest:
	env PYTHONPATH=. $(PYTEST) -v devtests/*
