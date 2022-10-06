from typing import Generic, Sized, Tuple, Type, TypeVar

from . import Crypto

Key = TypeVar('Key')
Message = TypeVar('Message', bound=Sized)
Ciphertext = TypeVar('Ciphertext', bound=Sized)

class OTPScheme(Crypto.Scheme, Generic[Key, Message, Ciphertext]):
    @staticmethod
    def KeyGen(keylen: int) -> Key: pass
    @staticmethod
    def Encrypt(key: Key, msg: Message) -> Ciphertext: pass
    @staticmethod
    def Decrypt(key: Key, ctxt: Ciphertext) -> Message: pass

class IND_Adversary(Crypto.Adversary, Generic[Key, Message, Ciphertext]):
    def challenge(self) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext) -> Crypto.Bit: pass

class IND_Left(Crypto.Game, Generic[Key, Message, Ciphertext]):
    def __init__(self, Scheme: Type[OTPScheme[Key, Message, Ciphertext]], Adversary: Type[IND_Adversary[Key, Message, Ciphertext]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        (m0, m1) = self.adversary.challenge()
        k = self.Scheme.KeyGen(len(m0))
        ct = self.Scheme.Encrypt(k, m0)
        r = self.adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

class IND_Right(Crypto.Game, Generic[Key, Message, Ciphertext]):
    def __init__(self, Scheme: Type[OTPScheme[Key, Message, Ciphertext]], Adversary: Type[IND_Adversary[Key, Message, Ciphertext]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        (m0, m1) = self.adversary.challenge()
        k = self.Scheme.KeyGen(len(m1))
        ct = self.Scheme.Encrypt(k, m1)
        r = self.adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

IND = Crypto.DistinguishingExperimentLeftOrRight("OTP", "IND", IND_Left, IND_Right, IND_Adversary)

class ROR_Adversary(Crypto.Adversary, Generic[Key, Message, Ciphertext]):
    def challenge(self) -> Message: pass
    def guess(self, ct: Ciphertext) -> Crypto.Bit: pass

class ROR_Real(Crypto.Game, Generic[Key, Message, Ciphertext]):
    def __init__(self, Scheme: Type[OTPScheme[Key, Message, Ciphertext]], Adversary: Type[ROR_Adversary[Key, Message, Ciphertext]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        m = self.adversary.challenge()
        k = self.Scheme.KeyGen(len(m))
        ct = self.Scheme.Encrypt(k, m)
        r = self.adversary.guess(ct)
        return r

class ROR_Random(Crypto.Game, Generic[Key, Message, Ciphertext]):
    def __init__(self, Scheme: Type[OTPScheme[Key, Message, Ciphertext]], Adversary: Type[ROR_Adversary[Key, Message, Ciphertext]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        m = self.adversary.challenge()
        ct = Crypto.BitString.uniformly_random(len(m))
        r = self.adversary.guess(ct)
        return r

ROR = Crypto.DistinguishingExperimentLeftOrRight("OTP", "ROR", ROR_Real, ROR_Random, ROR_Adversary)
