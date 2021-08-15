from typing import Sized, Tuple, Type, Union

from . import Crypto

class PublicKey(): pass
class SecretKey(): pass
class Ciphertext(): pass
class Message(Sized): pass

class PKE(Crypto.Scheme):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encrypt(self, pk: PublicKey, msg: Message) -> Ciphertext: pass
    def Decrypt(self, sk: SecretKey, ct: Ciphertext) -> Union[Message, Crypto.Reject]: pass

class INDCPA_Adversary(Crypto.Adversary):
    def __init__(self, pke: PKE): pass
    def challenge(self, pk: PublicKey) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext) -> Crypto.Bit: pass

class INDCPA_Left(Crypto.Game):
    def main(self, pke: PKE, Adversary: Type[INDCPA_Adversary]) -> Crypto.Bit:
        adversary = Adversary(pke)
        (pk, sk) = pke.KeyGen()
        (m0, m1) = adversary.challenge(pk)
        ct = pke.Encrypt(pk, m0)
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

class INDCPA_Right(Crypto.Game):
    def main(self, pke: PKE, Adversary: Type[INDCPA_Adversary]) -> Crypto.Bit:
        adversary = Adversary(pke)
        (pk, sk) = pke.KeyGen()
        (m0, m1) = adversary.challenge(pk)
        ct = pke.Encrypt(pk, m1)
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret

INDCPA = Crypto.DistinguishingExperimentLeftOrRight(INDCPA_Left, INDCPA_Right, INDCPA_Adversary)
