import ast
import random
import unittest

from typing import cast, Type

import gamehop.inlining
from gamehop.primitives import Crypto

def expected_result(g):
    gdef = gamehop.utils.get_class_def(g)
    gdef.name = gdef.name.replace('_expected_result', '')
    return ast.unparse(gdef)

# This is a pretty complicated test case
# The idea is that we have two primitives P1 and P2, with corresponding games G1 and G2.
# We also have a generic construction of a P2 from a P1, called P2fromP1.
# We give a reduction R which is a G1 adversary against P1 which makes use of a G2 adversary against P2fromP1.
# We want to check that R inlined into G1 for P1 looks like G2 for P2fromP1.
# First we have to construct G2 for P2fromP1, which we do by inline_scheme_into_game(P2fromP1, G2) and check that against the expected result. (Technically this test case is checking inline_scheme_into_game rather than inline_reduction_into_game, but we put it into this test file rather than test_inline_scheme_into_game since we need the objects to be present here for the next step.)
# Then we have inline R into G1 which we do by inline_reduction_into_game(R, G1, G2) and check that against the same expected result from the previous step.
# Well, these two different inlinings won't actually be equal as strings yet because we haven't applied canonicalization, so we'll list the two different versions we expect to get, which I have inspected and believe are logically equivalent.

class P1(Crypto.Scheme):
    class PublicKey(): pass
    class Ciphertext(): pass
    @staticmethod
    def KeyGen() -> PublicKey: pass
    @staticmethod
    def Encrypt(pk: PublicKey, msg: str) -> Ciphertext: pass
class G1_Adversary(Crypto.Adversary): # game idea: is ct the encryption of "hi" or "bye"?
    def hi_or_bye(self, pk: P1.PublicKey, ct: P1.Ciphertext) -> int: pass
class G1(Crypto.Game):
    def __init__(self, Scheme: Type[P1], Adversary: Type[G1_Adversary]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        pk = self.Scheme.KeyGen()
        b = random.choice([0,1])
        msge = "hi!" if b == 0 else "bye"
        ct = self.Scheme.Encrypt(pk, msge)
        bstar = self.adversary.hi_or_bye(pk, ct)
        ret = 1 if b == bstar else 0
        return Crypto.Bit(ret)
class P2(Crypto.Scheme):
    class PK(): pass
    class CT(): pass
    @staticmethod
    def KG() -> PK: pass
    @staticmethod
    def ENC(pk: PK, msg: str) -> CT: pass
class G2_Adversary(Crypto.Adversary): # game idea: is ct the encryption of "hi!" or not?"
    def hi_or_not(self, pk: P2.PK, ct: P2.CT) -> bool: pass
class G2(Crypto.Game):
    def __init__(self, Scheme: Type[P2], Adversary: Type[G2_Adversary]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        pk = self.Scheme.KG()
        b = random.choice([0,1])
        msge = "hi!" if b == 0 else "bye"
        ct = self.Scheme.ENC(pk, msge)
        bnew = self.adversary.hi_or_not(pk, ct)
        bstar = 0 if bnew else 1
        ret = 1 if b == bstar else 0
        return Crypto.Bit(ret)
class P2fromP1(P2):
    class PK(P2.PK):
        def __init__(self, pk: P1.PublicKey):
            self.pk = pk
    class CT(P2.CT):
        def __init__(self, ct: P1.Ciphertext):
            self.ct = ct
    @staticmethod
    def KG():
        pk = P1.KeyGen()
        return P2fromP1.PK(pk)
    @staticmethod
    def ENC(pk, msg):
        ct = P1.Encrypt(pk.pk, msg)
        return P2fromP1.CT(ct)
class R(Crypto.Reduction, G1_Adversary):
    def __init__(self, Scheme: Type[P1], inner_adversary: G2_Adversary):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary
    def hi_or_bye(self, pk: P1.PublicKey, ct: P1.Ciphertext) -> int:
        pkprime = P2fromP1.PK(pk)
        ctprime = P2fromP1.CT(ct)
        g = self.inner_adversary.hi_or_not(pkprime, ctprime)
        ret = 0 if g else 1
        return ret

class TestInlineReductionIntoGame(unittest.TestCase):

    def test_P2fromP1_into_G2(self):
        self.maxDiff = None
        class G2_expected_result(Crypto.Game):
            def __init__(self, Adversary: Type[G2_Adversary]):
                self.Scheme = P2fromP1
                self.adversary = Adversary(P2fromP1)
            def main(self) -> Crypto.Bit:
                P2fromP1_KGᴠ1ⴰpk = P1.KeyGen()
                pk = P2fromP1.PK.__new__(P2fromP1.PK)
                pk.pk = P2fromP1_KGᴠ1ⴰpk
                b = random.choice([0, 1])
                msge = "hi!" if b == 0 else "bye"
                P2fromP1_ENCᴠ1ⴰct = P1.Encrypt(pk.pk, msge)
                ct = P2fromP1.CT.__new__(P2fromP1.CT)
                ct.ct = P2fromP1_ENCᴠ1ⴰct
                bnew = self.adversary.hi_or_not(pk, ct)
                bstar = 0 if bnew else 1
                ret = 1 if b == bstar else 0
                return Crypto.Bit(ret)
        self.assertEqual(
            gamehop.inlining.inline_scheme_into_game(P2fromP1, G2),
            expected_result(G2_expected_result))

    def test_R_into_G1(self):
        self.maxDiff = None
        class G2_expected_result(Crypto.Game):
            def __init__(self, Adversary: Type[G2_Adversary]):
                self.Scheme = P2fromP1
                self.adversary = Adversary(P2fromP1)
            def main(self) -> Crypto.Bit:
                pk = P1.KeyGen()
                b = random.choice([0, 1])
                msge = 'hi!' if b == 0 else 'bye'
                ct = P1.Encrypt(pk, msge)
                R_hi_or_byeᴠ1ⴰpkprime = P2fromP1.PK.__new__(P2fromP1.PK)
                R_hi_or_byeᴠ1ⴰpkprime.pk = pk
                R_hi_or_byeᴠ1ⴰctprime = P2fromP1.CT.__new__(P2fromP1.CT)
                R_hi_or_byeᴠ1ⴰctprime.ct = ct
                R_hi_or_byeᴠ1ⴰg = self.adversary.hi_or_not(R_hi_or_byeᴠ1ⴰpkprime, R_hi_or_byeᴠ1ⴰctprime)
                R_hi_or_byeᴠ1ⴰret = 0 if R_hi_or_byeᴠ1ⴰg else 1
                bstar = R_hi_or_byeᴠ1ⴰret
                ret = 1 if b == bstar else 0
                return Crypto.Bit(ret)
        self.assertEqual(
            gamehop.inlining.inline_reduction_into_game(R, G1, P1, G2, P2fromP1),
            expected_result(G2_expected_result))
