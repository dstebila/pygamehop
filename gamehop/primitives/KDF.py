from typing import Annotated, Callable, Generic, Sized, Type, TypeVar

from . import Crypto
from .. import lists

Key = TypeVar('Key')
Output = TypeVar('Output', bound=Sized)

class KDFScheme(Crypto.Scheme, Generic[Key, Output]):
    @staticmethod
    def uniformKey() -> Annotated[Key, Crypto.UniformlyRandom]: pass
    @staticmethod
    def uniformOutput(outlen: int) -> Annotated[Output, Crypto.UniformlyRandom]: pass
    @staticmethod
    def Eval(k: Key, label: str, outlen: int) -> Output: pass

class ROR_Adversary(Crypto.Adversary, Generic[Key, Output]):
    def run(self, o_eval: Callable[[str, int], Output]) -> Crypto.Bit: pass

class ROR_Real(Crypto.Game, Generic[Key, Output]):
    def __init__(self, Scheme: Type[KDFScheme[Key, Output]], Adversary: Type[ROR_Adversary[Key, Output]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.k = self.Scheme.uniformKey()
        r = self.adversary.run(self.o_eval)
        return r
    def o_eval(self, label: str, outlen: int) -> Output:
        return self.Scheme.Eval(self.k, label, outlen)

class ROR_Random(Crypto.Game, Generic[Key, Output]):
    def __init__(self, Scheme: Type[KDFScheme[Key, Output]], Adversary: Type[ROR_Adversary[Key, Output]]):
        self.Scheme = Scheme
        self.adversary = Adversary(Scheme)
    def main(self) -> Crypto.Bit:
        self.query_list = lists.new_empty_list()
        r = self.adversary.run(self.o_eval)
        return r
    def o_eval(self, label: str, outlen: int) -> Output:
        if (label, outlen) not in self.query_list:
            self.query_list = lists.set_item(self.query_list, (label, outlen), self.Scheme.uniformOutput(outlen))
        return self.query_list.get_item((label, outlen))

ROR = Crypto.DistinguishingExperimentRealOrRandom("KDF", "ROR", ROR_Real, ROR_Random, ROR_Adversary)
