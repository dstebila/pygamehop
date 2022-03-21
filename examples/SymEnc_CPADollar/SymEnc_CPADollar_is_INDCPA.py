import os
from typing import Callable, Generic, Tuple, Type, TypeVar

from gamehop.primitives import Crypto, SymEnc
from gamehop.proofs2 import Proof

from SE import SE, InnerSymEnc, SK, MSG, CT

# Theorem: SE is IND-CPA-secure if InnerSymEnc is IND-CPADollar-secure.
proof = Proof(SE, SymEnc.INDCPA)

class R1(Crypto.Reduction,
    Generic[SK, MSG, CT],
    SymEnc.INDCPADollar_Adversary[SK, MSG, CT]
):
    def __init__(self, Scheme: Type[SymEnc.SymEncScheme[SK, MSG, CT]], inner_adversary: SymEnc.INDCPA_Adversary[SK, MSG, CT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the INDCPA adversary
    def run(self, o_ctxt: Callable[[MSG], CT]) -> Crypto.Bit:
        self.io_ctxt = o_ctxt
        r = self.inner_adversary.run(self.o_eavesdrop)
        return r
    def o_eavesdrop(self, msg_L: MSG, msg_R: MSG) -> CT:
        ctxt = self.io_ctxt(msg_L)
        return ctxt

proof.add_distinguishing_proof_step(R1, SymEnc.INDCPADollar, InnerSymEnc, "InnerSymEnc")

class R2(Crypto.Reduction,
    Generic[SK, MSG, CT],
    SymEnc.INDCPADollar_Adversary[SK, MSG, CT]
):
    def __init__(self, Scheme: Type[SymEnc.SymEncScheme[SK, MSG, CT]], inner_adversary: SymEnc.INDCPA_Adversary[SK, MSG, CT]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the INDCPA adversary
    def run(self, o_ctxt: Callable[[MSG], CT]) -> Crypto.Bit:
        self.io_ctxt = o_ctxt
        r = self.inner_adversary.run(self.o_eavesdrop)
        return r
    def o_eavesdrop(self, msg_L: MSG, msg_R: MSG) -> CT:
        ctxt = self.io_ctxt(msg_R)
        return ctxt

proof.add_distinguishing_proof_step(R2, SymEnc.INDCPADollar, InnerSymEnc, "InnerSymEnc", reverse_direction = True)

assert proof.check(print_hops=True, print_canonicalizations=True, print_diffs=True, abort_on_failure=True)
print("Theorem:")
print(proof.advantage_bound())

with open(os.path.join('examples', 'SymEnc_CPADollar', 'SymEnc_CPADollar_is_INDCPA.tex'), 'w') as fh:
    fh.write(proof.tikz_figure())
