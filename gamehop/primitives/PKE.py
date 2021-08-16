from abc import ABC
from typing import Sized, Tuple, Type, Union

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
    def __init__(self, Scheme: Type[PKEScheme]): pass
    def challenge(self, pk: PKEScheme.PublicKey) -> Tuple[PKEScheme.Message, PKEScheme.Message]: pass
    def guess(self, ct: PKEScheme.Ciphertext) -> Crypto.Bit: pass

class INDCPA_Left(Crypto.Game):
    def __init__(self, Scheme: Type[PKEScheme], Adversary: Type[INDCPA_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        adversary = self.Adversary(self.Scheme)
        (pk, sk) = self.Scheme.KeyGen()
        self.sk = sk
        (m0, m1) = adversary.challenge(pk)
        ct = self.Scheme.Encrypt(pk, m0)
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

class INDCPA_Right(Crypto.Game):
    def __init__(self, Scheme: Type[PKEScheme], Adversary: Type[INDCPA_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        adversary = self.Adversary(self.Scheme)
        (pk, sk) = self.Scheme.KeyGen()
        self.sk = sk
        (m0, m1) = adversary.challenge(pk)
        ct = self.Scheme.Encrypt(pk, m1)
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

INDCPA = Crypto.DistinguishingExperimentLeftOrRight(INDCPA_Left, INDCPA_Right, INDCPA_Adversary)
