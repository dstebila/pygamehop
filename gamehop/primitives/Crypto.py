from typing import TypeVar, Annotated, Type

class Bit(int): pass
class UniformlyRandom(): pass
class Reject(): pass

class BitString():
    # def __xor__(self, other: ByteString) -> ByteString: pass
    def __xor__(self, other): pass
    @staticmethod
    def uniformly_random(length: int): pass

T = TypeVar('T')
def UniformlySample(s: Type[T]) -> Annotated[T, UniformlyRandom]: pass

class Scheme(): pass
class Adversary(): pass
class Reduction(Adversary):
    InnerAdversary: Type[Adversary] = None

class Game(): pass
class Experiment(): pass
class DistinguishingExperiment(Experiment):
    def get_left(self): pass
    def get_right(self): pass
    def get_adversary(self): return self.adversary
class DistinguishingExperimentLeftOrRight(DistinguishingExperiment):
    def __init__(self, left: Type[Game], right: Type[Game], adversary: Type[Adversary]):
        self.left = left
        self.right = right
        self.adversary = adversary
    def get_left(self): return self.left
    def get_right(self): return self.right
class DistinguishingExperimentRealOrRandom(DistinguishingExperiment):
    def __init__(self, real: Type[Game], random: Type[Game], adversary: Type[Adversary]):
        self.real = real
        self.random = random
        self.adversary = adversary
    def get_left(self): return self.real
    def get_right(self): return self.random
class DistinguishingExperimentHiddenBit(DistinguishingExperiment):
    def __init__(self, game: Type[Game], adversary: Type[Adversary]):
        self.game = game
        self.adversary = adversary
    def get_left(self): raise NotImplementedError()
    def get_right(self): raise NotImplementedError()
