from abc import ABC
from typing import Any, Callable

import Crypto

class Scheme(ABC):
    def F(self, k: Any, x: Any) -> Crypto.ByteString: pass

class Ideal(ABC):
    def __init__(self):
        self.table = dict()

    def F(self, k: Crypto.UniformlyRandom, x: Any) -> Crypto.UniformlyRandomByteString:
        if k not in self.table: self.table[k] = dict()
        if x not in self.table[k]: self.table[k][x] = Crypto.UniformlyRandomByteString()
        return self.table[k][x]

class KDF_adversary(ABC):
    def guess(self, oracle: Callable[[Any, Any], Crypto.ByteString]) -> Crypto.Bit: pass
    
def KDF_real(kdf: Scheme, adversary: KDF_adversary) -> Crypto.Bit:
    oracle = lambda k, x: kdf.F(k, x)
    return adversary.guess(oracle)

def KDF_random(kdf: Ideal, adversary: KDF_adversary) -> Crypto.Bit:
    oracle = lambda k, x: kdf.F(k, x)
    return adversary.guess(oracle)
