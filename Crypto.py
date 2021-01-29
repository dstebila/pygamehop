from abc import ABC

from typing import Any

class Bit(int): pass
class UniformlyRandom(ABC): pass

class ByteString(ABC):
    def __xor__(self, other: ByteString) -> ByteString: pass
    
class UniformlyRandomByteString(UniformlyRandom, ByteString): pass
