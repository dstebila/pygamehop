from abc import ABC

from typing import Any, TypeVar, Generic, Set, Annotated, Tuple, Callable, Type

class Bit(int): pass
class UniformlyRandom(ABC): pass
class Reject(ABC): pass

class ByteString(ABC):
    # def __xor__(self, other: ByteString) -> ByteString: pass
    def __xor__(self, other): pass

class UniformlyRandomByteString(UniformlyRandom, ByteString): pass

T = TypeVar('T')
def UniformlySample(s: Type[T]) -> Annotated[T, UniformlyRandom]: pass

class Adversary():
    def setup(self, scheme: Any) -> None: pass

class Scheme(): pass
