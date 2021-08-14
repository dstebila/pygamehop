from abc import ABC
import inspect
from typing import List, Type
import typing
import ast
import jinja2

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
    def stepType(self): pass
    def leftGameSrc(self): pass
    def rightGameSrc(self): pass
    def leftDescription(self): pass
    def rightDescription(self): pass
    def advantage(self): pass

class distinguishingProofStep(proofStep):
    def __init__(self, experiment, scheme, reduction, reverseDirection, renaming):
        self.experiment = experiment
        self.scheme = scheme
        self.reduction = reduction
        self.reverseDirection = reverseDirection
        self.renaming = renaming

    def stepType(self): return "distinguishing step"

    def _inlinedGame(self, game):
        inlined = inlining.inline_class(game, 'adversary', self.reduction)
        return ast.unparse(internal.rename_variables(inlined, self.renaming, error_if_exists = False))
    def leftGameSrc(self):
        return self._inlinedGame(self.experiment.main0 if not self.reverseDirection else self.experiment.main1)
    def rightGameSrc(self):
        return self._inlinedGame(self.experiment.main0 if self.reverseDirection else self.experiment.main1)

    def leftDescription(self):
        return f"{fqn(self.experiment)}.main{0 if not self.reverseDirection else 1} with reduction {fqn(self.reduction)} inlined"
    def rightDescription(self):
        return f"{fqn(self.experiment)}.main{0 if self.reverseDirection else 1} with reduction {fqn(self.reduction)} inlined"

    def advantage(self):
        return "Advantage of {:s} in experiment {:s} for scheme {:s}".format(fqn(self.reduction), fqn(self.experiment), "TODO")

class rewritingStep(proofStep):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def stepType(self): return "rewriting step"

    def leftGameSrc(self):
        return ast.unparse(utils.get_function_def(self.left))
    def rightGameSrc(self):
        return ast.unparse(utils.get_function_def(self.right))

    def leftDescription(self):
        return "Rewriting step (left)"
    def rightDescription(self):
        return "Rewriting step (right)"

    def advantage(self):
        return "0 (Rewriting step)"


class Proof():
    def __init__(self, experiment: Type[Experiment], scheme, adversary):
        self.experiment = experiment
        self.scheme = scheme
        self.adversary = adversary
        self.proofSteps: List[proofStep] = []

    def addDistinguishingProofStep(self, experiment: Type[DistinguishingExperiment], scheme, reduction, reverseDirection=False, renaming=dict()):
        self.proofSteps.append(distinguishingProofStep(experiment, scheme, reduction, reverseDirection, renaming))

    def addRewritingStep(self, left, right):
        self.proofSteps.append(rewritingStep(left, right))

    @staticmethod
    def gamesEqual(lgameDescription, lgameSrcCanonicalized, rgameDescription, rgameSrcCanonicalized):
        if lgameSrcCanonicalized == rgameSrcCanonicalized:
            print(f"✅ canoncalizations of ({lgameDescription}) and ({rgameDescription}) are equal")
            return True
        else:
            print(f"❌ canoncalizations of ({lgameDescription}) and ({rgameDescription}) are NOT equal")
            stringDiff(lgameSrcCanonicalized, rgameSrcCanonicalized)
            return False

    def check(self, print_hops=False, print_canonicalizations=False, show_call_graphs=False):
        def printHop(gameSrc, gameSrcCanonicalized):
            if print_hops:
                print(gameSrc)
                if print_canonicalizations:
                    print("---- canonicalization ----")
                    print(gameSrcCanonicalized)
                if show_call_graphs: verification.canonicalization.show_call_graph(utils.get_function_def(gameSrcCanonicalized))


        if issubclass(self.experiment, DistinguishingExperiment):
            print("==== STARTING GAME ====");
            startGameDescription = "experiment {:s}.main0 with scheme {:s} inlined".format(fqn(self.experiment), fqn(self.scheme))
            print("---- {:s} ----".format(startGameDescription))
            startGameSrc = inlining.inline_class(self.experiment.main0, 'scheme', self.scheme)
            startGameSrcCanonicalized = verification.canonicalize_function(startGameSrc)
            printHop(startGameSrc, startGameSrcCanonicalized)

            previousGameDescription = startGameDescription
            previousGameSrc = startGameSrc
            previousGameSrcCanonicalized = startGameSrcCanonicalized

            for stepNum, step in enumerate(self.proofSteps):
                print("==== GAME HOP from {:d} to {:d} ({:s}) ====".format(stepNum, stepNum + 1, step.stepType()))
                nextGameDescription = step.leftDescription()
                print(f"---- {nextGameDescription} ----")
                nextGameSrc = step.leftGameSrc()
                nextGameSrcCanonicalized = verification.canonicalize_function(nextGameSrc)
                printHop(nextGameSrc, nextGameSrcCanonicalized)

                if not Proof.gamesEqual(previousGameDescription, previousGameSrcCanonicalized, nextGameDescription, nextGameSrcCanonicalized):
                    return False
                
                if isinstance(step, rewritingStep) and print_hops:
                    print(f"---- diff of rewriting step ----")
                    stringDiff(step.leftGameSrc(), step.rightGameSrc())

                previousGameDescription = step.rightDescription()
                previousGameSrc = step.rightGameSrc()
                previousGameSrcCanonicalized = verification.canonicalize_function(previousGameSrc)

                if stepNum != len(self.proofSteps) - 1 and print_hops:
                    print(f"---- {previousGameDescription} ----")
                    printHop(previousGameSrc, previousGameSrcCanonicalized)

            print("==== ENDING GAME ====");
            endGameDescription = "experiment {:s}.main1 with scheme {:s} inlined".format(fqn(self.experiment), fqn(self.scheme))
            print(f"---- {endGameDescription} ----")
            endGameSrc = inlining.inline_class(self.experiment.main1, 'scheme', self.scheme)
            endGameSrcCanonical = verification.canonicalize_function(endGameSrc)
            printHop(endGameSrc, endGameSrcCanonical)

            return Proof.gamesEqual(previousGameDescription, previousGameSrcCanonicalized, endGameDescription, endGameSrcCanonical)

        else: raise TypeError("Unsupported experiment type for proof checker: {:s}.".format(str(type(self.experiment).__name__)))

    def advantage_bound(self):
        lines = []
        lines.append("Advantage of {:s} in experiment {:s} for scheme {:s}".format(fqn(self.adversary), fqn(self.experiment), fqn(self.scheme)))
        lines.append("≤")
        for stepNum, step in enumerate(self.proofSteps):
            lines.append(step.advantage())
            if stepNum < len(self.proofSteps) - 1: lines.append("+")
        return "\n".join(lines)

    def tikz_figure(self):
        def classname_filter(value):
            if value.__module__ == '__main__': return value.__name__
            elif value.__module__.startswith('gamehop.primitives.'): return value.__module__.replace('gamehop.primitives.', '') + '.' + value.__name__
            else: return value.__module__ + '.' + value.__name__
        env = jinja2.Environment(
            loader=jinja2.PackageLoader("gamehop"),
            trim_blocks=True, # https://stackoverflow.com/questions/33775085/is-it-possible-to-change-the-default-double-curly-braces-delimiter-in-polymer
            block_start_string='≤%',
            block_end_string='%≥',
            variable_start_string='≤≤',
            variable_end_string='≥≥'
        )
        env.filters['classname'] = classname_filter
        template = env.get_template("tikz_figure.tex")
        return template.render(proof=self)
