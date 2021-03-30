import subprocess
import sys
import unittest

def run_example(name):
    subprocess.run(
        [sys.executable, "examples/" + name + "/proof2.py"],
        check=True
    )

class TestProofs(unittest.TestCase):
    def test_KEMfromPKE(self): run_example("KEMfromPKE")
    # def test_stupiddoublePKE(self): run_example("stupiddoublePKE")
    # def test_doublePKE(self): run_example("doublePKE")
