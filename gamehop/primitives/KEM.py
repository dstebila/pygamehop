from typing import Tuple, Union, TypeVar, Generic, Set

from . import Crypto
from .. import proofs

PublicKey = TypeVar('PublicKey')
SecretKey = TypeVar('SecretKey')
Ciphertext = TypeVar('Ciphertext')
SharedSecret = TypeVar('SharedSecret')
Reject = TypeVar('Reject')

class KEMScheme(Generic[PublicKey, SecretKey, Ciphertext, SharedSecret, Reject]):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encaps(self, pk: PublicKey) -> Tuple[Ciphertext, SharedSecret]: pass
    def Decaps(self, sk: SecretKey, ct: Ciphertext) -> Union[SharedSecret, Reject]: pass
    SharedSecretSet: Set[SharedSecret] = set()

class KEMINDCPA_adversary(Generic[PublicKey, SecretKey, Ciphertext, SharedSecret, Reject]):
    def setup(self, kem: KEMScheme): pass
    def guess(self, pk: PublicKey, ct: Ciphertext, ss: SharedSecret) -> Crypto.Bit: pass

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
