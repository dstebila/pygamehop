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
class Adversary():
    def __init__(self, scheme: Type[Scheme]) -> None: pass
class Reduction(Adversary):
    def __init__(self, scheme: Type[Scheme], inner_adversary: Adversary) -> None: pass

class AbstractGame():
    def main(self) -> Bit: pass

class Game(AbstractGame):
    def __init__(self, Scheme: Type[Scheme], Adversary: Type[Adversary]) -> None: pass

class GameParameterizedByBit(AbstractGame):
    def __init__(self, Scheme: Type[Scheme], Adversary: Type[Adversary], b: Bit) -> None: pass

class Experiment(): pass

class DistinguishingExperiment(Experiment):
    def get_adversary(self): return self.adversary

class DistinguishingExperimentLeftOrRight(DistinguishingExperiment):
    def __init__(self, left: Type[Game], right: Type[Game], adversary: Type[Adversary]):
        self.left = left
        self.right = right
        self.adversary = adversary

class DistinguishingExperimentRealOrRandom(DistinguishingExperiment):
    def __init__(self, real: Type[Game], random: Type[Game], adversary: Type[Adversary]):
        self.real = real
        self.random = random
        self.adversary = adversary

class DistinguishingExperimentHiddenBit(DistinguishingExperiment):
    def __init__(self, game: Type[GameParameterizedByBit], adversary: Type[Adversary]):
        self.game = game
        self.adversary = adversary

class WinLoseExperiment(Experiment):
    def __init__(self, game: Type[Game], adversary: Type[Adversary]):
        self.game = game
        self.adversary = adversary
    losing_game = """class LosingGame(Crypto.Game):
    def main(self) -> Crypto.Bit:
        return Crypto.Bit(0)"""
