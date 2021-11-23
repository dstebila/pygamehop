import os
from typing import cast, Generic, Tuple, Type, TypeVar

import gamehop.inlining
import gamehop.verification
from gamehop.primitives import Crypto, PKE
from gamehop.proofs2 import Proof
import gamehop.utils

from nestedPKE import NestedPKE, PKE1, PKE2, PK1, PK2, SK1, SK2, CT1, CT2, PT1

# Theorem: NestedPKE[PKE1, PKE2] is IND-CPA-secure if either PKE1 is IND-CPA-secure or PKE2 is IND-CPA-secure.
# This shown via two separate proofs:
# 1) If PKE1 is IND-CPA-secure, then NestedPKE[PKE1, PKE2] is IND-CPA-secure.
# 2) If PKE2 is IND-CPA-secure, then NestedPKE[PKE1, PKE2] is IND-CPA-secure.

# First proof: If PKE1 is IND-CPA-secure, then NestedPKE[PKE1, PKE2] is IND-CPA-secure.
# This is the statement we're trying to prove: NestedPKE is IND-CPA-secure.
proof1 = Proof(NestedPKE, PKE.INDCPA)

# Game 0 is the NestedPKE scheme inlined into PKE.INDCPA_Left (where m0 is encrypted).

# Game 1 encrypts m1 rather than m0.
# Game 1 is equivalent to the NestedPKE scheme inlined into PKE.INDCPA_Right (where m1 is encrypted).

