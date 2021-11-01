import os
from typing import Tuple, Type

from gamehop.primitives import Crypto, PKE
from gamehop.proofs2 import Proof

from parallelPKE import ParallelPKE, PKE1, PKE2

# Theorem: ParallelPKE[PKE1, PKE2] is IND-CPA-secure if both PKE1 and PKE2 are IND-CPA-secure.
proof = Proof(ParallelPKE, PKE.INDCPA)

# Game 0 is the ParallelPKE scheme inlined into PKE.INDCPA_Left (where m0 is encrypted).

# Game 1 encrypts m1 rather than m0 in PKE1.

# Game 0 and Game 1 are indistinguishable under the assumption that PKE1 is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against PKE1,
# and checking that this reduction, inlined into the IND-CPA experiment for PKE1,
# is equivalent to either Game 0 or Game 1.
class R1(PKE.INDCPA_Adversary, Crypto.Reduction): # This is an INDCPA adversary for PKE1
    def __init__(self, Scheme: Type[PKE1], inner_adversary: PKE.INDCPA_Adversary):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the ParallelPKE adversary
    def challenge(self, pk1: PKE1.PublicKey) -> Tuple[PKE1.Message, PKE1.Message]:
        # Use the ParallelPKE adversary to generate the two challenge messages.
        # To construct the ParallelPKE public key, we use the PKE1 public key given
        # by the INDCPA challenger for PKE1, and generate the PKE2 keypair ourselves.
        (pk2, sk2) = PKE2.KeyGen()
        pk_double = ParallelPKE.PublicKey(pk1, pk2)
        (m0, m1) = self.inner_adversary.challenge(pk_double)
        self.pk2 = pk2
        self.m0 = m0
        self.m1 = m1
        return (m0, m1)
    def guess(self, ct1: PKE1.Ciphertext) -> Crypto.Bit:
        # Given the challenge PKE1 ciphertext from the INDCPA challenger for PKE1,
        # construct a ParallelPKE ciphertext by encrypting m0 under the PKE2 public key,
        # then pass the ParallelPKE ciphertext to the ParallelPKE adversary.
        ct2 = PKE2.Encrypt(self.pk2, self.m0)
        ct = ParallelPKE.Ciphertext(ct1, ct2)
        return self.inner_adversary.guess(ct)

proof.add_distinguishing_proof_step(R1, PKE.INDCPA, PKE1)

# Game 2 encrypts m1 rather than m0 in PKE2.

# Game 1 and Game 2 are indistinguishable under the assumption that PKE2 is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against PKE2,
# and checking that this reduction, inlined into the IND-CPA experiment for PKE2,
# is equivalent to either Game 1 or Game 2.
class R2(PKE.INDCPA_Adversary, Crypto.Reduction): # This is an INDCPA adversary for PKE2
    def __init__(self, Scheme: Type[PKE2], inner_adversary: PKE.INDCPA_Adversary):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the ParallelPKE adversary
    def challenge(self, pk2: PKE2.PublicKey) -> Tuple[PKE2.Message, PKE2.Message]:
        # Use the ParallelPKE adversary to generate the two challenge messages.
        # To construct the ParallelPKE public key, we use the PKE2 public key given
        # by the INDCPA challenger for PKE2, and generate the PKE1 keypair ourselves.
        (pk1, sk1) = PKE1.KeyGen()
        pk_double = ParallelPKE.PublicKey(pk1, pk2)
        (m0, m1) = self.inner_adversary.challenge(pk_double)
        self.pk1 = pk1
        self.m0 = m0
        self.m1 = m1
        return (m0, m1)
    def guess(self, ct2: PKE2.Ciphertext) -> Crypto.Bit:
        # Given the challenge PKE2 ciphertext from the INDCPA challenger for PKE2,
        # construct a ParallelPKE ciphertext by encrypting m1 under the PKE1 public key,
        # then pass the ParallelPKE ciphertext to the ParallelPKE adversary.
        ct1 = PKE1.Encrypt(self.pk1, self.m1)
        ct = ParallelPKE.Ciphertext(ct1, ct2)
        return self.inner_adversary.guess(ct)

proof.add_distinguishing_proof_step(R2, PKE.INDCPA, PKE2)

assert proof.check(print_hops=True, print_canonicalizations=True, print_diffs=True, abort_on_failure=False)
print("Theorem :")
print(proof.advantage_bound())

with open(os.path.join('examples', 'parallelPKE', 'parallelPKE_is_INDCPA.tex'), 'w') as fh:
    fh.write(proof.tikz_figure())
