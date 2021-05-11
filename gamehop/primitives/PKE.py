from typing import Tuple, Union, TypeVar, Generic, Set, Any

from . import Crypto
from .. import proofs

class PKEScheme(Crypto.Scheme):
    class PublicKey(): pass
    class SecretKey(): pass
    class Ciphertext(): pass
    class Message(): pass
    class Reject(): pass
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encrypt(self, pk: PublicKey, msg: Message) -> Ciphertext: pass
    def Decrypt(self, sk: SecretKey, ct: Ciphertext) -> Union[Message, Reject]: pass

class PKEINDCPA_adversary(Crypto.Adversary):
    def setup(self, pke: PKEScheme): pass
    def challenge(self, pk: PKEScheme.PublicKey) -> Tuple[PKEScheme.Message, PKEScheme.Message]: pass
    def guess(self, ct: PKEScheme.Ciphertext) -> Crypto.Bit: pass

class INDCPA(proofs.DistinguishingExperiment):
    def main0(self, scheme: PKEScheme, adversary: PKEINDCPA_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (pk, sk) = scheme.KeyGen()
        (m0, m1) = adversary.challenge(pk)
        ct = scheme.Encrypt(pk, m0)
        r = adversary.guess(ct)
        return r
    def main1(self, scheme: PKEScheme, adversary: PKEINDCPA_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (pk, sk) = scheme.KeyGen()
        (m0, m1) = adversary.challenge(pk)
        ct = scheme.Encrypt(pk, m1)
        r = adversary.guess(ct)
        return r
