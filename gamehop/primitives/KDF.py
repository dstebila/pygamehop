from typing import Callable, Type

from . import Crypto
from .. import lists

class KDFScheme(Crypto.Scheme):
    class Key(): pass
    @staticmethod
    def Eval(k: Key, label: str, len: int) -> Crypto.BitString: pass

class ROR_Adversary(Crypto.Adversary):
    def run(self, o_eval: Callable[[str, int], Crypto.BitString]) -> Crypto.Bit: pass

class ROR_Real(Crypto.Game):
    def __init__(self, Scheme: Type[KDFScheme], Adversary: Type[ROR_Adversary]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.k = Crypto.UniformlySample(self.Scheme.Key)
        r = self.adversary.run(self.o_eval)
        return r
    def o_eval(self, label: str, length: int) -> Crypto.BitString:
        return self.Scheme.Eval(self.k, label, length)

class ROR_Random(Crypto.Game):
    def __init__(self, Scheme: Type[KDFScheme], Adversary: Type[ROR_Adversary]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.query_list = lists.new_empty_list()
        r = self.adversary.run(self.o_eval)
        return r
    def o_eval(self, label: str, length: int) -> Crypto.BitString:
        if (label, length) not in self.query_list:
            self.query_list = lists.set_item(self.query_list, (label, length), Crypto.BitString.uniformly_random(length))
        return self.query_list.get_item((label, length))

ROR = Crypto.DistinguishingExperimentRealOrRandom(ROR_Real, ROR_Random, ROR_Adversary)