# Game 0 and Game 1 are indistinguishable under the assumption that PKE1 is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against PKE1,
# and checking that this reduction, inlined into the IND-CPA experiment for PKE1, 
# is equivalent to either Game 0 or Game 1.
class R1(Generic[PK1, PK2, SK1, SK2, CT1, CT2, PT1], PKE.INDCPA_Adversary[PK1, SK1, CT1, PT1], Crypto.Reduction): # This is an INDCPA adversary for PKE1
    def __init__(self, Scheme: PKE.PKEScheme[PK1, SK1, CT1, PT1], inner_adversary: PKE.INDCPA_Adversary[Tuple[PK1, PK2], Tuple[SK1, SK2], CT2, PT1]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the NestedPKE adversary
    def challenge(self, pk1: PK1) -> Tuple[PT1, PT1]:
        # Use the NestedPKE adversary to generate the two challenge messages.
        # To construct the NestedPKE public key, we use the PKE1 public key given 
        # by the INDCPA challenger for PKE1, and generate the PKE2 keypair ourselves.
        (pk2, sk2) = PKE2.KeyGen()
        npk = (pk1, pk2)
        (m0, m1) = self.inner_adversary.challenge(npk)
        self.pk2 = pk2
        return (m0, m1)
    def guess(self, ct1: CT1) -> Crypto.Bit:
        # Given the challenge PKE1 ciphertext from the INDCPA challenger for PKE1,
        # construct a NestedPKE ciphertext by encrypting it under the PKE2 public key,
        # then pass the NestedPKE ciphertext to the NestedPKE adversary.
        ct2 = PKE2.Encrypt(self.pk2, ct1)
        return self.inner_adversary.guess(ct2)

proof1.add_distinguishing_proof_step(R1, PKE.INDCPA, PKE1, "PKE1")

assert proof1.check(print_hops=True, print_canonicalizations=True, print_diffs=True, abort_on_failure=False)
print("Theorem 1:")
print(proof1.advantage_bound())

with open(os.path.join('examples', 'nestedPKE', 'nestedPKE_is_INDCPA_proof1.tex'), 'w') as fh:
    fh.write(proof1.tikz_figure())

# Second proof: If PKE2 is IND-CPA-secure, then NestedPKE[PKE1, PKE2] is IND-CPA-secure.
# This is the statement we're trying to prove: NestedPKE is IND-CPA-secure.
proof2 = Proof(NestedPKE, PKE.INDCPA)

# Game 0 is the NestedPKE scheme inlined into PKE.INDCPA_Left (where m0 is encrypted).

# We want to hop to a game that encrypts m1 rather than m0.  Before we can do that,
# we need to codify an implicit assumption in NestedPKE, encryptions of equal-length
# messages yield equal-length ciphertexts.
# This will be done by a rewriting step.

INDCPA_Adversary = PKE.INDCPA_Adversary

class Rewrite0_Left(Crypto.Game, Generic[PK1, PK2, SK1, SK2, CT1, CT2, PT1]):

    def __init__(v0, v1: Type[INDCPA_Adversary[Tuple[PK1, PK2], Tuple[SK1, SK2], CT2, PT1]]):
        v0.Scheme = NestedPKE
        v0.adversary = v1(NestedPKE)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = PKE1.KeyGen()
        (v3, v4) = PKE2.KeyGen()
        (v5, v6) = v0.adversary.challenge((v1, v3))
        v7 = PKE1.Encrypt(v1, v5)
        v8 = PKE1.Encrypt(v1, v6)
        v9 = len(v5)
        v10 = len(v6)
        v11 = PKE2.Encrypt(v3, v7)
        v12 = len(v7)
        v13 = len(v8)
        v0ok = v9 == v10
        v14 = v0.adversary.guess(v11)
        v15 = Crypto.Bit(0)
        v16 = True
        v17 = v14 if v0ok else v15
        v18 = Crypto.Bit(0)
        v19 = v17 if v16 else v18
        return v19

class Rewrite0_Right(Crypto.Game, Generic[PK1, PK2, SK1, SK2, CT1, CT2, PT1]):

    def __init__(v0, v1: Type[INDCPA_Adversary[Tuple[PK1, PK2], Tuple[SK1, SK2], CT2, PT1]]):
        v0.Scheme = NestedPKE
        v0.adversary = v1(NestedPKE)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = PKE1.KeyGen()
        (v3, v4) = PKE2.KeyGen()
        (v5, v6) = v0.adversary.challenge((v1, v3))
        v7 = PKE1.Encrypt(v1, v5)
        v8 = PKE1.Encrypt(v1, v6)
        v9 = len(v5)
        v10 = len(v6)
        v11 = PKE2.Encrypt(v3, v7)
        v12 = len(v7)
        v13 = len(v8)
        v0.ok = v9 == v10
        v14 = v0.adversary.guess(v11)
        v15 = Crypto.Bit(0)
        v16 = v12 == v13
        v17 = v14 if v0.ok else v15
        v18 = Crypto.Bit(0)
        v19 = v17 if v16 else v18
        return v19

proof2.add_rewriting_proof_step(Rewrite0_Left, Rewrite0_Right)

# Game 2 encrypts m1 rather than m0.
# Game 2 is equivalent to the NestedPKE scheme inlined into PKE.INDCPA_Right (where m1 is encrypted).

# Game 1 and Game 2 are indistinguishable under the assumption that PKE2 is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against PKE2,
# and checking that this reduction, inlined into the IND-CPA experiment for PKE2, 
# is equivalent to either Game 1 or Game 2.
class R2(Generic[PK1, PK2, SK1, SK2, CT1, CT2, PT1], PKE.INDCPA_Adversary[PK2, SK2, CT2, CT1], Crypto.Reduction): # This is an INDCPA adversary for PKE2
    def __init__(self, Scheme: PKE.PKEScheme[PK2, SK2, CT2, CT1], inner_adversary: PKE.INDCPA_Adversary[Tuple[PK1, PK2], Tuple[SK1, SK2], CT2, CT1]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the NestedPKE adversary
    def challenge(self, pk2: PK2) -> Tuple[CT1, CT1]:
        # Use the NestedPKE adversary to generate the two challenge messages.
        # To construct the NestedPKE public key, we use the PKE2 public key given 
        # by the INDCPA challenger for PKE2, and generate the PKE1 keypair ourselves.
        # Once we get the challenge messages from the adversary, we have to encrypt
        # them under PKE1 so that the ciphertext we will eventually get back from
        # the PKE2 challenger is a NestedPKE ciphertext
        (pk1, sk1) = PKE1.KeyGen()
        npk = (pk1, pk2)
        (m0, m1) = self.inner_adversary.challenge(npk)
        self.ok = len(m0) == len(m1)
        c0 = PKE1.Encrypt(pk1, m0)
        c1 = PKE1.Encrypt(pk1, m1)
        return (c0, c1)
    def guess(self, ct2: CT2) -> Crypto.Bit:
        # The challenge PKE2 ciphertext from the INDCPA challenger for PKE2 contains
        # a PKE1 ciphertext of either m0 or m1, so it is immediately the NestedPKE 
        # challenge ciphertext.
        r = self.inner_adversary.guess(ct2)
        return r if self.ok else Crypto.Bit(0)

proof2.add_distinguishing_proof_step(R2, PKE.INDCPA, PKE2, 'PKE2')

# Need to codify an implicit assumption in NestedPKE that encryptions of equal-length
# messages yield equal-length ciphertexts.
# This will be done by a rewriting step.

class Rewrite2_Left(Crypto.Game, Generic[PK1, PK2, SK1, SK2, CT1, CT2, PT1]):

    def __init__(v0, v1: Type[INDCPA_Adversary[Tuple[PK1, PK2], Tuple[SK1, SK2], CT2, PT1]]):
        v0.Scheme = NestedPKE
        v0.adversary = v1(NestedPKE)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = PKE1.KeyGen()
        (v3, v4) = PKE2.KeyGen()
        (v5, v6) = v0.adversary.challenge((v1, v3))
        v7 = PKE1.Encrypt(v1, v5)
        v8 = PKE1.Encrypt(v1, v6)
        v9 = len(v5)
        v10 = len(v6)
        v11 = PKE2.Encrypt(v3, v8)
        v12 = len(v7)
        v13 = len(v8)
        v0.ok = v9 == v10
        v14 = v0.adversary.guess(v11)
        v15 = Crypto.Bit(0)
        v16 = v12 == v13
        v17 = v14 if v0.ok else v15
        v18 = Crypto.Bit(0)
        v19 = v17 if v16 else v18
        return v19

class Rewrite2_Right(Crypto.Game, Generic[PK1, PK2, SK1, SK2, CT1, CT2, PT1]):

    def __init__(v0, v1: Type[INDCPA_Adversary[Tuple[PK1, PK2], Tuple[SK1, SK2], CT2, PT1]]):
        v0.Scheme = NestedPKE
        v0.adversary = v1(NestedPKE)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = PKE1.KeyGen()
        (v3, v4) = PKE2.KeyGen()
        (v5, v6) = v0.adversary.challenge((v1, v3))
        v7 = PKE1.Encrypt(v1, v5)
        v8 = PKE1.Encrypt(v1, v6)
        v9 = len(v5)
        v10 = len(v6)
        v11 = PKE2.Encrypt(v3, v8)
        v12 = len(v7)
        v13 = len(v8)
        v0ok = v9 == v10
        v14 = v0.adversary.guess(v11)
        v15 = Crypto.Bit(0)
        v16 = True
        v17 = v14 if v0ok else v15
        v18 = Crypto.Bit(0)
        v19 = v17 if v16 else v18
        return v19

proof2.add_rewriting_proof_step(Rewrite2_Left, Rewrite2_Right)

assert proof2.check(print_hops=True, print_canonicalizations=True, print_diffs=True, abort_on_failure=False)
print("Theorem 2:")
print(proof2.advantage_bound())

with open(os.path.join('examples', 'nestedPKE', 'nestedPKE_is_INDCPA_proof2.tex'), 'w') as fh:
    fh.write(proof2.tikz_figure())
