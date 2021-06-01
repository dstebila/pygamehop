from abc import ABC
import inspect
from typing import List, Type
import typing

from .primitives import Crypto
from . import inlining
from . import verification

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

class Proof():
    def __init__(self, experiment: Type[Experiment], scheme, adversary):
        self.experiment = experiment
        self.scheme = scheme
        self.adversary = adversary
        self.proofSteps: List[dict] = []
    def addDistinguishingProofStep(self, experiment: Type[DistinguishingExperiment], scheme, reduction, reverseDirection=False):
        self.proofSteps.append({
            'type': 'distinguishingProofStep',
            'experiment': experiment,
            'scheme': scheme,
            'reduction': reduction,
            'reverseDirection': reverseDirection
        })
    def check(self, print_hops=False, print_canonicalizations=False):
        if issubclass(self.experiment, DistinguishingExperiment):
            startGame = inlining.inline_class(self.experiment.main0, 'scheme', self.scheme)
            print("==== STARTING GAME ====");
            startGameDescription = "experiment {:s}.main0 inlined with scheme {:s}".format(fqn(self.experiment), fqn(self.scheme))
            print("---- {:s} ----".format(startGameDescription))
            if print_hops:
                print(startGame)
                if print_canonicalizations:
                    print("---- canonicalization ----")
                    print(verification.canonicalize_function(startGame))
            previousGame = startGame
            previousGameDescription = startGameDescription
            for stepNum, step in enumerate(self.proofSteps):
                if step['type'] == 'distinguishingProofStep':
                    leftInlining = inlining.inline_class(step['experiment'].main0, 'adversary', step['reduction'])
                    rightInlining = inlining.inline_class(step['experiment'].main1, 'adversary', step['reduction'])
                    if step['reverseDirection']: (rightInlining, leftInlining) = (leftInlining, rightInlining)
                    s1 = verification.canonicalize_function(previousGame)
                    s2 = verification.canonicalize_function(leftInlining)
                    leftInliningDescription = "reduction {:s} inlined with {:s}.main{:d}".format(fqn(step['reduction']), fqn(step['experiment']), 0 if not step['reverseDirection'] else 1)
                    rightInliningDescription = "reduction {:s} inlined with {:s}.main{:d}".format(fqn(step['reduction']), fqn(step['experiment']), 1 if not step['reverseDirection'] else 0)
                    print("==== GAME HOP from {:d} to {:d} (distinguishing proof step) ====".format(stepNum, stepNum + 1))
                    print("---- {:s} ----".format(leftInliningDescription))
                    if print_hops:
                        print(leftInlining)
                        if print_canonicalizations:
                            print("---- canonicalization ----")
                            print(s2)
                    if s1 != s2:
                        print("❌ canoncalizations of ({:s}) and ({:s}) are not equal".format(previousGameDescription, leftInliningDescription))
                        return False
                    else: print("✅ canoncalizations of ({:s}) and ({:s}) are equal".format(previousGameDescription, leftInliningDescription))
                    previousGame = rightInlining
                    previousGameDescription = rightInliningDescription
                    if stepNum != len(self.proofSteps) - 1 and print_hops:
                        print("---- {:s} ----".format(rightInliningDescription))
                        print(rightInlining)
                        if print_canonicalizations:
                            print("---- canonicalization ----")
                            print(verification.canonicalize_function(rightInlining))
                else: raise TypeError("Unsupported proof step type: {:s}.".format(str(step['type'])))
            endGame = inlining.inline_class(self.experiment.main1, 'scheme', self.scheme)
            endGameDescription = "experiment {:s}.main1 inlined with scheme {:s}".format(fqn(self.experiment), fqn(self.scheme))
            s1 = verification.canonicalize_function(previousGame)
            s2 = verification.canonicalize_function(endGame)
            print("==== ENDING GAME ====");
            print("---- {:s} ----".format(endGameDescription))
            if print_hops:
                print(endGame)
                if print_canonicalizations:
                    print("---- canonicalization ----")
                    print(s2)
            if s1 !=  s2:
                print("❌ canoncalizations of ({:s}) and ({:s}) are not equal".format(previousGameDescription, endGameDescription))
                return False
            else: print("✅ canoncalizations of ({:s}) and ({:s}) are equal".format(previousGameDescription, endGameDescription))
            return True
        else: raise TypeError("Unsupported experiment type for proof checker: {:s}.".format(str(type(self.experiment).__name__)))

    def advantage_bound(self):
        lines = []
        lines.append("Advantage of {:s} in experiment {:s} for scheme {:s}".format(fqn(self.adversary), fqn(self.experiment), fqn(self.scheme)))
        lines.append("≤")
        for stepNum, step in enumerate(self.proofSteps):
            if step['type'] == 'distinguishingProofStep':
                lines.append("Advantage of {:s} in experiment {:s} for scheme {:s}".format(fqn(step['reduction']), fqn(step['experiment']), "TODO"))
            else: raise TypeError("Unsupported experiment type for proof checker: {:s}.".format(str(type(self.experiment).__name__)))
            if stepNum < len(self.proofSteps) - 1: lines.append("+")
        return "\n".join(lines)
