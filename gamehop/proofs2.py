from typing import Type

from .primitives import Crypto
from . import inlining
from .inlining import internal
from . import verification
from . import utils

class ProofStep():
    def get_left(self) -> str: pass
    def get_right(self) -> str: pass

class DistinguishingProofStep(ProofStep):
    def __init__(self, reduction: Crypto.Reduction, experiment: Crypto.DistinguishingExperiment, scheme: Crypto.Scheme, reverse_direction: bool):
        self.reduction = reduction
        self.experiment = experiment
        self.scheme = scheme
        self.reverse_direction = reverse_direction

class Proof():
    def __init__(self, scheme: Type[Crypto.Scheme], experiment: Crypto.Experiment):
        self.scheme = scheme
        self.experiment = experiment
        self.proof_steps = list()

    def addDistinguishingProofStep(self, reduction: Crypto.Reduction, experiment: Crypto.DistinguishingExperiment, scheme: Crypto.Scheme, reverse_direction = False) -> None:
        """Add a distinguishing proof step for a reduction 'reduction' against the distinguishing security experiment 'experiment' for a scheme 'scheme'.
        If reverse_direction == False, the "left" and "right" sides of the game hopping proof are lined up with the get_left and get_right methods of the given distinguishing experiment, and are swapped if reverse_direction == True."""
        self.proof_steps.append(DistinguishingProofStep(reduction, experiment, scheme, reverse_direction))

    def get_game(self, gamenum: int, before = True) -> str:
        if gamenum == 0 and before: # use the original experiment
            if isinstance(self.experiment, Crypto.DistinguishingExperimentLeftOrRight):
                return inlining.inline_scheme_into_game(self.scheme, self.experiment.left)
            elif isinstance(self.experiment, Crypto.DistinguishingExperimentRealOrRandom):
                return inlining.inline_scheme_into_game(self.scheme, self.experiment.real)
            elif isinstance(self.experiment, Crypto.DistinguishingExperimentHiddenBit):
                raise NotImplementedError("Not yet implemented")
            elif isinstance(self.experiment, Crypto.WinLoseExperiment):
                return inlining.inline_scheme_into_game(self.scheme, self.game)
        elif (gamenum == -1 or gamenum == len(self.proof_steps) - 1) and not(before): # use the final experiment
            if isinstance(self.experiment, Crypto.DistinguishingExperimentLeftOrRight):
                return inlining.inline_scheme_into_game(self.scheme, self.experiment.right)
            elif isinstance(self.experiment, Crypto.DistinguishingExperimentRealOrRandom):
                return inlining.inline_scheme_into_game(self.scheme, self.experiment.random)
            elif isinstance(self.experiment, Crypto.DistinguishingExperimentHiddenBit):
                raise NotImplementedError("Not yet implemented")
            elif isinstance(self.experiment, Crypto.WinLoseExperiment):
                return Crypto.WinLoseExperiment.losing_game
        elif 0 <= gamenum < len(self.proof_steps) - 1 and not(before): # use the alleged equivalent of the game after hopping
            step = self.proof_steps[gamenum]
            if isinstance(step, DistinguishingProofStep): pass
                # TODO left off here
