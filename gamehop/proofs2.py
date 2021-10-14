from typing import List, Type

from .primitives import Crypto
from . import inlining
from .inlining import internal
from . import verification
from . import utils

class ProofStep():
    def get_left_game(self) -> Crypto.Game: pass
    def get_left_src(self, target_game: Type[Crypto.Game], target_scheme: Type[Crypto.Scheme]) -> str: pass
    def get_right_game(self) -> Crypto.Game: pass
    def get_right_src(self, target_game: Type[Crypto.Game], target_scheme: Type[Crypto.Scheme]) -> str: pass
    def advantage(self) -> str: pass

class DistinguishingProofStep(ProofStep):
    def __init__(self, reduction: Type[Crypto.Reduction], experiment: Crypto.DistinguishingExperiment, scheme: Type[Crypto.Scheme], reverse_direction: bool):
        self.reduction = reduction
        self.experiment = experiment
        self.scheme = scheme
        self.reverse_direction = reverse_direction
    def get_left_game(self):
        return self.experiment.get_left() if not(self.reverse_direction) else self.experiment.get_right()
    def get_left_src(self, target_game: Type[Crypto.Game], target_scheme: Type[Crypto.Scheme]):
        return inlining.inline_reduction_into_game(self.reduction, self.get_left_game(), self.scheme, target_game, target_scheme)
    def get_right_game(self):
        return self.experiment.get_left() if self.reverse_direction else self.experiment.get_right()
    def get_right_src(self, target_game: Type[Crypto.Game], target_scheme: Type[Crypto.Scheme]):
        return inlining.inline_reduction_into_game(self.reduction, self.get_right_game(), self.scheme, target_game, target_scheme)
    def advantage(self):
        return f"Advantage of reduction {utils.fqn(self.reduction)} in experiment {self.experiment.name} for {utils.parentfqn(self.scheme)} scheme {utils.fqn(self.scheme)}"

