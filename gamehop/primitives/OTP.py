from typing import Sized, Tuple, Type

from . import Crypto

class OTPScheme(Crypto.Scheme):
    class Message(Sized): pass
    @staticmethod
    def Encrypt(key: Crypto.BitString, msg: Message) -> Crypto.BitString: pass
    @staticmethod
    def Decrypt(key: Crypto.BitString, ctxt: Crypto.BitString) -> Message: pass

class IND_Adversary(Crypto.Adversary):
    @staticmethod
    def challenge(Scheme: Type[OTPScheme]) -> Tuple[OTPScheme.Message, OTPScheme.Message, Tuple]: pass
    @staticmethod
    def guess(Scheme: Type[OTPScheme], state: Tuple, ct: Crypto.BitString) -> Crypto.Bit: pass

class IND_Left(Crypto.Game):
    def __init__(self, Scheme: Type[OTPScheme], Adversary: Type[IND_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        (m0, m1, st) = self.Adversary.challenge(self.Scheme)
        k = Crypto.BitString.uniformly_random(len(m0))
        ct = self.Scheme.Encrypt(k, m0)
        r = self.Adversary.guess(self.Scheme, st, ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

class IND_Right(Crypto.Game):
    def __init__(self, Scheme: Type[OTPScheme], Adversary: Type[IND_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        (m0, m1, st) = self.Adversary.challenge(self.Scheme)
        k = Crypto.BitString.uniformly_random(len(m0))
        ct = self.Scheme.Encrypt(k, m1)
        r = self.Adversary.guess(self.Scheme, st, ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

IND = Crypto.DistinguishingExperimentLeftOrRight(IND_Left, IND_Right, IND_Adversary)
