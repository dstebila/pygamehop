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
	$(MYPY) --ignore-missing-imports -p gamehop

unittest_library:
#	env PYTHONPATH=. $(PYTEST) -v tests/gamehop

test_examples:
	env PYTHONPATH=. $(PYTEST) -v tests/examples

devtest:
	env PYTHONPATH=. $(PYTEST) -v devtests/*

example_figures:
	cd examples/PKEfromKEM && pdflatex PKEfromKEM_is_INDCPA.tex
	convert -density 144 examples/PKEfromKEM/PKEfromKEM_is_INDCPA.pdf docs/images/PKEfromKEM_is_INDCPA.png
	cd examples/KEMfromPKE && pdflatex KEMfromPKE_is_INDCPA.tex
	convert -density 144 examples/KEMfromPKE/KEMfromPKE_is_INDCPA.pdf docs/images/KEMfromPKE_is_INDCPA.png
	cd examples/parallelPKE && pdflatex parallelPKE_is_INDCPA.tex
	convert -density 144 examples/parallelPKE/parallelPKE_is_INDCPA.pdf docs/images/parallelPKE_is_INDCPA.png
	cd examples/nestedPKE && pdflatex nestedPKE_is_INDCPA_proof1.tex
	cd examples/nestedPKE && pdflatex nestedPKE_is_INDCPA_proof2.tex
	convert -density 144 examples/nestedPKE/nestedPKE_is_INDCPA_proof1.pdf docs/images/nestedPKE_is_INDCPA_proof1.png
	convert -density 144 examples/nestedPKE/nestedPKE_is_INDCPA_proof2.pdf docs/images/nestedPKE_is_INDCPA_proof2.png
	rm -f examples/*/*.aux
	rm -f examples/*/*.log
