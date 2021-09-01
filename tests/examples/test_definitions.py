import unittest

from gamehop.primitives import KEM
import gamehop.inlining
from gamehop.verification import canonicalize_function

class TestDefinitions(unittest.TestCase):

    def oldtest_KEM_INDCPA_definitions_equivalent(self): 
        assert canonicalize_function(KEM.INDCPAv2.get_left()) == canonicalize_function(KEM.INDCPA.get_left())
        assert canonicalize_function(KEM.INDCPAv2.get_right()) == canonicalize_function(KEM.INDCPA.get_right())
