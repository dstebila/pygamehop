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
    def guess(self, pk: PublicKey, ct: Ciphertext, ss: SharedSecret) -> Crypto.Bit: pass

def INDCPA_real(kem: KEMScheme, adversary: KEMINDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = kem.KeyGen()
    (ct, ss_real) = kem.Encaps(pk)
    return adversary.guess(pk, ct, ss_real)

def INDCPA_random(kem: KEMScheme, adversary: KEMINDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = kem.KeyGen()
    (ct, _) = kem.Encaps(pk)
    ss_rand = Crypto.UniformlySample(kem.SharedSecretSet)
    return adversary.guess(pk, ct, ss_rand)
