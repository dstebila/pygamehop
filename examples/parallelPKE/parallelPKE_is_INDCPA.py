import os
from typing import Generic, Tuple, Type

from gamehop.primitives import Crypto, PKE
from gamehop.proofs2 import Proof

from parallelPKE import ParallelPKE, PKE1, PKE2, PK1, PK2, SK1, SK2, CT1, CT2, PT12

# Theorem: ParallelPKE[PKE1, PKE2] is IND-CPA-secure if both PKE1 and PKE2 are IND-CPA-secure.
proof = Proof(ParallelPKE, PKE.INDCPA)

# Game 0 is the ParallelPKE scheme inlined into PKE.INDCPA_Left (where m0 is encrypted).

# Game 1 encrypts m1 rather than m0 in PKE1.

# Game 0 and Game 1 are indistinguishable under the assumption that PKE1 is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against PKE1,
# and checking that this reduction, inlined into the IND-CPA experiment for PKE1,
# is equivalent to either Game 0 or Game 1.
class R1(Crypto.Reduction,
    Generic[PK1, PK2, SK1, SK2, CT1, CT2, PT12],
    PKE.INDCPA_Adversary[PK1, SK1, CT1, PT12] # This is an INDCPA adversary for PKE1
):
    def __init__(self, Scheme: Type[PKE.PKEScheme[PK1, SK1, CT1, PT12]], inner_adversary: PKE.INDCPA_Adversary[Tuple[PK1, PK2], Tuple[SK1, SK2], Tuple[CT1, CT2], PT12]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the ParallelPKE adversary
    def challenge(self, pk1: PK1) -> Tuple[PT12, PT12]:
        # Use the ParallelPKE adversary to generate the two challenge messages.
        # To construct the ParallelPKE public key, we use the PKE1 public key given
        # by the INDCPA challenger for PKE1, and generate the PKE2 keypair ourselves.
        (pk2, sk2) = PKE2.KeyGen()
        (m0, m1) = self.inner_adversary.challenge((pk1, pk2))
        self.pk2 = pk2
        self.m0 = m0
        self.m1 = m1
        return (m0, m1)
    def guess(self, ct1: CT1) -> Crypto.Bit:
        # Given the challenge PKE1 ciphertext from the INDCPA challenger for PKE1,
        # construct a ParallelPKE ciphertext by encrypting m0 under the PKE2 public key,
        # then pass the ParallelPKE ciphertext to the ParallelPKE adversary.
        ct2 = PKE2.Encrypt(self.pk2, self.m0)
        return self.inner_adversary.guess((ct1, ct2))

proof.add_distinguishing_proof_step(R1, PKE.INDCPA, PKE1, "PKE1")

# Game 2 encrypts m1 rather than m0 in PKE2.

# Game 1 and Game 2 are indistinguishable under the assumption that PKE2 is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against PKE2,
# and checking that this reduction, inlined into the IND-CPA experiment for PKE2,
# is equivalent to either Game 1 or Game 2.
class R2(Crypto.Reduction,
    Generic[PK1, PK2, SK1, SK2, CT1, CT2, PT12],
    PKE.INDCPA_Adversary[PK2, SK2, CT2, PT12] # This is an INDCPA adversary for PKE2
):
    def __init__(self, Scheme: Type[PKE.PKEScheme[PK2, SK2, CT2, PT12]], inner_adversary: PKE.INDCPA_Adversary[Tuple[PK1, PK2], Tuple[SK1, SK2], Tuple[CT1, CT2], PT12]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the ParallelPKE adversary
    def challenge(self, pk2: PK2) -> Tuple[PT12, PT12]:
        # Use the ParallelPKE adversary to generate the two challenge messages.
        # To construct the ParallelPKE public key, we use the PKE2 public key given
        # by the INDCPA challenger for PKE2, and generate the PKE1 keypair ourselves.
        (pk1, sk1) = PKE1.KeyGen()
        (m0, m1) = self.inner_adversary.challenge((pk1, pk2))
        self.pk1 = pk1
        self.m0 = m0
        self.m1 = m1
        return (m0, m1)
    def guess(self, ct2: CT2) -> Crypto.Bit:
        # Given the challenge PKE2 ciphertext from the INDCPA challenger for PKE2,
        # construct a ParallelPKE ciphertext by encrypting m1 under the PKE1 public key,
        # then pass the ParallelPKE ciphertext to the ParallelPKE adversary.
        ct1 = PKE1.Encrypt(self.pk1, self.m1)
        return self.inner_adversary.guess((ct1, ct2))

proof.add_distinguishing_proof_step(R2, PKE.INDCPA, PKE2, "PKE2")

assert proof.check(print_hops=False, print_canonicalizations=False, print_diffs=False, abort_on_failure=False)
print("Theorem:")
print(proof.advantage_bound())

with open(os.path.join('examples', 'parallelPKE', 'parallelPKE_is_INDCPA.tex'), 'w') as fh:
    fh.write(proof.tikz_figure())
