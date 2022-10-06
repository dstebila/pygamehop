import os
from typing import Generic, Tuple, Type

from gamehop.primitives import Crypto, OTP
from gamehop.proofs2 import Proof

from DoubleOTP import DoubleOTP, SK1, SK2, CT1, CT2, PT1, InnerOTP, OuterOTP

# Theorem: DoubleOTP is ROR-secure if OuterOTP is.
proof = Proof(DoubleOTP, OTP.ROR)

# Game 0 is the DoubleOTP scheme inlined into OTP.ROR_Real.

# Before we can jump to game 1, we need to do a rewriting step regarding message 
# / ciphertext lengths that pygamehop can't deduce automatically.
# In particular, that the length of the inner ciphertext is the same as the length
# of the original message.
# We do this using a "rewriting step" in which we specify the two versions of the game
# before and after rewriting. pygame will then check that the before version
# matches the previous game and the after version matches the next game.

class RW1Left(Crypto.Game, Generic[SK1, SK2, CT1, CT2, PT1]):
    def __init__(self, Adversary: Type[OTP.ROR_Adversary[Tuple[SK1, SK2], PT1, CT2]]):
        self.Scheme = DoubleOTP
        self.adversary = Adversary(DoubleOTP)
    def main(self) -> Crypto.Bit:
        R1_challengeᴠ1ⴰm = self.adversary.challenge()
        R1_challengeᴠ1ⴰsk1 = InnerOTP.KeyGen(len(R1_challengeᴠ1ⴰm))
        R1_challengeᴠ1ⴰct1 = InnerOTP.Encrypt(R1_challengeᴠ1ⴰsk1, R1_challengeᴠ1ⴰm)
        m = R1_challengeᴠ1ⴰct1
        k = OuterOTP.KeyGen(len(R1_challengeᴠ1ⴰm)) # This line changes
        ct = OuterOTP.Encrypt(k, m)
        r = self.adversary.guess(ct)
        return r

class RW1Right(Crypto.Game, Generic[SK1, SK2, CT1, CT2, PT1]):
    def __init__(self, Adversary: Type[OTP.ROR_Adversary[Tuple[SK1, SK2], PT1, CT2]]):
        self.Scheme = DoubleOTP
        self.adversary = Adversary(DoubleOTP)
    def main(self) -> Crypto.Bit:
        R1_challengeᴠ1ⴰm = self.adversary.challenge()
        R1_challengeᴠ1ⴰsk1 = InnerOTP.KeyGen(len(R1_challengeᴠ1ⴰm))
        R1_challengeᴠ1ⴰct1 = InnerOTP.Encrypt(R1_challengeᴠ1ⴰsk1, R1_challengeᴠ1ⴰm)
        m = R1_challengeᴠ1ⴰct1
        k = OuterOTP.KeyGen(len(m))  # This line changed
        ct = OuterOTP.Encrypt(k, m)
        r = self.adversary.guess(ct)
        return r

proof.add_rewriting_proof_step(RW1Left, RW1Right)

# Now we do a reduction to the ROR security of the outer OTP scheme.
# The reduction acts as an adversary against the ROR security of the outer OTP scheme.
# The reduction must simulate the previous game (which is the slightly rewritten ROR.Real
# security game for DoubleOTP) to the original adversary.
# The technique is for the reduction to do the inner OTP encryption itself, but then
# rely on the ROR security challenger for the outer OTP scheme to do the second
# layer of encryption.
class R1(Crypto.Reduction,
    Generic[SK1, SK2, CT1, CT2, PT1],
    OTP.ROR_Adversary[SK2, CT1, CT2] # This is an ROR adversary for outer OTP
):
    def __init__(self, Scheme: Type[OTP.OTPScheme[SK2, CT1, CT2]], inner_adversary: OTP.ROR_Adversary[Tuple[SK1, SK2], PT1, CT2]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the DoubleOTP adversary
    def challenge(self) -> PT1:
        # Use the DoubleOTP adversary to generate the challenge message.
        m = self.inner_adversary.challenge()
        sk1 = InnerOTP.KeyGen(len(m))
        ct1 = InnerOTP.Encrypt(sk1, m)
        return ct1
    def guess(self, ct2: CT2) -> Crypto.Bit:
        return self.inner_adversary.guess(ct2)

proof.add_distinguishing_proof_step(R1, OTP.ROR, OuterOTP, "OuterOTP")

# We have to do one more rewriting step, again about message lengths and ciphertext,
# basically undoing our first rewriting step.
# We are able to do this rewriting in a simpler search-and-replace way since it
# doesn't require manually reordering any lines.

proof.insert_simple_rewriting_proof_step_after({
    "len(m)": "len(R1_challengeᴠ1ⴰm)"
})


assert proof.check(print_hops=True, print_canonicalizations=True, print_diffs=True, abort_on_failure=False)
print(proof.advantage_bound())

with open(os.path.join('examples', 'DoubleOTP', 'DoubleOTP_is_ROR.tex'), 'w') as fh:
    fh.write(proof.tikz_figure())