class Proof():
    def __init__(self, scheme: Type[Crypto.Scheme], experiment: Crypto.Experiment):
        self.scheme = scheme
        self.experiment = experiment
        self.proof_steps: List[ProofStep] = list()
        self.proof_checked = "unchecked"

    def add_distinguishing_proof_step(self, reduction: Type[Crypto.Reduction], experiment: Crypto.DistinguishingExperiment, scheme: Type[Crypto.Scheme], reverse_direction = False) -> None:
        """Add a distinguishing proof step for a reduction 'reduction' against the distinguishing security experiment 'experiment' for a scheme 'scheme'.
        If reverse_direction == False, the "left" and "right" sides of the game hopping proof are lined up with the get_left and get_right methods of the given distinguishing experiment, and are swapped if reverse_direction == True."""
        self.proof_steps.append(DistinguishingProofStep(reduction, experiment, scheme, reverse_direction))

    def get_game_src(self, gamenum: int, before_hop = True) -> str:
        if gamenum == 0 and before_hop: # use the original experiment
            if isinstance(self.experiment, Crypto.DistinguishingExperiment):
                return inlining.inline_scheme_into_game(self.scheme, self.experiment.get_left())
        elif 0 <= gamenum < len(self.proof_steps) and not(before_hop): # use the reduction inlined into the left side of its experiment
            step = self.proof_steps[gamenum]
            if isinstance(step, DistinguishingProofStep):
                return step.get_left_src(step.experiment.get_left(), self.scheme)
        elif 0 < gamenum <= len(self.proof_steps) and before_hop: # use the reduction inlined into the right side of its experiment
            step = self.proof_steps[gamenum - 1]
            if isinstance(step, DistinguishingProofStep):
                return step.get_right_src(step.experiment.get_right(), self.scheme)
        elif (gamenum == -1 or gamenum == len(self.proof_steps)) and not(before_hop): # use the final experiment
            if isinstance(self.experiment, Crypto.DistinguishingExperiment):
                return inlining.inline_scheme_into_game(self.scheme, self.experiment.get_right())
        raise NotImplementedError()

    def get_game_description(self, gamenum: int, before_hop = True) -> str:
        if gamenum == 0 and before_hop: # use the original experiment
            if isinstance(self.experiment, Crypto.DistinguishingExperiment):
                return f"game {utils.fqn(self.experiment.get_left())} with {utils.parentfqn(self.scheme)} scheme {utils.fqn(self.scheme)} inlined"
        elif 0 <= gamenum < len(self.proof_steps) and not(before_hop): # use the reduction inlined into the left side of its experiment
            step = self.proof_steps[gamenum]
            if isinstance(step, DistinguishingProofStep):
                return f"reduction {utils.fqn(step.reduction)} inlined into game {utils.fqn(step.get_left_game())} for {utils.parentfqn(step.scheme)} scheme {utils.fqn(step.scheme)}"
        elif 0 < gamenum <= len(self.proof_steps) and before_hop: # use the reduction inlined into the right side of its experiment
            step = self.proof_steps[gamenum - 1]
            if isinstance(step, DistinguishingProofStep):
                return f"reduction {utils.fqn(step.reduction)} inlined into game {utils.fqn(step.get_right_game())} for {utils.parentfqn(step.scheme)} scheme {utils.fqn(step.scheme)}"
        elif (gamenum == -1 or gamenum == len(self.proof_steps)) and not(before_hop): # use the final experiment
            if isinstance(self.experiment, Crypto.DistinguishingExperiment):
                return f"game {utils.fqn(self.experiment.get_right())} with {utils.parentfqn(self.scheme)} scheme {utils.fqn(self.scheme)} inlined"
        raise NotImplementedError()

    def check(self, print_hops=False, print_canonicalizations=False, show_call_graphs=False) -> bool:
        def print_hop(game_src, game_src_canonicalized):
            if print_hops:
                print(game_src)
                if print_canonicalizations:
                    print("---- canonicalization ----")
                    print(game_src_canonicalized)
                if show_call_graphs: verification.canonicalization.show_call_graph(utils.get_function_def(game_src_canonicalized))

        for gamenum in range(len(self.proof_steps) + 1):
            print(f"==== GAME {gamenum} ====")
            if gamenum == 0: print(f"---- starting game: {self.get_game_description(gamenum, True)} --- ")
            else: print(f"---- after hop: {self.get_game_description(gamenum, True)} --- ")
            left_game_src = self.get_game_src(gamenum, True)
            left_game_src_canonicalized = verification.canonicalize_game(left_game_src)
            print_hop(left_game_src, left_game_src_canonicalized)
            if gamenum == len(self.proof_steps): print(f"---- ending game: {self.get_game_description(gamenum, False)} --- ")
            else: print(f"---- before hop: {self.get_game_description(gamenum, False)} --- ")
            right_game_src = self.get_game_src(gamenum, False)
            right_game_src_canonicalized = verification.canonicalize_game(right_game_src)
            print_hop(right_game_src, right_game_src_canonicalized)
            if left_game_src_canonicalized != right_game_src_canonicalized:
                print("❌ canoncalizations are NOT equal")
                utils.stringDiff(left_game_src_canonicalized, right_game_src_canonicalized)
                self.proof_checked = "invalid"
                return False
            else:
                print("✅ canoncalizations are equal")

        self.proof_checked = "valid"
        return True

    def advantage_bound(self) -> str:
        if self.proof_checked == "unchecked":
            raise ValueError("Cannot compute advantage bound, proof has not been checked")
        elif self.proof_checked == "invalid":
            raise ValueError("Cannot compute advantage bound, proof is not valid")
        lines = []
        lines.append(f"Advantage of adversary in experiment {self.experiment.get_name()} for {utils.parentfqn(self.scheme)} scheme {utils.fqn(self.scheme)}")
        lines.append("≤")
        for stepnum, step in enumerate(self.proof_steps):
            lines.append(step.advantage())
            if stepnum < len(self.proof_steps) - 1: lines.append("+")
        return "\n".join(lines)

