from typing import Tuple, Union, TypeVar, Generic, Set, Any

from . import Crypto
from .. import proofs

Ciphertext = TypeVar('Ciphertext')
PublicKey = TypeVar('PublicKey')
Reject = Crypto.Reject
SecretKey = TypeVar('SecretKey')
Message = TypeVar('Message')


class PKEScheme(Generic[Ciphertext, PublicKey, SecretKey, Message]):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encrypt(self, pk: PublicKey, msg: Message) -> Ciphertext: pass
    def Decrypt(self, sk: SecretKey, ct: Ciphertext) -> Union[Message, Reject]: pass
    MessageSet: Set[Message] = set()

class PKEINDCPA_adversary(Generic[Ciphertext, PublicKey, SecretKey, Message], Crypto.AdversaryBaseClass):
    def setup(self, pke: PKEScheme): pass
    def challenge(self, pk: PublicKey) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext) -> Crypto.Bit: pass

class INDCPA(proofs.DistinguishingExperiment):
    def main0(self, pke: PKEScheme, adversary: PKEINDCPA_adversary) -> Crypto.Bit:
        dummy = adversary.setup(pke)
        (pk, sk) = pke.KeyGen()
        (m0, m1) = adversary.challenge(pk)
        ct = pke.Encrypt(pk, m0)
        r = adversary.guess(ct)
        return r
    def main1(self, pke: PKEScheme, adversary: PKEINDCPA_adversary) -> Crypto.Bit:
        dummy = adversary.setup(pke)
        (pk, sk) = pke.KeyGen()
        (m0, m1) = adversary.challenge(pk)
        ct = pke.Encrypt(pk, m1)
        r = adversary.guess(ct)
        return r
