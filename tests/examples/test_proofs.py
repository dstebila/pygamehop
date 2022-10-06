import subprocess
import sys
import unittest

def run_example(name, property):
    subprocess.run(
        [sys.executable, "examples/" + name + "/" + name + "_is_" + property + ".py"],
        check=True
    )

class TestProofs(unittest.TestCase):
    def test_KEMfromPKE_is_INDCPA(self): run_example("KEMfromPKE", "INDCPA")
    def test_parallelPKE_is_INDCPA(self): run_example("parallelPKE", "INDCPA")
    def test_nestedPKE_is_INDCPA(self): run_example("nestedPKE", "INDCPA")
    def test_PKEfromKEM_is_INDCPA(self): run_example("PKEfromKEM", "INDCPA")
    def test_SymEnc_CPADollar_is_INDCPA(self): run_example("SymEnc_CPADollar", "INDCPA")
    def test_DoubleOTP_is_ROR(self): run_example("DoubleOTP", "ROR")
