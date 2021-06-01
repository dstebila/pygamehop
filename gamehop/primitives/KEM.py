from typing import Tuple, Union

from . import Crypto
from .. import proofs

class PublicKey(): pass
class SecretKey(): pass
class Ciphertext(): pass
class SharedSecret(): pass

class KEMScheme(Crypto.Scheme):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encaps(self, pk: PublicKey) -> Tuple[Ciphertext, SharedSecret]: pass
    def Decaps(self, sk: SecretKey, ct: Ciphertext) -> Union[SharedSecret, Crypto.Reject]: pass

class KEMINDCPA_adversary(Crypto.Adversary):
    def setup(self, kem: KEMScheme): pass
    def guess(self, pk: PublicKey, ct: Ciphertext, ss: SharedSecret) -> Crypto.Bit: pass

class INDCPA(proofs.DistinguishingExperiment):
    def main0(self, scheme: KEMScheme, adversary: KEMINDCPA_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (pk, sk) = scheme.KeyGen()
        (ct, ss_real) = scheme.Encaps(pk)
        r = adversary.guess(pk, ct, ss_real)
        return r
    def main1(self, scheme: KEMScheme, adversary: KEMINDCPA_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (pk, sk) = scheme.KeyGen()
        (ct, _) = scheme.Encaps(pk)
        ss_rand = Crypto.UniformlySample(SharedSecret)
        r = adversary.guess(pk, ct, ss_rand)
        return r
