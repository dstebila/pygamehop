from typing import Sized, Tuple, Type, Union

from . import Crypto

class Message(Sized): pass

class OTP(Crypto.Scheme):
    def Encrypt(self, key: Crypto.BitString, msg: Message) -> Crypto.BitString: pass
    def Decrypt(self, key: Crypto.BitString, ctxt: Crypto.BitString) -> Message: pass

class IND_Adversary(Crypto.Adversary):
    def __init__(self, otp: OTP): pass
    def challenge(self) -> Tuple[Message, Message]: pass
    def guess(self, ct: Crypto.BitString) -> Crypto.Bit: pass

class IND_Left(Crypto.Game):
    def main(self, otp: OTP, Adversary: Type[IND_Adversary]) -> Crypto.Bit:
        adversary = Adversary(otp)
        (m0, m1) = adversary.challenge()
        k = Crypto.BitString.uniformly_random(len(m0))
        ct = otp.Encrypt(k, m0)
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

class IND_Right(Crypto.Game):
    def main(self, otp: OTP, Adversary: Type[IND_Adversary]) -> Crypto.Bit:
        adversary = Adversary(otp)
        (m0, m1) = adversary.challenge()
        k = Crypto.BitString.uniformly_random(len(m0))
        ct = otp.Encrypt(k, m1)
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

IND = Crypto.DistinguishingExperimentLeftOrRight(IND_Left, IND_Right, IND_Adversary)
