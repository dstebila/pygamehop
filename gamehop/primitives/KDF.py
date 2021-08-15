from typing import Callable, Tuple, Type, Union

from . import Crypto

class Key(): pass

class KDF(Crypto.Scheme):
    def Eval(self, k: Key, label: str, len: int) -> Crypto.BitString: pass

class ROR_Adversary(Crypto.Adversary):
    def __init__(self, kdf: KDF): pass
    def run(self, o_eval: Callable[[str, int], Crypto.BitString]) -> Crypto.Bit: pass

class ROR_Real(Crypto.Game):
    def main(self, kdf: KDF, Adversary: Type[ROR_Adversary]) -> Crypto.Bit:
        self.kdf = kdf
        adversary = Adversary(kdf)
        self.k = Crypto.UniformlySample(Key)
        r = adversary.run(self.o_eval)
        return r
    def o_eval(self, label: str, length: int) -> Crypto.BitString:
        return self.kdf.Eval(self.k, label, length)

class ROR_Random(Crypto.Game):
    def main(self, kdf: KDF, Adversary: Type[ROR_Adversary]) -> Crypto.Bit:
        self.kdf = kdf
        adversary = Adversary(kdf)
        r = adversary.run(self.o_eval)
        return r
    def o_eval(self, label: str, length: int) -> Crypto.BitString:
        # TODO: turn into a lazily sampled random function
        return Crypto.BitString.uniformly_random(length)

ROR = Crypto.DistinguishingExperimentRealOrRandom(ROR_Real, ROR_Random, ROR_Adversary)
