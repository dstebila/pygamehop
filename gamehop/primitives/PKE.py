from typing import Sized, Tuple, Union

from . import Crypto
from .. import proofs

class PublicKey(): pass
class SecretKey(): pass
class Ciphertext(): pass
class Message(Sized): pass

class PKEScheme(Crypto.Scheme):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encrypt(self, pk: PublicKey, msg: Message) -> Ciphertext: pass
    def Decrypt(self, sk: SecretKey, ct: Ciphertext) -> Union[Message, Crypto.Reject]: pass

class PKEINDCPA_adversary(Crypto.Adversary):
    def setup(self, pke: PKEScheme): pass
    def challenge(self, pk: PublicKey) -> Tuple[Message, Message]: pass
    def guess(self, ct: Ciphertext) -> Crypto.Bit: pass

class INDCPA(proofs.DistinguishingExperiment):
    def main0(self, scheme: PKEScheme, adversary: PKEINDCPA_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (pk, sk) = scheme.KeyGen()
        (m0, m1) = adversary.challenge(pk)
        ct = scheme.Encrypt(pk, m0)
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret
    def main1(self, scheme: PKEScheme, adversary: PKEINDCPA_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (pk, sk) = scheme.KeyGen()
        (m0, m1) = adversary.challenge(pk)
        ct = scheme.Encrypt(pk, m1)
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret
