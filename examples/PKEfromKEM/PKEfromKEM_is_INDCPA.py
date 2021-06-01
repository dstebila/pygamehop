from typing import Tuple

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
        return r

proof.addDistinguishingProofStep(KEM.INDCPA, KEMScheme, R01)

# game hop:
# replace output of KDF with random
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing KDF.KDFsec (with b = 0) from KDF.KDFsec (with b = 1) for KDF
class R12(KDF.OTKDFsec_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, kem: KEMScheme) -> None:
        self.adversary = adversary
        self.kem = kem
    def setup(self, kdf: KDFScheme) -> None:
        self.kdf = kdf
        return None
    def phase1(self) -> Tuple[str, int]:
        (pk, sk) = self.kem.KeyGen()
        (self.m0, m1) = self.adversary.challenge(pk)
        (self.ct1, _) = self.kem.Encaps(pk)
        return ("label", len(self.m0))
    def phase2(self, kk: Crypto.ByteString) -> Crypto.Bit:
        ct2 = kk ^ self.m0
        r = self.adversary.guess((self.ct1, ct2))
        return r

proof.addDistinguishingProofStep(KDF.OTKDFsec, KDFScheme, R12, renaming = {'Key': 'SharedSecret'})

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
    def guess(self, ct: Crypto.ByteString) -> Crypto.Bit:
        return self.adversary.guess((self.ct1, ct))

proof.addDistinguishingProofStep(OTP.OTIND, OTPScheme, R23)

# game hop:
# replace output of KDF with real
# proven by constructing reduction from distinguishing the previous game and this game to distinguishing KDF.KDFsec (with b = 1) from KDF.KDFsec (with b = 0) for KDF
class R34(KDF.OTKDFsec_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, kem: KEMScheme) -> None:
        self.adversary = adversary
        self.kem = kem
    def setup(self, kdf: KDFScheme) -> None:
        self.kdf = kdf
        return None
    def phase1(self) -> Tuple[str, int]:
        (pk, sk) = self.kem.KeyGen()
        (m0, self.m1) = self.adversary.challenge(pk)
        (self.ct1, _) = self.kem.Encaps(pk)
        return ("label", len(self.m1))
    def phase2(self, kk: Crypto.ByteString) -> Crypto.Bit:
        ct2 = kk ^ self.m1
        r = self.adversary.guess((self.ct1, ct2))
        return r

proof.addDistinguishingProofStep(KDF.OTKDFsec, KDFScheme, R34, reverseDirection = True, renaming = {'Key': 'SharedSecret'})

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
        return r

proof.addDistinguishingProofStep(KEM.INDCPA, KEMScheme, R45, reverseDirection = True)

assert proof.check(print_hops=True, print_canonicalizations=True)
print()
print(proof.advantage_bound())
