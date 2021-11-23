import ast
import random
import unittest

from typing import Generic, Type, TypeVar

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

PublicKey1 = TypeVar('PublicKey1')
Ciphertext1 = TypeVar('Ciphertext1')

class P1(Crypto.Scheme, Generic[PublicKey1, Ciphertext1]):
    @staticmethod
    def KeyGen() -> PublicKey1: pass
    @staticmethod
    def Encrypt(pk: PublicKey1, msg: str) -> Ciphertext1: pass
class G1_Adversary(Crypto.Adversary, Generic[PublicKey1, Ciphertext1]): # game idea: is ct the encryption of "hi" or "bye"?
    def hi_or_bye(self, pk: PublicKey1, ct: Ciphertext1) -> int: pass
class G1(Crypto.Game, Generic[PublicKey1, Ciphertext1]):
    def __init__(self, Scheme: Type[P1[PublicKey1, Ciphertext1]], Adversary: Type[G1_Adversary[PublicKey1, Ciphertext1]]):
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

PublicKey2 = TypeVar('PublicKey2')
Ciphertext2 = TypeVar('Ciphertext2')

class P2(Crypto.Scheme, Generic[PublicKey2, Ciphertext2]):
    @staticmethod
    def KG() -> PublicKey2: pass
    @staticmethod
    def ENC(pk: PublicKey2, msg: str) -> Ciphertext2: pass
class G2_Adversary(Crypto.Adversary, Generic[PublicKey2, Ciphertext2]): # game idea: is ct the encryption of "hi!" or not?"
    def hi_or_not(self, pk: PublicKey2, ct: Ciphertext2) -> bool: pass
class G2(Crypto.Game, Generic[PublicKey2, Ciphertext2]):
    def __init__(self, Scheme: Type[P2[PublicKey2, Ciphertext2]], Adversary: Type[G2_Adversary[PublicKey2, Ciphertext2]]):
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

PK = TypeVar('PK')
CT = TypeVar('CT')

P1Instance = P1[PK, CT]

class P2fromP1(Generic[PK, CT], P2[PK, CT]):
    @staticmethod
    def KG():
        return P1Instance.KeyGen()
    @staticmethod
    def ENC(pk, msg):
        return P1Instance.Encrypt(pk, msg)
class R(Generic[PK, CT], Crypto.Reduction, G1_Adversary[PK, CT]):
    def __init__(self, Scheme: Type[P1[PK, CT]], inner_adversary: G2_Adversary[PK, CT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary
    def hi_or_bye(self, pk: PK, ct: CT) -> int:
        g = self.inner_adversary.hi_or_not(pk, ct)
        ret = 0 if g else 1
        return ret

class TestInlineReductionIntoGame(unittest.TestCase):

    def test_P2fromP1_into_G2(self):
        self.maxDiff = None
        class G2_expected_result(Crypto.Game, Generic[PK, CT]):
            def __init__(self, Adversary: Type[G2_Adversary[PK, CT]]):
                self.Scheme = P2fromP1
                self.adversary = Adversary(P2fromP1)
            def main(self) -> Crypto.Bit:
                pk = P1Instance.KeyGen()
                b = random.choice([0, 1])
                msge = "hi!" if b == 0 else "bye"
                ct = P1Instance.Encrypt(pk, msge)
                bnew = self.adversary.hi_or_not(pk, ct)
                bstar = 0 if bnew else 1
                ret = 1 if b == bstar else 0
                return Crypto.Bit(ret)
        self.assertEqual(
            gamehop.inlining.inline_scheme_into_game(P2fromP1, G2),
            expected_result(G2_expected_result))

    def test_R_into_G1(self):
        self.maxDiff = None
        class G2_expected_result(Crypto.Game, Generic[PK, CT]):
            def __init__(self, Adversary: Type[G2_Adversary[PK, CT]]):
                self.Scheme = P2fromP1
                self.adversary = Adversary(P2fromP1)
            def main(self) -> Crypto.Bit:
                pk = P1Instance.KeyGen()
                b = random.choice([0, 1])
                msge = 'hi!' if b == 0 else 'bye'
                ct = P1Instance.Encrypt(pk, msge)
                R_hi_or_byeᴠ1ⴰg = self.adversary.hi_or_not(pk, ct)
                R_hi_or_byeᴠ1ⴰret = 0 if R_hi_or_byeᴠ1ⴰg else 1
                bstar = R_hi_or_byeᴠ1ⴰret
                ret = 1 if b == bstar else 0
                return Crypto.Bit(ret)
        self.assertEqual(
            gamehop.inlining.inline_reduction_into_game(R, G1, P1Instance, "P1Instance", G2, P2fromP1, G2_Adversary),
            expected_result(G2_expected_result))
