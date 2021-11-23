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

class Experiment():
    def get_primitive_name(self) -> str: pass
    def get_experiment_name(self) -> str: pass
    def get_target_game(self) -> Type[Game]: pass
    def get_adversary(self) -> Type[Adversary]: pass

class DistinguishingExperiment(Experiment):
    def get_adversary(self): return self.adversary
    def get_left(self): raise NotImplementedError()
    def get_right(self): raise NotImplementedError()

class DistinguishingExperimentLeftOrRight(DistinguishingExperiment):
    def __init__(self, primitive_name: str, experiment_name: str, left: Type[Game], right: Type[Game], adversary: Type[Adversary]):
        self.primitive_name = primitive_name
        self.experiment_name = experiment_name
        self.left = left
        self.right = right
        self.adversary = adversary
    def get_primitive_name(self): return self.primitive_name
    def get_experiment_name(self): return self.experiment_name
    def get_target_game(self): return self.left
    def get_left(self): return self.left
    def get_right(self): return self.right

class DistinguishingExperimentRealOrRandom(DistinguishingExperiment):
    def __init__(self, primitive_name: str, experiment_name: str, real: Type[Game], random: Type[Game], adversary: Type[Adversary]):
        self.primitive_name = primitive_name
        self.experiment_name = experiment_name
        self.real = real
        self.random = random
        self.adversary = adversary
    def get_primitive_name(self): return self.primitive_name
    def get_experiment_name(self): return self.experiment_name
    def get_target_game(self): return self.real
    def get_left(self): return self.real
    def get_right(self): return self.random

class DistinguishingExperimentHiddenBit(DistinguishingExperiment):
    def __init__(self, primitive_name: str, experiment_name: str, game: Type[GameParameterizedByBit], adversary: Type[Adversary]):
        self.primitive_name = primitive_name
        self.experiment_name = experiment_name
        self.game = game
        self.adversary = adversary
    def get_primitive_name(self): return self.primitive_name
    def get_experiment_name(self): return self.experiment_name
    def get_target_game(self): return self.game

class WinLoseExperiment(Experiment):
    def __init__(self, primitive_name: str, experiment_name: str, game: Type[Game], adversary: Type[Adversary]):
        self.primitive_name = primitive_name
        self.experiment_name = experiment_name
        self.game = game
        self.adversary = adversary
    def get_primitive_name(self): return self.primitive_name
    def get_experiment_name(self): return self.experiment_name
    def get_target_game(self): return self.game
    losing_game = """class LosingGame(Crypto.Game):
    def main(self) -> Crypto.Bit:
        return Crypto.Bit(0)"""
