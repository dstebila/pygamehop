from typing import Tuple

from gamehop.primitives import Crypto, KEM, PKE
from gamehop.proofs import Proof

import KEMfromPKE

KEMINDCPA_adversary = KEM.KEMINDCPA_adversary

# statement we're trying to prove
proof = Proof(KEM.INDCPA, KEMfromPKE.Scheme, KEMINDCPA_adversary)

# game hop:
# send the encryption of an independent random value instead of the actual shared secret
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing PKE.INDCPA (with b = 0) from PKE.INDCPA (with b = 1)
class R01(PKE.PKEINDCPA_adversary):
    def __init__(self, kem_adversary: KEMINDCPA_adversary) -> None:
        self.kem_adversary = kem_adversary
    def setup(self, pke2: PKE.PKEScheme) -> None:
        self.pke = pke2
        return None
    def challenge(self, pk: PKE.PKEScheme.PublicKey) -> Tuple[PKE.PKEScheme.Message, PKE.PKEScheme.Message]:
        self.pk = pk
        self.ss0 = Crypto.UniformlySample(self.pke.MessageSet)
        self.ct0 = self.pke.Encrypt(pk, self.ss0)
        self.m0 = self.ss0
        self.ss1 = Crypto.UniformlySample(self.pke.MessageSet)
        self.ct1 = self.pke.Encrypt(pk, self.ss1)
        self.m1 = self.ss1
        return (self.m0, self.m1)
    def guess(self, ct: PKE.PKEScheme.Ciphertext) -> Crypto.Bit:
        return self.kem_adversary.guess(self.pk, ct, self.m0)

proof.addDistinguishingProofStep(PKE.INDCPA, PKE.PKEScheme, R01)

assert proof.check(print_hops=False, print_canonicalizations=False)
print()
print(proof.advantage_bound())
