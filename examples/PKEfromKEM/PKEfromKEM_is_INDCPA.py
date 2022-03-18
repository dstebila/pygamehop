import os
from typing import Callable, Generic, Tuple, Type, TypeVar

from gamehop.primitives import Crypto, KDF, KEM, OTP, PKE
from gamehop.proofs2 import Proof

from PKEfromKEM import PKEfromKEM, InnerKDF, InnerKEM, InnerOTP, PK, SK, CT_KEM, CT_BODY, SS, PT

# Theorem: PKEfromKEM[InnerKDF, InnerKEM, InnerOTP] is IND-CPA-secure if TODO.
proof = Proof(PKEfromKEM, PKE.INDCPA)

# Game 0 is the PKEfromKEM scheme inlined into PKE.INDCPA_Left.

# Game 1 is uses a random KEM shared secret, rather than the real value.
# Game 0 and Game 1 are indistinguishable under the assumption that InnerKEM is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against InnerKEM,
# and checking that this reduction, inlined into the IND-CPA experiment for InnerKEM,
# is equivalent to either Game 0 or Game 1.
class R1(Crypto.Reduction,
    Generic[PK, SK, CT_KEM, CT_BODY, SS, PT],
    KEM.INDCPA_Adversary[PK, SK, CT_KEM, SS]
):
    def __init__(self, Scheme: Type[KEM.KEMScheme[PK, SK, CT_KEM, SS]], inner_adversary: PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the PKEfromKEM adversary
    def guess(self, pk: PK, ct_kem: CT_KEM, ss: SS) -> Crypto.Bit:
        (m0, m1) = self.inner_adversary.challenge(pk)
        # use the shared secret from the InnerKEM IND-CPA challenger
        mask = InnerKDF.Eval(ss, "label", len(m0))
        ct_body = InnerOTP.Encrypt(mask, m0)
        r = self.adversary.guess((ct_kem, ct_body))
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

proof.add_distinguishing_proof_step(R1, KEM.INDCPA, InnerKEM, "InnerKEM")

# Game 2 is a rewriting step that tells the prover that a uniform shared secret from InnerKEM is 
# good as a uniform key for InnerKDF.
proof.insert_simple_rewriting_proof_step_after({
    "InnerKEM.uniformSharedSecret": "InnerKDF.uniformKey"
})

# Game 3 replaces the output of the KDF with a random value.
# Game 2 and Game 3 are indistinguishable under the assumption that InnerKDF is ROR1-secure.
# This is chosen by constructing a reduction that acts an ROR1-adversary against InnerKDF,
# and checking that this reduction, inlined into the ROR1 experiment for InnerKDF,
# is equivalent to either Game 2 or Game 3.
class R2(Crypto.Reduction,
    Generic[PK, SK, CT_KEM, CT_BODY, SS, PT],
    KDF.ROR1_Adversary[SS, CT_BODY]
):
    def __init__(self, Scheme: Type[KDF.KDFScheme[SS, CT_BODY]], inner_adversary: PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the PKEfromKEM adversary
    def challenge(self) -> Tuple[str, int]:
        (pk, sk) = InnerKEM.KeyGen()
        (self.m0, self.m1) = self.inner_adversary.challenge(pk)
        (self.ct_kem, _) = InnerKEM.Encaps(pk)
        return ("label", len(self.m0))
    def guess(self, mask) -> Crypto.Bit:
        ct_body = InnerOTP.Encrypt(mask, self.m0)
        r = self.adversary.guess((self.ct_kem, ct_body))
        ret = r if len(self.m0) == len(self.m1) else Crypto.Bit(0)
        return ret

proof.add_distinguishing_proof_step(R2, KDF.ROR1, InnerKDF, "InnerKDF")

# Game 4 is a rewriting step that tells the prover that the uniform output of a KDF
# is good as a uniform key for the OTP.
proof.insert_simple_rewriting_proof_step_after({
    "InnerKDF.uniformOutput": "Crypto.BitString.uniformly_random"
})

# Game 5 encrypts message m1 rather than m0 using the OTP.
# Game 4 and Game 5 are indistinguishable under the assumption that InnerOTP is IND-secure.
# This is chosen by constructing a reduction that acts an IND-adversary against InnerOTP,
# and checking that this reduction, inlined into the IND experiment for InnerOTP,
# is equivalent to either Game 4 or Game 5.
class R3(Crypto.Reduction,
    Generic[PK, SK, CT_KEM, CT_BODY, SS, PT],
    OTP.IND_Adversary[CT_BODY, PT, CT_BODY]
):
    def __init__(self, Scheme: Type[OTP.OTPScheme[CT_BODY, PT, CT_BODY]], inner_adversary: PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the PKEfromKEM adversary
    def challenge(self):
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = self.inner_adversary.challenge(v1)
        (self.ct_kem, _) = InnerKEM.Encaps(v1)
        return (v3, v4)
    def guess(self, ct_body):
        return self.inner_adversary.guess((self.ct_kem, ct_body))

proof.add_distinguishing_proof_step(R3, OTP.IND, InnerOTP, "InnerOTP")

# Now we have to "undo" everything in the proof, to wind our way back to a normal encryption of m1.

# Game 6 is a rewriting step that tells the prover that the uniform output of a KDF
# is good as a uniform key for the OTP.
proof.insert_simple_rewriting_proof_step_after({
    "Crypto.BitString.uniformly_random": "InnerKDF.uniformOutput"
})

# Game 7 uses a real value for the output of the KDF rather than random.
# Game 6 and Game 7 are indistinguishable under the assumption that InnerKDF is ROR1-secure.
# This is chosen by constructing a reduction that acts an ROR1-adversary against InnerKDF,
# and checking that this reduction, inlined into the ROR1 experiment for InnerKDF,
# is equivalent to either Game 7 or Game 6.
class R4(Crypto.Reduction,
    Generic[PK, SK, CT_KEM, CT_BODY, SS, PT],
    KDF.ROR1_Adversary[SS, CT_BODY]
):
    def __init__(self, Scheme: Type[KDF.KDFScheme[SS, CT_BODY]], inner_adversary: PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the PKEfromKEM adversary
    def challenge(self) -> Tuple[str, int]:
        (pk, sk) = InnerKEM.KeyGen()
        (self.m0, self.m1) = self.inner_adversary.challenge(pk)
        (self.ct_kem, _) = InnerKEM.Encaps(pk)
        return ("label", len(self.m1))
    def guess(self, mask) -> Crypto.Bit:
        ct_body = InnerOTP.Encrypt(mask, self.m1)
        r = self.adversary.guess((self.ct_kem, ct_body))
        ret = r if len(self.m0) == len(self.m1) else Crypto.Bit(0)
        return ret

proof.add_distinguishing_proof_step(R4, KDF.ROR1, InnerKDF, "InnerKDF", reverse_direction = True)

# Game 8 is a rewriting step that tells the prover that a uniform shared secret from InnerKEM is 
# good as a uniform key for InnerKDF.
proof.insert_simple_rewriting_proof_step_after({
    "InnerKDF.uniformKey": "InnerKEM.uniformSharedSecret"
})

# Game 9 is uses a real KEM shared secret, rather than the random value used in game 8.
# Game 8 and Game 9 are indistinguishable under the assumption that InnerKEM is IND-CPA-secure.
# This is chosen by constructing a reduction that acts an IND-CPA-adversary against InnerKEM,
# and checking that this reduction, inlined into the IND-CPA experiment for InnerKEM,
# is equivalent to either Game 9 or Game 8.
class R5(Crypto.Reduction,
    Generic[PK, SK, CT_KEM, CT_BODY, SS, PT],
    KEM.INDCPA_Adversary[PK, SK, CT_KEM, SS]
):
    def __init__(self, Scheme: Type[KEM.KEMScheme[PK, SK, CT_KEM, SS]], inner_adversary: PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the PKEfromKEM adversary
    def guess(self, pk: PK, ct_kem: CT_KEM, ss: SS) -> Crypto.Bit:
        (m0, m1) = self.inner_adversary.challenge(pk)
        mask = InnerKDF.Eval(ss, "label", len(m1))
        ct_body = InnerOTP.Encrypt(mask, m1)
        r = self.adversary.guess((ct_kem, ct_body))
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

proof.add_distinguishing_proof_step(R5, KEM.INDCPA, InnerKEM, "InnerKEM", reverse_direction = True)

assert proof.check(print_hops=True, print_canonicalizations=True, print_diffs=True, abort_on_failure=True)
print("Theorem:")
print(proof.advantage_bound())

with open(os.path.join('examples', 'PKEfromKEM', 'PKEfromKEM_is_INDCPA.tex'), 'w') as fh:
    fh.write(proof.tikz_figure())
