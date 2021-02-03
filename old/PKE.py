from abc import ABC
from typing import Tuple, Union

import Crypto

class Ciphertext(ABC): pass
class PublicKey(ABC): pass
class SecretKey(ABC): pass
class Message(ABC): pass
class Reject(object): pass

class Scheme(ABC):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encrypt(self, pk: PublicKey, msg: Message) -> Ciphertext: pass
    def Decrypt(self, sk: SecretKey, ct: Ciphertext) -> Union[Message, Reject]: pass

class INDCPA_adversary(ABC):
    def challenge(self, pk: PublicKey) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext) -> Crypto.Bit: pass

def INDCPA0(pke: Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = pke.KeyGen()
    (m0, m1) = adversary.challenge(pk)
    ct = pke.Encrypt(pk, m0)
    return adversary.guess(ct)

def INDCPA1(pke: Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = pke.KeyGen()
    (m0, m1) = adversary.challenge(pk)
    ct = pke.Encrypt(pk, m1)
    return adversary.guess(ct)