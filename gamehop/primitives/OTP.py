from abc import ABC
from typing import Sized, Tuple, Type, Union

from . import Crypto

class OTPScheme(Crypto.Scheme):
    class Message(Sized): pass
    @staticmethod
    def Encrypt(key: Crypto.BitString, msg: Message) -> Crypto.BitString: pass
    @staticmethod
    def Decrypt(key: Crypto.BitString, ctxt: Crypto.BitString) -> Message: pass

class IND_Adversary(Crypto.Adversary):
    def __init__(self, Scheme: Type[OTPScheme]): pass
    def challenge(self) -> Tuple[OTPScheme.Message, OTPScheme.Message]: pass
    def guess(self, ct: Crypto.BitString) -> Crypto.Bit: pass

class IND_Left(Crypto.Game):
    def __init__(self, Scheme: Type[OTPScheme], Adversary: Type[IND_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        adversary = self.Adversary(self.Scheme)
        (m0, m1) = adversary.challenge()
        k = Crypto.BitString.uniformly_random(len(m0))
        ct = self.Scheme.Encrypt(k, m0)
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

class IND_Right(Crypto.Game):
    def __init__(self, Scheme: Type[OTPScheme], Adversary: Type[IND_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        adversary = self.Adversary(self.Scheme)
        (m0, m1) = adversary.challenge()
        k = Crypto.BitString.uniformly_random(len(m0))
        ct = self.Scheme.Encrypt(k, m1)
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

IND = Crypto.DistinguishingExperimentLeftOrRight(IND_Left, IND_Right, IND_Adversary)
