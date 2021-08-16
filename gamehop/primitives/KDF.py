from abc import ABC
from typing import Callable, Tuple, Type, Union

from . import Crypto
from .. import lists

class KDFScheme(Crypto.Scheme, ABC):
    class Key(): pass
    @staticmethod
    def Eval(k: Key, label: str, len: int) -> Crypto.BitString: pass

class ROR_Adversary(Crypto.Adversary):
    def __init__(self, Scheme: Type[KDFScheme]): pass
    def run(self, o_eval: Callable[[str, int], Crypto.BitString]) -> Crypto.Bit: pass

class ROR_Real(Crypto.Game):
    def __init__(self, Scheme: Type[KDFScheme], Adversary: Type[ROR_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        adversary = self.Adversary(self.Scheme)
        self.k = Crypto.UniformlySample(self.Scheme.Key)
        r = adversary.run(self.o_eval)
        return r
    def o_eval(self, label: str, length: int) -> Crypto.BitString:
        return self.Scheme.Eval(self.k, label, length)

class ROR_Random(Crypto.Game):
    def __init__(self, Scheme: Type[KDFScheme], Adversary: Type[ROR_Adversary]):
        self.Scheme = Scheme
        self.Adversary = Adversary
    def main(self) -> Crypto.Bit:
        adversary = self.Adversary(self.Scheme)
        self.query_list = lists.new_empty_list()
        r = adversary.run(self.o_eval)
        return r
    def o_eval(self, label: str, length: int) -> Crypto.BitString:
        if (label, length) not in self.query_list:
            self.query_list = lists.set_item(self.query_list, (label, length), Crypto.BitString.uniformly_random(length))
        return self.query_list.get_item((label, length))

ROR = Crypto.DistinguishingExperimentRealOrRandom(ROR_Real, ROR_Random, ROR_Adversary)
