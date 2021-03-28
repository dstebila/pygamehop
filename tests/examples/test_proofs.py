import subprocess
import sys
import unittest

def run_example(name):
    subprocess.run(
        [sys.executable, "gamehop/app.py", "examples/" + name],
        check=True
    )

class TestProofs(unittest.TestCase):
    def test_KEMfromPKE(self): run_example("KEMfromPKE")
    def test_stupiddoublePKE(self): run_example("stupiddoublePKE")