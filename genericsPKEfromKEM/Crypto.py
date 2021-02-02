from abc import ABC

from typing import Any, TypeVar, Generic, Set, Annotated

class Bit(int): pass
class UniformlyRandom(ABC): pass
class Reject(ABC): pass

class ByteString(ABC):
    # def __xor__(self, other: ByteString) -> ByteString: pass
    def __xor__(self, other): pass

class UniformlyRandomByteString(UniformlyRandom, ByteString): pass

T = TypeVar('T')
UniformlyRandomT = Annotated[T, UniformlyRandom]
def UniformlySample(s : Set[T]) -> UniformlyRandomT[T]: pass
