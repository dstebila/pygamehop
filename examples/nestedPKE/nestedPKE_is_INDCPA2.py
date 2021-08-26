from typing import cast, Tuple, Type

import gamehop.inlining
from gamehop.primitives import Crypto, PKE
from gamehop.proofs2 import Proof

from nestedPKE import NestedPKE, PKE1, PKE2

# term we're trying to bound, first in terms of PKE1 security
proof1 = Proof(NestedPKE, PKE.INDCPA)

# game hop:
# encrypt m1 rather than m0; simulate PKE2's encryption
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing PKE.INDCPA (with b = 0) from PKE.INDCPA (with b = 1) for PKE1
class R1(PKE.INDCPA_Adversary, Crypto.Reduction): # this is a INDCPA adversary for PKE1
    def __init__(self, Scheme: Type[PKE1], inner_adversary: PKE.INDCPA_Adversary):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary
    def challenge(self, pk1: PKE1.PublicKey) -> Tuple[PKE1.Message, PKE1.Message]:
        (self.pk2, self.sk2) = PKE2.KeyGen()
        pk_double = NestedPKE.PublicKey(pk1, self.pk2)
        (m0, m1) = self.inner_adversary.challenge(pk_double)
        return (m0, m1)
    def guess(self, ct1: PKE1.Ciphertext) -> Crypto.Bit:
        pt2 = cast(PKE2.Message, ct1)
        ct2 = PKE2.Encrypt(self.pk2, pt2)
        ctprime = cast(NestedPKE.Ciphertext, ct2)
        return self.inner_adversary.guess(ctprime)

print(gamehop.inlining.inline_scheme_into_game(NestedPKE, PKE.INDCPA.get_left()))
print(gamehop.inlining.inline_reduction_into_game(R1, PKE.INDCPA.get_left(), PKE1, PKE.INDCPA.get_left(), NestedPKE))

# proof1.addDistinguishingProofStep(PKE.INDCPA, 'pke1', R1)
