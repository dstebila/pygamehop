import ast
import inspect
import unittest

import gamehop.inlining
from gamehop.primitives import Crypto

def expected_result(g):
    gdef = gamehop.utils.get_class_def(g)
    gdef.name = gdef.name.replace('_expected_result', '')
    return ast.unparse(gdef)

class TestInlineSchemeIntoGame(unittest.TestCase):

    def test_basic(self):
        class G(Crypto.Game):
            def __init__(self, Scheme, Adversary):
                self.Scheme = Scheme
                self.Adversary = Adversary
            def main(self) -> Crypto.Bit:
                adversary = self.Adversary(self.Scheme)
                (pk, sk) = self.Scheme.KeyGen()
                return 0
        class P(Crypto.Scheme):
            @staticmethod
            def KeyGen(): return (1, 2)
        class G_expected_result(Crypto.Game):
            def __init__(self, Adversary):
                self.Scheme = P
                self.Adversary = Adversary
            def main(self) -> Crypto.Bit:
                adversary = self.Adversary(P)
                (pk, sk) = (1, 2)
                return 0
        self.assertEqual(
            gamehop.inlining.inline_scheme_into_game(P, G),
            expected_result(G_expected_result))
