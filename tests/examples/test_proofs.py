import subprocess
import sys
import unittest

def run_example(name, property):
    subprocess.run(
        [sys.executable, "examples/" + name + "/" + name + "_is_" + property + ".py"],
        check=True
    )

class TestProofs(unittest.TestCase):
    def oldtest_KEMfromPKE_is_INDCPA(self): run_example("KEMfromPKE", "INDCPA")
    def oldtest_parallelPKE_is_INDCPA(self): run_example("parallelPKE", "INDCPA")
    def oldtest_nestedPKE_is_INDCPA(self): run_example("nestedPKE", "INDCPA")
    def oldtest_PKEfromKEM_is_INDCPA(self): run_example("PKEfromKEM", "INDCPA")
    def test_placeholder(self): return True # needed temporarily because pytest fails if there are no tests
