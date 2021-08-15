import unittest

from gamehop.primitives import kem
import gamehop.inlining
from gamehop.verification import canonicalize_function

class TestDefinitions(unittest.TestCase):

    def old_test_KEM_INDCPA_definitions_equivalent(self): 
        assert canonicalize_function(kem.INDCPAv2.get_left()) == canonicalize_function(kem.INDCPA.get_left())
        assert canonicalize_function(kem.INDCPAv2.get_right()) == canonicalize_function(kem.INDCPA.get_right())
