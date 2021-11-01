import os
from typing import cast, Tuple, Type

from gamehop.primitives import Crypto, PKE
from gamehop.proofs2 import Proof

from KEMfromPKE import KEMfromPKE, PKE1

# Theorem: KEMfromPKE[PKE1] is IND-CPA-secure if PKE1 is IND-CPA-secure.
proof = Proof(KEMfromPKE, PKE.INDCPA)

# Game 0 is the KEMfromPKE scheme inlined into KEM.INDCPA_Real

# Game 1 sends the encryption of an independent random value instead of the actual shared secret.

# Game 0 and Game 1 are indistinguishable under the assumption that PKE1 is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against PKE1,
# and checking that this reduction, inlined into the IND-CPA experiment for PKE1,
# is equivalent to either Game 0 or Game 1.

class R1(PKE.INDCPA_Adversary, Crypto.Reduction): # This is an INDCPA adversary for PKE1
    def __init__(self, Scheme: Type[PKE1], inner_adversary: PKE.INDCPA_Adversary):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the ParallelPKE adversary
    def challenge(self, pk1: PKE1.PublicKey) -> Tuple[PKE1.Message, PKE1.Message]:
        self.pk = cast(KEMfromPKE.PublicKey, pk1)
        # Generate two independent shared secrets as the challenge messages.
        ss0 = Crypto.UniformlySample(KEMfromPKE.SharedSecret)
        self.ss0 = ss0
        ss1 = Crypto.UniformlySample(KEMfromPKE.SharedSecret)
        msg0 = cast(PKE1.Message, ss0)
        msg1 = cast(PKE1.Message, ss1)
        return (msg0, msg1)
    def guess(self, ct1: PKE1.Ciphertext) -> Crypto.Bit:
        # Given the challenge PKE1 ciphertext from the INDCPA challenger for PKE1,
        # pass it (as a KEMfromPKE ciphertext) to the KEMfromPKE adversary.
        ct = cast(KEMfromPKE.Ciphertext, ct)
        return self.inner_adversary.guess(self.pk, ct, self.ss0)

proof.add_distinguishing_proof_step(R1, PKE.INDCPA, PKE1)

# TODO: Will probably need to add rewriting steps before and after R1 about len(Crypto.UniformlySample(SharedSecret)) == len(Crypto.UniformlySample(SharedSecret))

assert proof.check(print_hops=True, print_canonicalizations=True, print_diffs=True, abort_on_failure=False)
print("Theorem :")
print(proof.advantage_bound())

with open(os.path.join('examples', 'KEMfromPKE', 'KEMfromPKE_is_INDCPA.tex'), 'w') as fh:
    fh.write(proof.tikz_figure())
