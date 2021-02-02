from abc import ABC
from typing import Tuple, Union, TypeVar, Generic

import Crypto

PublicKey = TypeVar('PublicKey')
SecretKey = TypeVar('SecretKey')
Ciphertext = TypeVar('Ciphertext')
SharedSecretKey = Crypto.SharedSecretKey
Reject = TypeVar('Reject')

class Scheme(Generic[PublicKey, SecretKey, Ciphertext, Reject]):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encaps(self, pk: PublicKey) -> Tuple[Ciphertext, SharedSecretKey]: pass
    def Decaps(self, sk: SecretKey, ct: Ciphertext) -> Union[SharedSecretKey, Reject]: pass

class INDCPA_adversary(Generic[PublicKey, SecretKey, Ciphertext, Reject]):
    def guess(self, pk: PublicKey, ct: Ciphertext, ss: SharedSecretKey) -> Crypto.Bit: pass

def INDCPA_real(kem: Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = kem.KeyGen()
    (ct, ss_real) = kem.Encaps(pk)
    return adversary.guess(pk, ct, ss_real)

def INDCPA_random(kem: Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = kem.KeyGen()
    (ct, _) = kem.Encaps(pk)
    ss_rand = Crypto.UninformlyRandomSharedSecretKey()
    return adversary.guess(pk, ct, ss_rand)

# not sure about the shared secret type. i think needs to be some union somewhere...
