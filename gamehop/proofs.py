from abc import ABC
from typing import List, Type

from .primitives import Crypto
from . import inlining
from . import verification

class Experiment(): pass
class DistinguishingExperiment(Experiment):
    def main0(self, scheme, adversary) -> Crypto.Bit: pass
    def main1(self, scheme, adversary) -> Crypto.Bit: pass
class GuessingExperiment(Experiment):
    def main(self, scheme, adversary, bit: Crypto.Bit) -> Crypto.Bit: pass

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
            startGameDescription = "experiment {:s}.{:s}.main0 inlined with scheme {:s}.{:s}".format(
                self.experiment.__module__, self.experiment.__name__,
                self.scheme.__module__, self.scheme.__name__
            )
            print("---- {:s} ----".format(startGameDescription))
            if print_hops:
                print(startGame)
                if print_canonicalizations:
                    print("---- canonicalization ----")
                    print(verification.canonicalize_function(startGame))
            previousGame = startGame
            previousGameDescription = startGameDescription
            for stepNum in range(len(self.proofSteps)):
                step = self.proofSteps[stepNum]
                if step['type'] == 'distinguishingProofStep':
                    leftInlining = inlining.inline_class(step['experiment'].main0, 'adversary', step['reduction'])
                    rightInlining = inlining.inline_class(step['experiment'].main1, 'adversary', step['reduction'])
                    s1 = verification.canonicalize_function(previousGame)
                    s2 = verification.canonicalize_function(leftInlining)
                    if step['reverseDirection']: (rightInlining, leftInlining) = (leftInlining, rightInlining)
                    leftInliningDescription = "reduction {:s} inlined with {:s}.{:s}.main{:d}".format(
                        step['reduction'].__name__,
                        step['experiment'].__module__, step['experiment'].__name__,
                        0 if not step['reverseDirection'] else 1
                    )
                    rightInliningDescription = "reduction {:s} inlined with {:s}.{:s}.main{:d}".format(
                        step['reduction'].__name__,
                        step['experiment'].__module__, step['experiment'].__name__,
                        1 if not step['reverseDirection'] else 0
                    )
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
                    if stepNum == len(self.proofSteps) - 1 and print_hops:
                        print("---- {:s} ----".format(rightInliningDescription))
                        print(rightInlining)
                        if print_canonicalizations:
                            print("---- canonicalization ----")
                            print(verification.canonicalize_function(rightInlining))
                else: raise TypeError("Unsupported proof step type: {:s}.".format(str(step['type'])))
            endGame = inlining.inline_class(self.experiment.main1, 'scheme', self.scheme)
            endGameDescription = "experiment {:s}.{:s}.main1 inlined with scheme {:s}.{:s}".format(
                self.experiment.__module__, self.experiment.__name__,
                self.scheme.__module__, self.scheme.__name__
            )
            s1 = verification.canonicalize_function(previousGame)
            s2 = verification.canonicalize_function(endGame)
            print("==== ENDING GAME ====");
            print("---- experiment {:s}.{:s}.main1 inlined with scheme {:s}.{:s}".format(
                self.experiment.__module__, self.experiment.__name__,
                self.scheme.__module__, self.scheme.__name__
            ))
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
