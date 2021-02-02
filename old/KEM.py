from abc import ABC
from typing import Tuple, Union

import Crypto

class PublicKey(ABC): pass
class SecretKey(ABC): pass
class Ciphertext(ABC): pass
class SharedSecret(ABC): pass
class RandomSharedSecret(SharedSecret, Crypto.UniformlyRandom): pass
class Reject(object): pass

class Scheme(ABC):
    def KeyGen(self) -> Tuple[PublicKey, SecretKey]: pass
    def Encaps(self, pk: PublicKey) -> Tuple[Ciphertext, SharedSecret]: pass
    def Decaps(self, sk: SecretKey, ct: Ciphertext) -> Union[SharedSecret, Reject]: pass

class INDCPA_adversary(ABC):
    def guess(self, pk: PublicKey, ct: Ciphertext, ss: SharedSecret) -> Crypto.Bit: pass

def INDCPA_real(kem: Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = kem.KeyGen()
    (ct, ss_real) = kem.Encaps(pk)
    return adversary.guess(pk, ct, ss_real)

def INDCPA_random(kem: Scheme, adversary: INDCPA_adversary) -> Crypto.Bit:
    (pk, sk) = kem.KeyGen()
    (ct, _) = kem.Encaps(pk)
    ss_rand = RandomSharedSecret()
    return adversary.guess(pk, ct, ss_rand)
