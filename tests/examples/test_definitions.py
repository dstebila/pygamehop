import unittest

from gamehop.primitives import KEM, KEM2
import gamehop.inlining
from gamehop.verification import canonicalize_function

class TestDefinitions(unittest.TestCase):

    def test_KEM_INDCPA_definitions_equivalent(self): 
        g0 = gamehop.inlining.inline_argument_into_function('b', 0, KEM2.INDCPA.main)
        g1 = gamehop.inlining.inline_argument_into_function('b', 1, KEM2.INDCPA.main)
        assert canonicalize_function(g0) == canonicalize_function(KEM.INDCPA.main0)
        assert canonicalize_function(g1) == canonicalize_function(KEM.INDCPA.main1)
