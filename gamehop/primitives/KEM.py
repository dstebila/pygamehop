from typing import Tuple, Union, Set

from . import Crypto
from .. import proofs

class KEMScheme(Crypto.Scheme):
    class PublicKey(): pass
    class SecretKey(): pass
    class Ciphertext(): pass
    class SharedSecret(): pass
    class Reject(): pass
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encaps(self, pk: PublicKey) -> Tuple[Ciphertext, SharedSecret]: pass
    def Decaps(self, sk: SecretKey, ct: Ciphertext) -> Union[SharedSecret, Reject]: pass
    SharedSecretSet: Set[SharedSecret] = set()

class KEMINDCPA_adversary(Crypto.Adversary):
    def setup(self, kem: KEMScheme): pass
    def guess(self, pk: KEMScheme.PublicKey, ct: KEMScheme.Ciphertext, ss: KEMScheme.SharedSecret) -> Crypto.Bit: pass

class INDCPA(proofs.DistinguishingExperiment):
    def main0(self, scheme: KEMScheme, adversary: KEMINDCPA_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (pk, sk) = scheme.KeyGen()
        (ct, ss_real) = scheme.Encaps(pk)
        return adversary.guess(pk, ct, ss_real)
    def main1(self, scheme: KEMScheme, adversary: KEMINDCPA_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (pk, sk) = scheme.KeyGen()
        (ct, _) = scheme.Encaps(pk)
        ss_rand = Crypto.UniformlySample(scheme.SharedSecretSet)
        return adversary.guess(pk, ct, ss_rand)
