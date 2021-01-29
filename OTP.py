from abc import ABC
from typing import Tuple, Union

import Crypto

class Scheme(ABC):
    @staticmethod
    def Enc(k: Crypto.UniformlyRandomByteString, m: Crypto.ByteString) -> Crypto.ByteString:
        return k ^ m

class OTP_adversary(ABC):
    def setkey(self) -> Crypto.UniformlyRandomByteString: pass
    def challenge(self) -> Tuple[Crypto.ByteString, Crypto.ByteString]: pass
    def guess(self, ct: Crypto.ByteString) -> Crypto.Bit: pass

def OTPCPA0(otp: Scheme, adversary: OTP_adversary) -> Crypto.Bit:
    mask = adversary.setkey()
    (m0, m1) = adversary.challenge()
    ct = otp.Enc(mask, m0)
    return adversary.guess(ct)

def OTPCPA1(otp: Scheme, adversary: OTP_adversary) -> Crypto.Bit:
    mask = adversary.setkey()
    (m0, m1) = adversary.challenge()
    ct = otp.Enc(mask, m1)
    return adversary.guess(ct)
