import os
from typing import cast, Tuple, Type

import gamehop.inlining
import gamehop.verification
from gamehop.primitives import Crypto, PKE
from gamehop.proofs2 import Proof
import gamehop.utils

from nestedPKE import NestedPKE, PKE1, PKE2, NPK, NSK, PK1, PK2, SK1, SK2, CT1, CT2, PT1

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
class R1(PKE.INDCPA_Adversary[NPK, NSK, CT2, PT1], Crypto.Reduction): # This is an INDCPA adversary for PKE1
    def __init__(self, Scheme, inner_adversary):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the NestedPKE adversary
    def challenge(self, pk1):
        # Use the NestedPKE adversary to generate the two challenge messages.
        # To construct the NestedPKE public key, we use the PKE1 public key given 
        # by the INDCPA challenger for PKE1, and generate the PKE2 keypair ourselves.
        (pk2, sk2) = PKE2.KeyGen()
        npk = (pk1, pk2)
        (m0, m1) = self.inner_adversary.challenge(npk)
        self.pk2 = pk2
        return (m0, m1)
    def guess(self, ct1):
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

exit()

# Second proof: If PKE2 is IND-CPA-secure, then NestedPKE[PKE1, PKE2] is IND-CPA-secure.
# This is the statement we're trying to prove: NestedPKE is IND-CPA-secure.
proof2 = Proof(NestedPKE, PKE.INDCPA)

# Game 0 is the NestedPKE scheme inlined into PKE.INDCPA_Left (where m0 is encrypted).

# We want to hop to a game that encrypts m1 rather than m0.  Before we can do that,
# we need to codify an implicit assumption in NestedPKE, encryptions of equal-length
# messages yield equal-length ciphertexts.
# This will be done by a rewriting step.

INDCPA_Adversary = PKE.INDCPA_Adversary

class Rewrite0_Left(Crypto.Game):

    def __init__(v0, v1: Type[INDCPA_Adversary]):
        v0.Scheme = NestedPKE
        v0.adversary = v1(NestedPKE)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = PKE1.KeyGen()
        (v3, v4) = PKE2.KeyGen()
        v5 = NestedPKE.PublicKey.__new__(NestedPKE.PublicKey)
        v5.pk1 = v1
        v5.pk2 = v3
        (v6, v7) = v0.adversary.challenge(v5)
        v8 = PKE1.Encrypt(v1, v6)
        v9 = cast(PKE2.Message, v8)
        v10 = PKE1.Encrypt(v1, v7)
        v11 = PKE2.Encrypt(v3, v9)
        v12 = cast(PKE2.Message, v10)
        v13 = len(v6)
        v14 = len(v7)
        v15 = cast(NestedPKE.Ciphertext, v11)
        v16 = len(v9)
        v17 = len(v12)
        v0ok = v13 == v14
        v18 = v0.adversary.guess(v15)
        v19 = Crypto.Bit(0)
        v20 = True
        v21 = v18 if v0ok else v19
        v22 = Crypto.Bit(0)
        v23 = v21 if v20 else v22
        return v23

class Rewrite0_Right(Crypto.Game):

    def __init__(v0, v1: Type[INDCPA_Adversary]):
        v0.Scheme = NestedPKE
        v0.adversary = v1(NestedPKE)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = PKE1.KeyGen()
        (v3, v4) = PKE2.KeyGen()
        v5 = NestedPKE.PublicKey.__new__(NestedPKE.PublicKey)
        v5.pk1 = v1
        v5.pk2 = v3
        (v6, v7) = v0.adversary.challenge(v5)
        v8 = PKE1.Encrypt(v1, v6)
        v9 = cast(PKE2.Message, v8)
        v10 = PKE1.Encrypt(v1, v7)
        v11 = PKE2.Encrypt(v3, v9)
        v12 = cast(PKE2.Message, v10)
        v13 = len(v6)
        v14 = len(v7)
        v15 = cast(NestedPKE.Ciphertext, v11)
        v16 = len(v9)
        v17 = len(v12)
        v0.ok = v13 == v14
        v18 = v0.adversary.guess(v15)
        v19 = Crypto.Bit(0)
        v20 = v16 == v17
        v21 = v18 if v0.ok else v19
        v22 = Crypto.Bit(0)
        v23 = v21 if v20 else v22
        return v23

proof2.add_rewriting_proof_step(Rewrite0_Left, Rewrite0_Right)

# Game 2 encrypts m1 rather than m0.
# Game 2 is equivalent to the NestedPKE scheme inlined into PKE.INDCPA_Right (where m1 is encrypted).

