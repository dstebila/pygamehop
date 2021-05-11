from typing import Tuple, Any

from gamehop.primitives import Crypto, PKE
from gamehop.proofs import Proof

import nestedPKE

PKEScheme = PKE.PKEScheme
PKEINDCPA_adversary = PKE.PKEINDCPA_adversary

# term we're trying to bound, first in terms of PKE1 security
proof1 = Proof(PKE.INDCPA, nestedPKE.Scheme, PKEINDCPA_adversary)

# game hop:
# encrypt m1 rather than m0; simulate PKE2's encryption
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing PKE.INDCPA (with b = 0) from PKE.INDCPA (with b = 1) for PKE1
class R1(PKEINDCPA_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, pke2: PKEScheme) -> None:
        self.adversary = adversary      # this is the adversary for doublepke
        self.pke2 = pke2
    def setup(self, pke1: PKEScheme) -> None:
        self.pke1 = pke1
        dummy = self.adversary.setup(PKEScheme(self.pke1, self.pke2))
        return None
    def challenge(self, pk: PKE.PKEScheme.PublicKey) -> Tuple[PKE.PKEScheme.Message, PKE.PKEScheme.Message]:
        self.pk1 = pk
        (self.pk2, self.sk2)  = self.pke2.KeyGen()
        pk_double = (self.pk1, self.pk2)
        (m0, m1) = self.adversary.challenge(pk_double)
        return (m0, m1)
    def guess(self, ct: PKE.PKEScheme.Ciphertext) -> Crypto.Bit:
        ct2 = self.pke2.Encrypt(self.pk2, ct)
        return self.adversary.guess(ct2)

proof1.addDistinguishingProofStep(PKE.INDCPA, PKEScheme, R1)

assert proof1.check(print_hops=False, print_canonicalizations=False)
print()
print(proof1.advantage_bound())


# term we're trying to bound, first in terms of PKE1 security
proof2 = Proof(PKE.INDCPA, nestedPKE.Scheme, PKEINDCPA_adversary)

# game hop:
# encrypt m1 rather than m0; simulate PKE1's encryption
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing PKE.INDCPA (with b = 0) from PKE.INDCPA (with b = 1) for PKE2
class R2(PKEINDCPA_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, pke1: PKEScheme) -> None:
        self.adversary = adversary      # this is the adversary for doublepke
        self.pke1 = pke1
    def setup(self, pke2: PKEScheme) -> None:
        self.pke2 = pke2
        dummy = self.adversary.setup(PKEScheme(self.pke1, self.pke2))
        return None
    def challenge(self, pk: PKE.PKEScheme.PublicKey) -> Tuple[PKE.PKEScheme.Message, PKE.PKEScheme.Message]:
        self.pk2 = pk
        (self.pk1, self.sk1)  = self.pke1.KeyGen()
        pk_double = (self.pk1, self.pk2)
        (m0, m1) = self.adversary.challenge(pk_double)
        i0 = self.pke1.Encrypt(self.pk1, m0)
        i1 = self.pke1.Encrypt(self.pk1, m1)
        return (i0, i1)
    def guess(self, ct: PKE.PKEScheme.Ciphertext) -> Crypto.Bit:
        return self.adversary.guess(ct)

proof2.addDistinguishingProofStep(PKE.INDCPA, PKEScheme, R2)

assert proof2.check(print_hops=False, print_canonicalizations=False)
print()
print(proof2.advantage_bound())
