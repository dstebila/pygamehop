from abc import ABC
from typing import Callable, Sized, Tuple, Type, Union

from . import Crypto

class PKEScheme(Crypto.Scheme, ABC):
    class PublicKey(): pass
    class SecretKey(): pass
    class Ciphertext(): pass
    class Message(Sized): pass
    @staticmethod
    def KeyGen() -> Tuple[PublicKey, SecretKey]: pass
    @staticmethod
    def Encrypt(pk: PublicKey, msg: Message) -> Ciphertext: pass
    @staticmethod
    def Decrypt(sk: SecretKey, ct: Ciphertext) -> Union[Message, Crypto.Reject]: pass

class INDCPA_Adversary(Crypto.Adversary):
    @staticmethod
    def challenge(Scheme: Type[PKEScheme], pk: PKEScheme.PublicKey) -> Tuple[PKEScheme.Message, PKEScheme.Message, Tuple]: pass
    @staticmethod
    def guess(Scheme: Type[PKEScheme], state: Tuple, ct: PKEScheme.Ciphertext) -> Crypto.Bit: pass

class INDCPA_Left(Crypto.Game):
    def __init__(self, Scheme: Type[PKEScheme], Adversary: Type[INDCPA_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        (m0, m1, st) = self.Adversary.challenge(self.Scheme, pk)
        ct = self.Scheme.Encrypt(pk, m0)
        r = self.Adversary.guess(self.Scheme, st, ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

class INDCPA_Right(Crypto.Game):
    def __init__(self, Scheme: Type[PKEScheme], Adversary: Type[INDCPA_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        (m0, m1, st) = self.Adversary.challenge(self.Scheme, pk)
        ct = self.Scheme.Encrypt(pk, m1)
        r = self.Adversary.guess(self.Scheme, st, ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

INDCPA = Crypto.DistinguishingExperimentLeftOrRight(INDCPA_Left, INDCPA_Right, INDCPA_Adversary)

class INDCCA2_Adversary(Crypto.Adversary):
    @staticmethod
    def challenge(Scheme: Type[PKEScheme], pk: PKEScheme.PublicKey, o_decrypt: Callable[[PKEScheme.Ciphertext], Union[PKEScheme.Message, Crypto.Reject]]) -> Tuple[PKEScheme.Message, PKEScheme.Message, Tuple]: pass
    @staticmethod
    def guess(Scheme: Type[PKEScheme], state: Tuple, ct: PKEScheme.Ciphertext, o_decrypt: Callable[[PKEScheme.Ciphertext], Union[PKEScheme.Message, Crypto.Reject]]) -> Crypto.Bit: pass

class INDCCA2_Left(Crypto.Game):
    def __init__(self, Scheme: Type[PKEScheme], Adversary: Type[INDCCA2_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        self.sk = sk
        self.ctstar = None
        (m0, m1, st) = self.Adversary.challenge(self.Scheme, pk, self.o_decrypt)
        self.ctstar = self.Scheme.Encrypt(pk, m0)
        r = self.Adversary.guess(self.Scheme, st, self.ctstar, self.o_decrypt)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret
    def o_decrypt(self, ct: PKEScheme.Ciphertext) -> Union[PKEScheme.Message, Crypto.Reject]:
        ret: Union[PKEScheme.Message, Crypto.Reject] = Crypto.Reject()
        if ct != self.ctstar: ret = self.Scheme.Decrypt(self.sk, ct)
        return ret

class INDCCA2_Right(Crypto.Game):
    def __init__(self, Scheme: Type[PKEScheme], Adversary: Type[INDCCA2_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        (pk, sk) = self.Scheme.KeyGen()
        self.sk = sk
        self.ctstar = None
        (m0, m1, st) = self.Adversary.challenge(self.Scheme, pk, self.o_decrypt)
        self.ctstar = self.Scheme.Encrypt(pk, m1)
        r = self.Adversary.guess(self.Scheme, st, self.ctstar, self.o_decrypt)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret
    def o_decrypt(self, ct: PKEScheme.Ciphertext) -> Union[PKEScheme.Message, Crypto.Reject]:
        ret: Union[PKEScheme.Message, Crypto.Reject] = Crypto.Reject()
        if ct != self.ctstar: ret = self.Scheme.Decrypt(self.sk, ct)
        return ret

INDCCA2 = Crypto.DistinguishingExperimentLeftOrRight(INDCCA2_Left, INDCCA2_Right, INDCCA2_Adversary)
