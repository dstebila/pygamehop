from typing import Tuple, Union, TypeVar, Generic, Set

from . import Crypto

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

def INDCPA_b(kem: KEMScheme, adversary: KEMINDCPA_adversary, b: Crypto.Bit) -> Crypto.Bit:
    dummy = adversary.setup(kem)
    (pk, sk) = kem.KeyGen()
    (ct, ss_real) = kem.Encaps(pk)
    ss_rand = Crypto.UniformlySample(kem.SharedSecretSet)
    ss_challenge = ss_real if b == 0 else ss_rand
    return adversary.guess(pk, ct, ss_challenge)
