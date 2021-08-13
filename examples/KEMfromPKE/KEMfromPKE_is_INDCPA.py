from typing import Tuple

from gamehop.primitives import Crypto, KEM, PKE
from gamehop.primitives.KEM import SharedSecret
from gamehop.proofs import Proof

import KEMfromPKE

PKEScheme = PKE.PKEScheme

KEMINDCPA_adversary = KEM.KEMINDCPA_adversary

# statement we're trying to prove
proof = Proof(KEM.INDCPA, KEMfromPKE.Scheme, KEMINDCPA_adversary)

# game hop: rewriting step
# len(Crypto.UniformlySample(SharedSecret)) == len(Crypto.UniformlySample(SharedSecret))
def rewrite_left0(v0: KEMINDCPA_adversary, v1: PKEScheme) -> Crypto.Bit:
    (v2, v3) = v1.KeyGen()
    v4 = Crypto.UniformlySample(SharedSecret)
    v5 = v1.Encrypt(v2, v4)
    v6 = v0.guess(v2, v5, v4)
    v7 = Crypto.UniformlySample(SharedSecret)
    v10 = v6 if True else Crypto.Bit(0)
    return v10

def rewrite_right0(v0: KEMINDCPA_adversary, v1: PKEScheme) -> Crypto.Bit:
    (v2, v3) = v1.KeyGen()
    v4 = Crypto.UniformlySample(SharedSecret)
    v5 = v1.Encrypt(v2, v4)
    v6 = v0.guess(v2, v5, v4)
    v7 = Crypto.UniformlySample(SharedSecret)
    v10 = v6 if len(v4) == len(v7) else Crypto.Bit(0)
    return v10

proof.addRewritingStep(rewrite_left0, rewrite_right0)

# game hop: distinguishing step
# send the encryption of an independent random value instead of the actual shared secret
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing PKE.INDCPA (with b = 0) from PKE.INDCPA (with b = 1)
class R12(PKE.PKEINDCPA_adversary):
    def __init__(self, kem_adversary: KEMINDCPA_adversary) -> None:
        self.kem_adversary = kem_adversary
    def setup(self, pke2: PKE.PKEScheme) -> None:
        self.pke = pke2
        return None
    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk = pk
        self.ss0 = Crypto.UniformlySample(SharedSecret)
        self.ct0 = self.pke.Encrypt(pk, self.ss0)
        self.m0 = self.ss0
        self.ss1 = Crypto.UniformlySample(SharedSecret)
        self.ct1 = self.pke.Encrypt(pk, self.ss1)
        self.m1 = self.ss1
        return (self.m0, self.m1)
    def guess(self, ct: PKE.Ciphertext) -> Crypto.Bit:
        return self.kem_adversary.guess(self.pk, ct, self.m0)

proof.addDistinguishingProofStep(PKE.INDCPA, PKE.PKEScheme, R12)

# game hop: rewriting step
# len(Crypto.UniformlySample(SharedSecret)) == len(Crypto.UniformlySample(SharedSecret))
def rewrite_left2(v0: KEMINDCPA_adversary, v1: PKEScheme) -> Crypto.Bit:
    (v2, v3) = v1.KeyGen()
    v4 = Crypto.UniformlySample(SharedSecret)
    v5 = v1.Encrypt(v2, v4)
    v6 = Crypto.UniformlySample(SharedSecret)
    v7 = v0.guess(v2, v5, v6)
    v8 = len(v6) == len(v4)
    v9 = Crypto.Bit(0)
    v10 = v7 if v8 else v9
    return v10

def rewrite_right2(v0: KEMINDCPA_adversary, v1: PKEScheme) -> Crypto.Bit:
    (v2, v3) = v1.KeyGen()
    v4 = Crypto.UniformlySample(SharedSecret)
    v5 = v1.Encrypt(v2, v4)
    v6 = Crypto.UniformlySample(SharedSecret)
    v7 = v0.guess(v2, v5, v6)
    v8 = True
    v9 = Crypto.Bit(0)
    v10 = v7 if v8 else v9
    return v10

proof.addRewritingStep(rewrite_left2, rewrite_right2)

assert proof.check(print_hops=True, print_canonicalizations=True)
print()
print(proof.advantage_bound())
