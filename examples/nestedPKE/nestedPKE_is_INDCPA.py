import os
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
class R1(PKEINDCPA_adversary): # this is an adversary for PKE1
    def __init__(self, adversary: PKEINDCPA_adversary, pke2: PKEScheme) -> None:
        self.adversary = adversary # this is the adversary for nestedPKE
        self.pke2 = pke2
    def setup(self, pke1: PKEScheme) -> None:
        self.pke1 = pke1
        dummy = self.adversary.setup(PKEScheme(self.pke1, self.pke2))
        return None
    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk1 = pk
        (self.pk2, self.sk2)  = self.pke2.KeyGen()
        pk_double = (self.pk1, self.pk2)
        (m0, m1) = self.adversary.challenge(pk_double)
        return (m0, m1)
    def guess(self, ct: PKE.Ciphertext) -> Crypto.Bit:
        ct2 = self.pke2.Encrypt(self.pk2, ct)
        return self.adversary.guess(ct2)

proof1.addDistinguishingProofStep(PKE.INDCPA, PKEScheme, R1)

assert proof1.check(print_hops=False, print_canonicalizations=False)
print()
print(proof1.advantage_bound())


# term we're trying to bound, first in terms of PKE1 security
proof2 = Proof(PKE.INDCPA, nestedPKE.Scheme, PKEINDCPA_adversary)

# gamehop: rewriting step
# len(PKEScheme.Encrypt(pk, m0)) = len(PKEScheme.Encrypt(pk, m1)) assuming len(m0) == len(m1)
def rewrite_left0(v0: PKEScheme, v1: PKEINDCPA_adversary, v2: PKEScheme) -> Crypto.Bit:
    (v3, v4) = v0.KeyGen()
    (v5, v6) = v2.KeyGen()
    (v7, v8) = v1.challenge((v3, v5))
    v9 = v0.Encrypt(v3, v7)
    v10 = v2.Encrypt(v5, v9)
    v11 = v1.guess(v10)
    v12 = len(v7) == len(v8)
    v13 = Crypto.Bit(0)
    v14 = v0.Encrypt(v3, v8)
    v15 = v11 if v12 else v13
    v16 = True
    v17 = Crypto.Bit(0)
    v18 = v15 if v16 else v17
    return v18
def rewrite_right0(v0: PKEScheme, v1: PKEINDCPA_adversary, v2: PKEScheme) -> Crypto.Bit:
    (v3, v4) = v0.KeyGen()
    (v5, v6) = v2.KeyGen()
    (v7, v8) = v1.challenge((v3, v5))
    v9 = v0.Encrypt(v3, v7)
    v10 = v2.Encrypt(v5, v9)
    v11 = v1.guess(v10)
    v12 = len(v7) == len(v8)
    v13 = Crypto.Bit(0)
    v14 = v0.Encrypt(v3, v8)
    v15 = v11 if v12 else v13
    v16 = len(v9) == len(v14)
    v17 = Crypto.Bit(0)
    v18 = v15 if v16 else v17
    return v18
proof2.addRewritingStep(rewrite_left0, rewrite_right0)

# game hop: distinguishing step
# encrypt m1 rather than m0; simulate PKE1's encryption
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing PKE.INDCPA (with b = 0) from PKE.INDCPA (with b = 1) for PKE2
class R2(PKEINDCPA_adversary): # this is an adversary for PKE2
    def __init__(self, adversary: PKEINDCPA_adversary, pke1: PKEScheme) -> None:
        self.adversary = adversary # this is the adversary for nestedPKE
        self.pke1 = pke1
    def setup(self, pke2: PKEScheme) -> None:
        self.pke2 = pke2
        dummy = self.adversary.setup(PKEScheme(self.pke1, self.pke2))
        return None
    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk2 = pk
        (self.pk1, self.sk1)  = self.pke1.KeyGen()
        pk_double = (self.pk1, self.pk2)
        (m0, m1) = self.adversary.challenge(pk_double)
        self.ok = len(m0) == len(m1)
        i0 = self.pke1.Encrypt(self.pk1, m0)
        i1 = self.pke1.Encrypt(self.pk1, m1)
        return (i0, i1)
    def guess(self, ct: PKE.Ciphertext) -> Crypto.Bit:
        r = self.adversary.guess(ct)
        return r if self.ok else Crypto.Bit(0)

proof2.addDistinguishingProofStep(PKE.INDCPA, PKEScheme, R2)

# gamehop: rewriting step
# len(PKEScheme.Encrypt(pk, m0)) = len(PKEScheme.Encrypt(pk, m1)) assuming len(m0) == len(m1)
def rewrite_left2(v0: PKEScheme, v1: PKEINDCPA_adversary, v2: PKEScheme) -> Crypto.Bit:
    (v3, v4) = v0.KeyGen()
    (v5, v6) = v2.KeyGen()
    (v7, v8) = v1.challenge((v3, v5))
    v9 = v0.Encrypt(v3, v8)
    v10 = v2.Encrypt(v5, v9)
    v11 = v1.guess(v10)
    v12 = len(v7) == len(v8)
    v13 = Crypto.Bit(0)
    v14 = v0.Encrypt(v3, v7)
    v15 = v11 if v12 else v13
    v16 = len(v14) == len(v9)
    v17 = Crypto.Bit(0)
    v18 = v15 if v16 else v17
    return v18
def rewrite_right2(v0: PKEScheme, v1: PKEINDCPA_adversary, v2: PKEScheme) -> Crypto.Bit:
    (v3, v4) = v0.KeyGen()
    (v5, v6) = v2.KeyGen()
    (v7, v8) = v1.challenge((v3, v5))
    v9 = v0.Encrypt(v3, v8)
    v10 = v2.Encrypt(v5, v9)
    v11 = v1.guess(v10)
    v12 = len(v7) == len(v8)
    v13 = Crypto.Bit(0)
    v14 = v0.Encrypt(v3, v7)
    v15 = v11 if v12 else v13
    v16 = True
    v17 = Crypto.Bit(0)
    v18 = v15 if v16 else v17
    return v18
proof2.addRewritingStep(rewrite_left2, rewrite_right2)

assert proof2.check(print_hops=True, print_canonicalizations=True)
print()
print(proof2.advantage_bound())

with open(os.path.join('examples', 'nestedPKE', 'nestedPKE_is_INDCPA_proof1.tex'), 'w') as fh:
    fh.write(proof1.tikz_figure())
with open(os.path.join('examples', 'nestedPKE', 'nestedPKE_is_INDCPA_proof2.tex'), 'w') as fh:
    fh.write(proof2.tikz_figure())
