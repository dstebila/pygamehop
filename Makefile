all:


# eventually just replace this with
# env PYTHONPATH=. pytest -v --mypy
test: typecheck_library unittest_library

typecheck_library:
	mypy -p gamehop.inlining
	mypy -p gamehop.primitives

unittest_library:
	env PYTHONPATH=. pytest -v
