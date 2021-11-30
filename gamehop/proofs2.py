import ast
import copy
import jinja2
from typing import cast, Dict, List, Optional, Type

from .primitives import Crypto
from . import inlining
from .inlining import internal
from . import verification
from . import utils

class ProofStep():
    def get_left_game(self) -> Crypto.Game: pass
    def get_left_src(self) -> str: pass
    def get_right_game(self) -> Crypto.Game: pass
    def get_right_src(self) -> str: pass
    def advantage(self) -> str: pass

class DistinguishingProofStep(ProofStep):
    def __init__(self, reduction: Type[Crypto.Reduction], experiment: Crypto.DistinguishingExperiment, scheme: Type[Crypto.Scheme], schemeName: str, reverse_direction: bool, target_experiment: Crypto.Experiment, target_scheme: Type[Crypto.Scheme]):
        self.reduction = reduction
        self.experiment = experiment
        self.scheme = scheme
        self.schemeName = schemeName
        self.reverse_direction = reverse_direction
        self.target_experiment = target_experiment
        self.target_scheme = target_scheme
    def get_left_game(self):
        return self.experiment.get_left() if not(self.reverse_direction) else self.experiment.get_right()
    def get_left_src(self):
        return inlining.inline_reduction_into_game(self.reduction, self.get_left_game(), self.scheme, self.schemeName, self.target_experiment.get_target_game(), self.target_scheme, self.target_experiment.get_adversary(), game_name = "G")
    def get_right_game(self):
        return self.experiment.get_left() if self.reverse_direction else self.experiment.get_right()
    def get_right_src(self):
        return inlining.inline_reduction_into_game(self.reduction, self.get_right_game(), self.scheme, self.schemeName, self.target_experiment.get_target_game(), self.target_scheme, self.target_experiment.get_adversary(), game_name = "G")
    def advantage(self):
        return f"Advantage of reduction {utils.fqn(self.reduction)} in experiment {self.experiment.get_primitive_name()}.{self.experiment.get_experiment_name()} for {utils.typefqn(self.scheme)} scheme {self.schemeName}"

class RewritingStep(ProofStep):
    def __init__(self, rewrite_left: Type[Crypto.Game], rewrite_right: Type[Crypto.Game]):
        self.rewrite_left = rewrite_left
        self.rewrite_right = rewrite_right
    def get_left_game(self): return self.rewrite_left
    def get_left_src(self): return ast.unparse(utils.get_class_def(self.rewrite_left))
    def get_right_game(self): return self.rewrite_right
    def get_right_src(self): return ast.unparse(utils.get_class_def(self.rewrite_right))
    def advantage(self): return "0 (Rewriting step)"

