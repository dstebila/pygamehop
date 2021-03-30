from typing import Tuple

from gamehop.primitives import Crypto, PKE
from gamehop.proofs import Proof

import stupiddoublePKE

PKEScheme = PKE.PKEScheme
PKEINDCPA_adversary = PKE.PKEINDCPA_adversary

# statement we're trying to prove
proof = Proof(PKE.INDCPA, stupiddoublePKE.Scheme, PKE.PKEINDCPA_adversary)

# game hop:
# for PKE1, encrypt m1 rather than m0
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing PKE.INDCPA (with b = 0) from PKE.INDCPA (with b = 1) for PKE1
class R01(PKEINDCPA_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, pke2: PKEScheme) -> None:
        self.adversary = adversary      # this is the adversary for pke1
        self.pke2 = pke2
    def setup(self, pke1: PKEScheme) -> None:        
        self.pke1 = pke1
        dummy = self.adversary.setup(self.pke1)
        return None
    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk1 = pk
        (self.pk2, self.sk2)  = self.pke2.KeyGen()
        pk_double = (self.pk1, self.pk2)
        (self.m0, self.m1) = self.adversary.challenge(pk_double)
        return (self.m0, self.m1)
    def guess(self, ct1: PKE.Ciphertext) -> Crypto.Bit:
        ct2 = self.pke2.Encrypt(self.pk2, self.m0)
        ct = (ct1, ct2)
        return self.adversary.guess(ct)

proof.addDistinguishingProofStep(PKE.INDCPA, PKEScheme, R01)

# game hop:
# for PKE2, encrypt m1 rather than m0
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing PKE.INDCPA (with b = 0) from PKE.INDCPA (with b = 1) for PKE2
class R12(PKEINDCPA_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, pke1: PKEScheme) -> None:
        self.adversary = adversary      # this is the adversary for pke2
        self.pke1 = pke1
    def setup(self, pke2: PKEScheme) -> None:
        self.pke2 = pke2
        dummy = self.adversary.setup(self.pke2)
        return None
    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk2 = pk
        (self.pk1, self.sk1)  = self.pke1.KeyGen()
        pk_double = (self.pk1, self.pk2)
        (self.m0, self.m1) = self.adversary.challenge(pk_double)
        return (self.m0, self.m1)
    def guess(self, ct2: PKE.Ciphertext) -> Crypto.Bit:
        ct1 = self.pke1.Encrypt(self.pk1, self.m1)
        ct = (ct1, ct2)
        return self.adversary.guess(ct)

proof.addDistinguishingProofStep(PKE.INDCPA, PKEScheme, R12)

assert proof.check(print_hops=False, print_canonicalizations=False)
print()
print(proof.advantage_bound())
