import os
from typing import Generic, Tuple, Type, TypeVar

from gamehop.primitives import Crypto, KEM, PKE
from gamehop.proofs2 import Proof

from KEMfromPKE import KEMfromPKE, InnerPKE, PK, SK, CT, SS

# Theorem: KEMfromPKE[InnerPKE] is IND-CPA-secure if InnerPKE is IND-CPA-secure.
proof = Proof(KEMfromPKE, KEM.INDCPA)

# Game 0 is the KEMfromPKE scheme inlined into KEM.INDCPA_Real (where the real shared secret is encrypted).

# We want to hop to a game that encrypts an unrelated shared secret rather than the 
# real shared secret.  Before we can do that, we need to codify an implicit assumption
# in KEMfromPKE, that encryptions of equal-length messages yield equal-length ciphertexts.
# This will be done by a rewriting step.
# The rewriting step also renames one member variable to a local variable since the
# canonicalization engine can't handle that properly yet.
# This rewriting step will be phrased by rewriting the next game to get the previous 
# game, so we have to defer inserting this rewriting step until after the next step 
# has been added.

# Game 2 sends the encryption of an independent random value instead of the actual shared secret.

# Game 1 and Game 2 are indistinguishable under the assumption that InnerPKE is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against InnerPKE,
# and checking that this reduction, inlined into the IND-CPA experiment for InnerPKE,
# is equivalent to either Game 0 or Game 1.

class R1(Crypto.Reduction,
    Generic[PK, SK, CT, SS],
    PKE.INDCPA_Adversary[PK, SK, CT, SS] # This is an INDCPA adversary for InnerPKE
):
    def __init__(self, Scheme: Type[PKE.PKEScheme[PK, SK, CT, SS]], inner_adversary: KEM.INDCPA_Adversary[PK, SK, CT, SS]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the KEMfromPKE adversary
    def challenge(self, pk: PK) -> Tuple[SS, SS]:
        self.pk = pk
        # Generate two independent shared secrets as the challenge messages.
        self.ss0 = KEMfromPKE.uniformSharedSecret()
        ss1 = KEMfromPKE.uniformSharedSecret()
        return (self.ss0, ss1)
    def guess(self, ct: CT) -> Crypto.Bit:
        # Given the challenge InnerPKE ciphertext from the INDCPA challenger for InnerPKE,
        # pass it (as a KEMfromPKE ciphertext) to the KEMfromPKE adversary.
        return self.inner_adversary.guess(self.pk, ct, self.ss0)

proof.add_distinguishing_proof_step(R1, PKE.INDCPA, InnerPKE, "InnerPKE")

proof.insert_simple_rewriting_proof_step_before({
    "self.ss0": "selfss0",
    "if len(m0) == len(m1)": "if True"
})

# Need to again codify an implicit assumption in KEMfromPKE that encryptions of 
# equal-length messages yield equal-length ciphertexts.
# This will be done by a rewriting step.
# The rewriting step also renames one member variable to a local variable since the
# canonicalization engine can't handle that properly yet.

proof.insert_simple_rewriting_proof_step_after({
    "self.ss0": "selfss0",
    "if len(m0) == len(m1)": "if True"
})

assert proof.check(print_hops=True, print_canonicalizations=True, print_diffs=True, abort_on_failure=False)
print("Theorem:")
print(proof.advantage_bound())

with open(os.path.join('examples', 'KEMfromPKE', 'KEMfromPKE_is_INDCPA.tex'), 'w') as fh:
    fh.write(proof.tikz_figure())