class Proof():
    def __init__(self, scheme: Type[Crypto.Scheme], experiment: Crypto.Experiment):
        self.scheme = scheme
        self.experiment = experiment
        self.proof_steps: List[ProofStep] = list()
        self.proof_checked = "unchecked"

    def add_distinguishing_proof_step(self, reduction: Type[Crypto.Reduction], experiment: Crypto.DistinguishingExperiment, scheme: Type[Crypto.Scheme], schemeName: str, reverse_direction = False) -> None:
        """Add a distinguishing proof step for a reduction 'reduction' against the distinguishing security experiment 'experiment' for a scheme 'scheme'.
        If reverse_direction == False, the "left" and "right" sides of the game hopping proof are lined up with the get_left and get_right methods of the given distinguishing experiment, and are swapped if reverse_direction == True."""
        self.proof_steps.append(DistinguishingProofStep(reduction, experiment, scheme, schemeName, reverse_direction, self.experiment, self.scheme))

    def add_rewriting_proof_step(self, rewrite_left: Type[Crypto.Game], rewrite_right: Type[Crypto.Game]) -> None:
        """Add a rewriting proof step asserting (without computer verification) that the games rewrite_left and rewrite_right are equivalent to each other."""
        self.proof_steps.append(RewritingStep(rewrite_left, rewrite_right))

    def insert_simple_rewriting_proof_step_after(self, rewrites: Dict[str, str], gamenum: Optional[int] = None) -> None:
        """Add a rewriting step that's constructed by using string replacements as specified in rewrites. The string replacements will be applied to the *uncanonicalized* form of game gamenum (where gamenum is the currently last game, if unspecified). The effect of this will be to add a rewriting step of the form (left=copy_of_game_gamenum_unchanged, right=copy_of_game_gamenum_with_replacements) immediately after game gamenum."""
        if gamenum is None: gamenum = len(self.proof_steps)
        prev_game_src = self.get_game_src(gamenum)
        next_game_src = copy.copy(prev_game_src)
        for k in rewrites:
            next_game_src = next_game_src.replace(k, rewrites[k])
        self.proof_steps.insert(gamenum, RewritingStep(
            cast(Type[Crypto.Game], utils.get_class_def(prev_game_src)), 
            cast(Type[Crypto.Game], utils.get_class_def(next_game_src))))

    def insert_simple_rewriting_proof_step_before(self, rewrites: Dict[str, str], gamenum: Optional[int] = None) -> None:
        """Add a rewriting step that's constructed by using string replacements as specified in rewrites. The string replacements will be applied to the *uncanonicalized* form of game gamenum (where gamenum is the currently last game, if unspecified). However, this method works in "reverse" compared to insert_simple_rewriting_proof_step_after: the effect of this will be to add a rewriting step of the form (left=copy_of_game_gamenum_with_replacements, right=copy_of_game_gamenum_unchanged) immediately *before* game gamenum.  Note this means that this method must be called after gamenum has been added."""
        if gamenum is None: gamenum = len(self.proof_steps) - 1
        next_game_src = self.proof_steps[gamenum].get_left_src()
        prev_game_src = copy.copy(next_game_src)
        for k in rewrites:
            prev_game_src = prev_game_src.replace(k, rewrites[k])
        self.proof_steps.insert(gamenum, RewritingStep(
            cast(Type[Crypto.Game], utils.get_class_def(prev_game_src)),
            cast(Type[Crypto.Game], utils.get_class_def(next_game_src))))

    def get_game_src(self, gamenum: int, before_hop = True) -> str:
        if gamenum == 0 and before_hop: # use the original experiment
            if isinstance(self.experiment, Crypto.DistinguishingExperiment):
                return inlining.inline_scheme_into_game(self.scheme, self.experiment.get_left(), game_name = "G", adversary_package = self.experiment.get_primitive_name())
        elif 0 <= gamenum < len(self.proof_steps) and not(before_hop): # use the reduction inlined into the left side of its experiment
            step = self.proof_steps[gamenum]
            if isinstance(step, DistinguishingProofStep) or isinstance(step, RewritingStep):
                return step.get_left_src()
        elif 0 < gamenum <= len(self.proof_steps) and before_hop: # use the reduction inlined into the right side of its experiment
            step = self.proof_steps[gamenum - 1]
            if isinstance(step, DistinguishingProofStep) or isinstance(step, RewritingStep):
                return step.get_right_src()
        elif (gamenum == -1 or gamenum == len(self.proof_steps)) and not(before_hop): # use the final experiment
            if isinstance(self.experiment, Crypto.DistinguishingExperiment):
                return inlining.inline_scheme_into_game(self.scheme, self.experiment.get_right(), game_name = "G", adversary_package = self.experiment.get_primitive_name())
        raise NotImplementedError()

    def get_game_description(self, gamenum: int, before_hop = True) -> str:
        if gamenum == 0 and before_hop: # use the original experiment
            if isinstance(self.experiment, Crypto.DistinguishingExperiment):
                return f"game {utils.fqn(self.experiment.get_left())} with {utils.typefqn(self.scheme)} scheme {utils.fqn(self.scheme)} inlined"
        elif 0 <= gamenum < len(self.proof_steps) and not(before_hop): # use the reduction inlined into the left side of its experiment
            step = self.proof_steps[gamenum]
            if isinstance(step, DistinguishingProofStep):
                return f"reduction {utils.fqn(step.reduction)} inlined into game {utils.fqn(step.get_left_game())} for {utils.typefqn(step.scheme)} scheme {step.schemeName}"
            elif isinstance(step, RewritingStep):
                return "rewriting step before rewriting"
        elif 0 < gamenum <= len(self.proof_steps) and before_hop: # use the reduction inlined into the right side of its experiment
            step = self.proof_steps[gamenum - 1]
            if isinstance(step, DistinguishingProofStep):
                return f"reduction {utils.fqn(step.reduction)} inlined into game {utils.fqn(step.get_right_game())} for {utils.typefqn(step.scheme)} scheme {step.schemeName}"
            elif isinstance(step, RewritingStep):
                return "rewriting step after rewriting"
        elif (gamenum == -1 or gamenum == len(self.proof_steps)) and not(before_hop): # use the final experiment
            if isinstance(self.experiment, Crypto.DistinguishingExperiment):
                return f"game {utils.fqn(self.experiment.get_right())} with {utils.typefqn(self.scheme)} scheme {utils.fqn(self.scheme)} inlined"
        raise NotImplementedError()

    def check(self, print_hops=False, print_canonicalizations=False, print_diffs=True, show_call_graphs=False, abort_on_failure=True) -> bool:
        result = True
        self.proof_checked = "valid"
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

            if gamenum < len(self.proof_steps) and isinstance(self.proof_steps[gamenum], RewritingStep) and print_hops:
                step = self.proof_steps[gamenum]
                print(f"---- diff of rewriting step ----")
                utils.stringDiff(step.get_left_src(), step.get_right_src())

            if left_game_src_canonicalized != right_game_src_canonicalized:
                print("❌ canoncalizations are NOT equal")
                if print_diffs: utils.stringDiff(left_game_src_canonicalized, right_game_src_canonicalized)
                self.proof_checked = "invalid"
                result = False
                if abort_on_failure: return result
            else:
                print("✅ canoncalizations are equal")

        return result

    def advantage_bound(self) -> str:
        if self.proof_checked == "unchecked":
            raise ValueError("Cannot compute advantage bound, proof has not been checked")
        elif self.proof_checked == "invalid":
            raise ValueError("Cannot compute advantage bound, proof is not valid")
        lines = []
        lines.append(f"Advantage of adversary in experiment {self.experiment.get_primitive_name()}.{self.experiment.get_experiment_name()} for {utils.typefqn(self.scheme)} scheme {utils.fqn(self.scheme)}")
        lines.append("≤")
        for stepnum, step in enumerate(self.proof_steps):
            lines.append(step.advantage())
            if stepnum < len(self.proof_steps) - 1: lines.append("+")
        return "\n".join(lines)

    def tikz_figure(self):
        env = jinja2.Environment(
            loader=jinja2.PackageLoader("gamehop"),
            trim_blocks=True, # https://stackoverflow.com/questions/33775085/is-it-possible-to-change-the-default-double-curly-braces-delimiter-in-polymer
            block_start_string='≤%',
            block_end_string='%≥',
            variable_start_string='≤≤',
            variable_end_string='≥≥'
        )
        env.filters['classname'] = lambda value: utils.fqn(value)
        env.filters['type'] = lambda value: type(value).__name__
        env.filters['isinstance'] = lambda value, type_to_test: isinstance(value, eval(type_to_test))
        env.filters['texify'] = lambda value: value.replace('_', '\_')
        template = env.get_template("tikz_figure.tex")
        return template.render(proof=self)
