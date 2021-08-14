import os
import subprocess
from typing import Callable, Tuple

from gamehop.primitives import Crypto, PKE, KEM, KDF, OTP
from gamehop.proofs import Proof

import PKEfromKEM

PKEINDCPA_adversary = PKE.PKEINDCPA_adversary
KDFScheme = KDF.KDFScheme
KEMScheme = KEM.KEMScheme
SharedSecret = KEM.SharedSecret
OTPScheme = OTP.OTPScheme

# statement we're trying to prove
proof = Proof(PKE.INDCPA, PKEfromKEM.Scheme, PKEINDCPA_adversary)

# game hop:
# replace KEM shared secret with random
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing KEM.INDCPA (with b = 0) from KEM.INDCPA (with b = 1) for KEM
class R01(KEM.KEMINDCPA_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, kdf: KDFScheme) -> None:
        self.adversary = adversary
        self.kdf = kdf
    def setup(self, kem: KEMScheme) -> None:        
        self.kem = kem
        return None
    def guess(self, pk: KEM.PublicKey, ct: KEM.Ciphertext, ss: KEM.SharedSecret) -> Crypto.Bit:
        (m0, m1) = self.adversary.challenge(pk)
        mask = self.kdf.KDF(ss, "label", len(m0))
        ctprime = mask ^ m0
        r = self.adversary.guess((ct, ctprime))
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

proof.addDistinguishingProofStep(KEM.INDCPA, KEMScheme, R01)

# game hop:
# replace output of KDF with random
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing KDF.KDFsec (with b = 0) from KDF.KDFsec (with b = 1) for KDF
class R12(KDF.KDFsec_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, kem: KEMScheme) -> None:
        self.adversary = adversary
        self.kem = kem
    def setup(self, kdf: KDFScheme) -> None:
        self.kdf = kdf
        return None
    def run(self, o_eval: Callable[[str, int], Crypto.BitString]) -> Crypto.Bit:
        (pk, sk) = self.kem.KeyGen()
        (self.m0, m1) = self.adversary.challenge(pk)
        (self.ct1, _) = self.kem.Encaps(pk)
        mask = o_eval("label", len(self.m0))
        ct2 = mask ^ self.m0
        r = self.adversary.guess((self.ct1, ct2))
        ret = r if len(self.m0) == len(m1) else Crypto.Bit(0)
        return ret

proof.addDistinguishingProofStep(KDF.KDFsec, KDFScheme, R12, renaming = {'Key': 'SharedSecret'})

# game hop:
# XOR the mask with m1 rather than m0
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing PKE.INDCPA (with b = 0) from PKE.INDCPA (with b = 1) for OTP
class R23(OTP.OTIND_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, kem: KEMScheme, kdf: KDFScheme) -> None:
        self.adversary = adversary
        self.kem = kem
    def setup(self, otp: OTPScheme) -> None:
        self.otp = otp
        return None
    def challenge(self) -> Tuple[OTP.Message, OTP.Message]:
        (pk, sk) = self.kem.KeyGen()
        (m0, m1) = self.adversary.challenge(pk)
        (self.ct1, _) = self.kem.Encaps(pk)
        return (m0, m1)
    def guess(self, ct: Crypto.BitString) -> Crypto.Bit:
        return self.adversary.guess((self.ct1, ct))

proof.addDistinguishingProofStep(OTP.OTIND, OTPScheme, R23)

# game hop:
# replace output of KDF with real
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing KDF.KDFsec (with b = 1) from KDF.KDFsec (with b = 0) for KDF
class R34(KDF.KDFsec_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, kem: KEMScheme) -> None:
        self.adversary = adversary
        self.kem = kem
    def setup(self, kdf: KDFScheme) -> None:
        self.kdf = kdf
        return None
    def run(self, o_eval: Callable[[str, int], Crypto.BitString]) -> Crypto.Bit:
        (pk, sk) = self.kem.KeyGen()
        (m0, self.m1) = self.adversary.challenge(pk)
        (self.ct1, _) = self.kem.Encaps(pk)
        mask = o_eval("label", len(self.m1))
        ct2 = mask ^ self.m1
        r = self.adversary.guess((self.ct1, ct2))
        ret = r if len(m0) == len(self.m1) else Crypto.Bit(0)
        return ret

proof.addDistinguishingProofStep(KDF.KDFsec, KDFScheme, R34, reverseDirection = True, renaming = {'Key': 'SharedSecret'})

# game hop:
# replace KEM shared secret with random
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing KEM.INDCPA (with b = 1) from KEM.INDCPA (with b = 0) for KEM
class R45(KEM.KEMINDCPA_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, kdf: KDFScheme) -> None:
        self.adversary = adversary
        self.kdf = kdf
    def setup(self, kem: KEMScheme) -> None:        
        self.kem = kem
        return None
    def guess(self, pk: KEM.PublicKey, ct: KEM.Ciphertext, ss: KEM.SharedSecret) -> Crypto.Bit:
        (m0, m1) = self.adversary.challenge(pk)
        mask = self.kdf.KDF(ss, "label", len(m1))
        ctprime = mask ^ m1
        r = self.adversary.guess((ct, ctprime))
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

proof.addDistinguishingProofStep(KEM.INDCPA, KEMScheme, R45, reverseDirection = True)

assert proof.check(print_hops=True, print_canonicalizations=True)
print()
print(proof.advantage_bound())

with open(os.path.join('examples', 'PKEfromKEM', 'PKEfromKEM_is_INDCPA.tex'), 'w') as fh:
    fh.write(proof.tikz_figure())

subprocess.run(
    ['pdflatex', 'PKEfromKEM_is_INDCPA.tex'],
    cwd = os.path.join('examples', 'PKEfromKEM')
)
