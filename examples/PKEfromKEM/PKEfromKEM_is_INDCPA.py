import os
from typing import Callable, Generic, Tuple, Type

from gamehop.primitives import Crypto, KDF, KEM, OTP, PKE
from gamehop.proofs2 import Proof

from PKEfromKEM import PKEfromKEM, InnerKDF, InnerKEM, InnerOTP, PK, SK, CT_KEM, CT_BODY, SS, PT

# statement we're trying to prove
proof = Proof(PKEfromKEM, PKE.INDCPA)

# game hop:
# replace KEM shared secret with random
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing KEM.INDCPA (with b = 0) from KEM.INDCPA (with b = 1) for KEM
class R1(Crypto.Reduction,
    Generic[PK, SK, CT_KEM, CT_BODY, SS, PT],
    KEM.INDCPA_Adversary[PK, SK, CT_KEM, SS]
):
    def __init__(self, Scheme: Type[KEM.KEMScheme[PK, SK, CT_KEM, SS]], inner_adversary: PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the PKEfromKEM adversary
    def guess(self, pk: PK, ct_kem: CT_KEM, ss: SS) -> Crypto.Bit:
        (m0, m1) = self.inner_adversary.challenge(pk)
        mask = InnerKDF.Eval(ss, "label", len(m0))
        ct_body = InnerOTP.Encrypt(mask, m0)
        r = self.adversary.guess((ct_kem, ct_body))
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

proof.add_distinguishing_proof_step(R1, KEM.INDCPA, InnerKEM, "InnerKEM")

class Rewrite0_Left(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = InnerKEM.Encaps(v1)
        (v5, v6) = v0.adversary.challenge(v1)
        v7 = InnerKEM.uniformSharedSecret()
        v8 = len(v5)
        v9 = InnerKDF.Eval(v7, 'label', v8)
        v10 = len(v5)
        v11 = len(v6)
        v12 = InnerOTP.Encrypt(v9, v5)
        v13 = v10 == v11
        v14 = v0.adversary.guess((v3, v12))
        v15 = Crypto.Bit(0)
        v16 = v14 if v13 else v15
        return v16

class Rewrite0_Right(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = InnerKEM.Encaps(v1)
        (v5, v6) = v0.adversary.challenge(v1)
        v0.k = InnerKDF.uniformKey()
        v8 = len(v5)
        v9 = InnerKDF.Eval(v0.k, 'label', v8)
        v10 = len(v5)
        v11 = len(v6)
        v12 = InnerOTP.Encrypt(v9, v5)
        v13 = v10 == v11
        v14 = v0.adversary.guess((v3, v12))
        v15 = Crypto.Bit(0)
        v16 = v14 if v13 else v15
        return v16

proof.add_rewriting_proof_step(Rewrite0_Left, Rewrite0_Right)

# game hop:
# replace output of KDF with random
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing KDF.KDFsec (with b = 0) from KDF.KDFsec (with b = 1) for KDF
class R2(Crypto.Reduction,
    Generic[PK, SK, CT_KEM, CT_BODY, SS, PT],
    KDF.ROR_Adversary[SS, CT_BODY]
):
    def __init__(self, Scheme: Type[KDF.KDFScheme[SS, CT_BODY]], inner_adversary: PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the PKEfromKEM adversary
    def run(self, o_eval: Callable[[str, int], CT_BODY]) -> Crypto.Bit:
        (pk, sk) = InnerKEM.KeyGen()
        (m0, m1) = self.inner_adversary.challenge(pk)
        (ct_kem, _) = InnerKEM.Encaps(pk)
        mask = o_eval("label", len(m0))
        ct_body = InnerOTP.Encrypt(mask, m0)
        r = self.adversary.guess((ct_kem, ct_body))
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

proof.add_distinguishing_proof_step(R2, KDF.ROR, InnerKDF, "InnerKDF")

class Rewrite1_Left(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = v0.adversary.challenge(v1)
        v5 = len(v3)
        v0.query_list = lists.new_empty_list()
        v6 = len(v3)
        v7 = InnerKDF.uniformOutput(v5)
        v8 = len(v3)
        v0.query_list = lists.set_item(v0.query_list, ('label', v6), v7)
        v9 = v0.query_list.get_item(('label', v8))
        v10 = len(v3)
        v11 = len(v4)
        (v12, v13) = InnerKEM.Encaps(v1)
        v14 = InnerOTP.Encrypt(v9, v3)
        v15 = v10 == v11
        v16 = v0.adversary.guess((v12, v14))
        v17 = Crypto.Bit(0)
        v18 = v16 if v15 else v17
        return v18

class Rewrite1_Right(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = v0.adversary.challenge(v1)
        v5 = len(v3)
        v0.query_list = lists.new_empty_list()
        v6 = len(v3)
        v7 = InnerKDF.uniformOutput(v5)
        v8 = len(v3)
        v0.query_list = lists.set_item(v0.query_list, ('label', v6), v7)
        v9 = v7
        v10 = len(v3)
        v11 = len(v4)
        (v12, v13) = InnerKEM.Encaps(v1)
        v14 = InnerOTP.Encrypt(v9, v3)
        v15 = v10 == v11
        v16 = v0.adversary.guess((v12, v14))
        v17 = Crypto.Bit(0)
        v18 = v16 if v15 else v17
        return v18

proof.add_rewriting_proof_step(Rewrite1_Left, Rewrite1_Right)

class Rewrite2_Left(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = v0.adversary.challenge(v1)
        v5 = len(v3)
        v6 = InnerKDF.uniformOutput(v5)
        v7 = len(v3)
        v8 = len(v4)
        (v9, v10) = InnerKEM.Encaps(v1)
        v11 = InnerOTP.Encrypt(v6, v3)
        v12 = v7 == v8
        v13 = v0.adversary.guess((v9, v11))
        v14 = Crypto.Bit(0)
        v15 = v13 if v12 else v14
        return v15

class Rewrite2_Right(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = v0.adversary.challenge(v1)
        v5 = len(v3)
        v6 = Crypto.BitString.uniformly_random(v5)
        v7 = len(v3)
        v8 = len(v4)
        (v0.ct_kem, v10) = InnerKEM.Encaps(v1)
        v11 = InnerOTP.Encrypt(v6, v3)
        v12 = v7 == v8
        v13 = v0.adversary.guess((v0.ct_kem, v11))
        v14 = Crypto.Bit(0)
        v15 = v13 if v12 else v14
        return v15

proof.add_rewriting_proof_step(Rewrite2_Left, Rewrite2_Right)

# game hop:
# encrypt m1 rather than m0 using the OTP
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

class Rewrite3_Left(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = v0.adversary.challenge(v1)
        v5 = len(v4)
        v6 = Crypto.BitString.uniformly_random(v5)
        v7 = len(v3)
        v8 = len(v4)
        (v0.ct_kem, v9) = InnerKEM.Encaps(v1)
        v10 = InnerOTP.Encrypt(v6, v4)
        v11 = v7 == v8
        v12 = v0.adversary.guess((v0.ct_kem, v10))
        v13 = Crypto.Bit(0)
        v14 = v12 if v11 else v13
        return v14

class Rewrite3_Right(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = v0.adversary.challenge(v1)
        v5 = len(v4)
        v6 = InnerKDF.uniformOutput(v5)
        v7 = len(v3)
        v8 = len(v4)
        (v0ct_kem, v9) = InnerKEM.Encaps(v1)
        v10 = InnerOTP.Encrypt(v6, v4)
        v11 = v7 == v8
        v12 = v0.adversary.guess((v0ct_kem, v10))
        v13 = Crypto.Bit(0)
        v14 = v12 if v11 else v13
        return v14

proof.add_rewriting_proof_step(Rewrite3_Left, Rewrite3_Right)

class Rewrite4_Left(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = v0.adversary.challenge(v1)
        v5 = len(v4)
        v0.query_list = lists.new_empty_list()
        v6 = len(v3)
        v7 = InnerKDF.uniformOutput(v5)
        v8 = len(v3)
        v0.query_list = lists.set_item(v0.query_list, ('label', v6), v7)
        v9 = v7
        v10 = len(v3)
        v11 = len(v4)
        (v12, v13) = InnerKEM.Encaps(v1)
        v14 = InnerOTP.Encrypt(v9, v4)
        v15 = v10 == v11
        v16 = v0.adversary.guess((v12, v14))
        v17 = Crypto.Bit(0)
        v18 = v16 if v15 else v17
        return v18

class Rewrite4_Right(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = v0.adversary.challenge(v1)
        v5 = len(v4)
        v0.query_list = lists.new_empty_list()
        v6 = len(v4)
        v7 = InnerKDF.uniformOutput(v5)
        v8 = len(v4)
        v0.query_list = lists.set_item(v0.query_list, ('label', v6), v7)
        v9 = v0.query_list.get_item(('label', v8))
        v10 = len(v3)
        v11 = len(v4)
        (v12, v13) = InnerKEM.Encaps(v1)
        v14 = InnerOTP.Encrypt(v9, v4)
        v15 = v10 == v11
        v16 = v0.adversary.guess((v12, v14))
        v17 = Crypto.Bit(0)
        v18 = v16 if v15 else v17
        return v18

proof.add_rewriting_proof_step(Rewrite4_Left, Rewrite4_Right)

# game hop:
# replace output of KDF with Real
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing KDF.KDFsec (with b = 0) from KDF.KDFsec (with b = 1) for KDF
class R4(Crypto.Reduction,
    Generic[PK, SK, CT_KEM, CT_BODY, SS, PT],
    KDF.ROR_Adversary[SS, CT_BODY]
):
    def __init__(self, Scheme: Type[KDF.KDFScheme[SS, CT_BODY]], inner_adversary: PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the PKEfromKEM adversary
    def run(self, o_eval: Callable[[str, int], CT_BODY]) -> Crypto.Bit:
        (pk, sk) = InnerKEM.KeyGen()
        (m0, m1) = self.inner_adversary.challenge(pk)
        (ct_kem, _) = InnerKEM.Encaps(pk)
        mask = o_eval("label", len(m1))
        ct_body = InnerOTP.Encrypt(mask, m1)
        r = self.adversary.guess((ct_kem, ct_body))
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

proof.add_distinguishing_proof_step(R4, KDF.ROR, InnerKDF, "InnerKDF", reverse_direction = True)

class Rewrite5_Left(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = v0.adversary.challenge(v1)
        v0.k = InnerKDF.uniformKey()
        v5 = len(v4)
        v6 = InnerKDF.Eval(v0.k, 'label', v5)
        v7 = len(v3)
        v8 = len(v4)
        (v9, v10) = InnerKEM.Encaps(v1)
        v11 = InnerOTP.Encrypt(v6, v4)
        v12 = v7 == v8
        v13 = v0.adversary.guess((v9, v11))
        v14 = Crypto.Bit(0)
        v15 = v13 if v12 else v14
        return v15

class Rewrite5_Right(Crypto.Game, Generic[PK, SK, CT_KEM, CT_BODY, SS, PT]):

    def __init__(v0, v1: Type[PKE.INDCPA_Adversary[PK, SK, Tuple[CT_KEM, CT_BODY], PT]]):
        v0.Scheme = PKEfromKEM
        v0.adversary = v1(PKEfromKEM)

    def main(v0) -> Crypto.Bit:
        (v1, v2) = InnerKEM.KeyGen()
        (v3, v4) = v0.adversary.challenge(v1)
        v0k = InnerKEM.uniformSharedSecret()
        v5 = len(v4)
        v6 = InnerKDF.Eval(v0k, 'label', v5)
        v7 = len(v3)
        v8 = len(v4)
        (v9, v10) = InnerKEM.Encaps(v1)
        v11 = InnerOTP.Encrypt(v6, v4)
        v12 = v7 == v8
        v13 = v0.adversary.guess((v9, v11))
        v14 = Crypto.Bit(0)
        v15 = v13 if v12 else v14
        return v15

proof.add_rewriting_proof_step(Rewrite5_Left, Rewrite5_Right)

# game hop:
# replace KEM shared secret with real
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing KEM.INDCPA (with b = 0) from KEM.INDCPA (with b = 1) for KEM
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

assert proof.check(print_hops=True, print_canonicalizations=True, print_diffs=True, abort_on_failure=False)
print("Theorem: ")
print(proof.advantage_bound())

with open(os.path.join('examples', 'PKEfromKEM', 'PKEfromKEM_is_INDCPA.tex'), 'w') as fh:
    fh.write(proof.tikz_figure())