# Game 1 and Game 2 are indistinguishable under the assumption that PKE2 is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against PKE2,
# and checking that this reduction, inlined into the IND-CPA experiment for PKE2, 
# is equivalent to either Game 1 or Game 2.
class R2(PKE.INDCPA_Adversary, Crypto.Reduction): # This is an INDCPA adversary for PKE2
    def __init__(self, Scheme: Type[PKE2], inner_adversary: PKE.INDCPA_Adversary):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the NestedPKE adversary
    def challenge(self, pk2: PKE2.PublicKey) -> Tuple[PKE2.Message, PKE2.Message]:
        # Use the NestedPKE adversary to generate the two challenge messages.
        # To construct the NestedPKE public key, we use the PKE2 public key given 
        # by the INDCPA challenger for PKE2, and generate the PKE1 keypair ourselves.
        # Once we get the challenge messages from the adversary, we have to encrypt
        # them under PKE1 so that the ciphertext we will eventually get back from
        # the PKE2 challenger is a NestedPKE ciphertext
        (pk1, sk1) = PKE1.KeyGen()
        pk_double = NestedPKE.PublicKey(pk1, pk2)
        (m0, m1) = self.inner_adversary.challenge(pk_double)
        self.ok = len(m0) == len(m1)
        i0 = PKE1.Encrypt(pk1, m0)
        i1 = PKE1.Encrypt(pk1, m1)
        c0 = cast(PKE2.Message, i0)
        c1 = cast(PKE2.Message, i1)
        return (c0, c1)
    def guess(self, ct2: PKE2.Ciphertext) -> Crypto.Bit:
        # The challenge PKE2 ciphertext from the INDCPA challenger for PKE2 contains
        # a PKE1 ciphertext of either m0 or m1, so it is immediately the NestedPKE 
        # challenge ciphertext.
        ct = cast(NestedPKE.Ciphertext, ct2) # Treat the PKE2 ciphertext as a NestedPKE ciphertext
        r = self.inner_adversary.guess(ct)
        return r if self.ok else Crypto.Bit(0)

proof2.add_distinguishing_proof_step(R2, PKE.INDCPA, PKE2)

# Need to codify an implicit assumption in NestedPKE that encryptions of equal-length
# messages yield equal-length ciphertexts.
# This will be done by a rewriting step.

class Rewrite2_Left(Crypto.Game):

    def __init__(v0, v1: Type[INDCPA_Adversary]):
        v0.Scheme = NestedPKE
        v0.adversary = v1(NestedPKE)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = PKE1.KeyGen()
        (v3, v4) = PKE2.KeyGen()
        v5 = NestedPKE.PublicKey.__new__(NestedPKE.PublicKey)
        v5.pk1 = v1
        v5.pk2 = v3
        (v6, v7) = v0.adversary.challenge(v5)
        v8 = PKE1.Encrypt(v1, v6)
        v9 = PKE1.Encrypt(v1, v7)
        v10 = cast(PKE2.Message, v9)
        v11 = PKE2.Encrypt(v3, v10)
        v12 = cast(PKE2.Message, v8)
        v13 = len(v6)
        v14 = len(v7)
        v15 = cast(NestedPKE.Ciphertext, v11)
        v16 = len(v12)
        v17 = len(v10)
        v0.ok = v13 == v14
        v18 = v0.adversary.guess(v15)
        v19 = Crypto.Bit(0)
        v20 = v16 == v17
        v21 = v18 if v0.ok else v19
        v22 = Crypto.Bit(0)
        v23 = v21 if v20 else v22
        return v23

class Rewrite2_Right(Crypto.Game):

    def __init__(v0, v1: Type[INDCPA_Adversary]):
        v0.Scheme = NestedPKE
        v0.adversary = v1(NestedPKE)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = PKE1.KeyGen()
        (v3, v4) = PKE2.KeyGen()
        v5 = NestedPKE.PublicKey.__new__(NestedPKE.PublicKey)
        v5.pk1 = v1
        v5.pk2 = v3
        (v6, v7) = v0.adversary.challenge(v5)
        v8 = PKE1.Encrypt(v1, v6)
        v9 = PKE1.Encrypt(v1, v7)
        v10 = cast(PKE2.Message, v9)
        v11 = PKE2.Encrypt(v3, v10)
        v12 = cast(PKE2.Message, v8)
        v13 = len(v6)
        v14 = len(v7)
        v15 = cast(NestedPKE.Ciphertext, v11)
        v16 = len(v12)
        v17 = len(v10)
        v0ok = v13 == v14
        v18 = v0.adversary.guess(v15)
        v19 = Crypto.Bit(0)
        v20 = True
        v21 = v18 if v0ok else v19
        v22 = Crypto.Bit(0)
        v23 = v21 if v20 else v22
        return v23

proof2.add_rewriting_proof_step(Rewrite2_Left, Rewrite2_Right)

assert proof2.check(print_hops=True, print_canonicalizations=False, print_diffs=False, abort_on_failure=False)
print("Theorem 2:")
print(proof2.advantage_bound())

with open(os.path.join('examples', 'nestedPKE', 'nestedPKE_is_INDCPA_proof2.tex'), 'w') as fh:
    fh.write(proof2.tikz_figure())
