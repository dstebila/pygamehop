from typing import Tuple, Union, TypeVar, Generic, Set

from . import Crypto

Ciphertext = TypeVar('Ciphertext')
PublicKey = TypeVar('PublicKey')
Reject = TypeVar('Reject')
SecretKey = TypeVar('SecretKey')
Message = TypeVar('Message')


class PKEScheme(Generic[Ciphertext, PublicKey, SecretKey, Message, Reject]):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encrypt(self, pk: PublicKey, msg: Message) -> Ciphertext: pass
    def Decrypt(self, sk: SecretKey, ct: Ciphertext) -> Union[Message, Reject]: pass
    MessageSet: Set[Message] = set()


class PKEINDCPA_adversary(Generic[Ciphertext, PublicKey, SecretKey, Message, Reject]):
    def challenge(self, pk: PublicKey) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext) -> Crypto.Bit: pass
    def setup(self, pke: PKEScheme) -> None: pass
    pke: PKEScheme

def INDCPA0(pke: PKEScheme, adversary: PKEINDCPA_adversary) -> Crypto.Bit:
    #adversary.pke = pke
    adversary.setup(pke)
    (pk, sk) = pke.KeyGen()
    (m0, m1) = adversary.challenge(pk)
    ct = pke.Encrypt(pk, m0)
    r = adversary.guess(ct)
    return r


def INDCPA1(pke: PKEScheme, adversary: PKEINDCPA_adversary) -> Crypto.Bit:
    #adversary.pke = pke
    adversary.setup(pke)
    (pk, sk) = pke.KeyGen()
    (m0, m1) = adversary.challenge(pk)
    ct = pke.Encrypt(pk, m1)
    r = adversary.guess(ct)
    return r
