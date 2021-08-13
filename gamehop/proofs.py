from abc import ABC
import inspect
from typing import List, Type
import typing
import ast

from . import stringDiff
from .primitives import Crypto
from . import inlining
from .inlining import internal
from . import verification
from . import utils

class Experiment(): pass
class DistinguishingExperiment(Experiment):
    def main0(self, scheme, adversary) -> Crypto.Bit: pass
    def main1(self, scheme, adversary) -> Crypto.Bit: pass
class GuessingExperiment(Experiment):
    def main(self, scheme, adversary, bit: Crypto.Bit) -> Crypto.Bit: pass

def fqn(o):
    if inspect.isclass(o):
        if o.__module__ == '__main__': return o.__name__
        else: return "{:s}.{:s}".format(o.__module__, o.__name__)
    elif isinstance(o, typing._GenericAlias):
        return typing.get_origin(o).__name__
    else: raise ValueError("Don't know how to find the name of objects of type {:s}".format(str(type(o))))

class proofStep():
    pass

class distinguishingProofStep(proofStep):
    def __init__(self, experiment, scheme, reduction, reverseDirection, renaming):
        self.experiment = experiment
        self.scheme = scheme
        self.reduction = reduction
        self.reverseDirection = reverseDirection
        self.renaming = renaming

    def inlinedGame(self, game):
        inlined = inlining.inline_class(game, 'adversary', self.reduction)
        return ast.unparse(internal.rename_variables(inlined, self.renaming, error_if_exists = False))
    def leftGame(self):
        return self.inlinedGame(self.experiment.main0 if not self.reverseDirection else self.experiment.main1)
    def rightGame(self):
        return self.inlinedGame(self.experiment.main0 if self.reverseDirection else self.experiment.main1)

    def gameDescription(self, game):
        return "reduction {:s} inlined with {:s}.main{:d}".format(fqn(self.reduction), fqn(self.experiment), game)
    def leftDescription(self):
        return  self.gameDescription(0 if not self.reverseDirection else 1)
    def rightDescription(self):
        return  self.gameDescription(0 if self.reverseDirection else 1)

    def gameCanonical(self, game):
        return verification.canonicalize_function(game)
    def leftCanonical(self):
        return self.gameCanonical(self.leftGame())
    def rightCanonical(self):
        return self.gameCanonical(self.rightGame())

    def advantage(self):
        return "Advantage of {:s} in experiment {:s} for scheme {:s}".format(fqn(self.reduction), fqn(self.experiment), "TODO")


class Proof():
    def __init__(self, experiment: Type[Experiment], scheme, adversary):
        self.experiment = experiment
        self.scheme = scheme
        self.adversary = adversary
        self.proofSteps: List[proofStep] = []

    def addDistinguishingProofStep(self, experiment: Type[DistinguishingExperiment], scheme, reduction, reverseDirection=False, renaming=dict()):
        self.proofSteps.append(distinguishingProofStep(experiment, scheme, reduction, reverseDirection, renaming))

    def gamesEqual(self, lgame, rgame):
        if lgame[1] != rgame[1]:
            print("❌ canoncalizations of ({:s}) and ({:s}) are not equal".format(lgame[2], rgame[2]))
            stringDiff(lgame[1], rgame[1])
            return False
        print("✅ canoncalizations of ({:s}) and ({:s}) are equal".format(lgame[2], rgame[2]))
        return True

    def check(self, print_hops=False, print_canonicalizations=False, show_call_graphs=False):
        def printHop(game):
            if print_hops:
                print(game[0])
                if print_canonicalizations:
                    print("---- canonicalization ----")
                    print(game[1])
                if show_call_graphs:
                    verification.canonicalization.show_call_graph(utils.get_function_def(game[1]))


        if issubclass(self.experiment, DistinguishingExperiment):
            startGame = inlining.inline_class(self.experiment.main0, 'scheme', self.scheme)
            print("==== STARTING GAME ====");
            startGameDescription = "experiment {:s}.main0 inlined with scheme {:s}".format(fqn(self.experiment), fqn(self.scheme))
            print("---- {:s} ----".format(startGameDescription))

            previousGame = (startGame, verification.canonicalize_function(startGame), startGameDescription)
            printHop(previousGame)

            for stepNum, step in enumerate(self.proofSteps):
                nextGame = (step.leftGame(), step.leftCanonical(), step.leftDescription())
                print("==== GAME HOP from {:d} to {:d} (distinguishing proof step) ====".format(stepNum, stepNum + 1))
                print("---- {:s} ----".format(nextGame[2]))
                printHop(nextGame)

                if not self.gamesEqual(previousGame, nextGame):
                    return False

                previousGame = (step.rightGame(), step.rightCanonical(), step.rightDescription())
                if stepNum != len(self.proofSteps) - 1 and print_hops:
                    print("---- {:s} ----".format(previousGame[2]))
                    printHop(previousGame)

            endGameX = inlining.inline_class(self.experiment.main1, 'scheme', self.scheme)
            endGameDescription = "experiment {:s}.main1 inlined with scheme {:s}".format(fqn(self.experiment), fqn(self.scheme))
            endGameCanonical = verification.canonicalize_function(endGameX)
            endGame = (endGameX, endGameCanonical, endGameDescription)
            print("==== ENDING GAME ====");
            print("---- {:s} ----".format(endGame[2]))
            printHop(endGame)

            return self.gamesEqual(previousGame, endGame)

        else: raise TypeError("Unsupported experiment type for proof checker: {:s}.".format(str(type(self.experiment).__name__)))

    def advantage_bound(self):
        lines = []
        lines.append("Advantage of {:s} in experiment {:s} for scheme {:s}".format(fqn(self.adversary), fqn(self.experiment), fqn(self.scheme)))
        lines.append("≤")
        for stepNum, step in enumerate(self.proofSteps):
            lines.append(step.advantage())
            if stepNum < len(self.proofSteps) - 1: lines.append("+")
        return "\n".join(lines)
