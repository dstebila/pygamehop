import os
from typing import Callable, Generic, Optional, Tuple, Type, TypeVar

from gamehop import lists
from gamehop.primitives import Crypto, SymEnc, MAC
from gamehop.proofs2 import Proof

from EncryptThenMAC import EncryptThenMAC, InnerSymEnc, InnerMAC, SEK, MSG, CT, MACK, TAG

# Theorem: EncryptThenMAC[InnerSymEnc, InnerMAC] is IND-CCA-secure if InnerSymEnc is IND-CPA-secure and InnerMAC is EUF-CMA.
proof = Proof(EncryptThenMAC, SymEnc.INDCCA)

class R1(Crypto.Reduction,
    Generic[SEK, MSG, CT, MACK, TAG],
    MAC.EUFCMA_Adversary[MACK, CT, TAG] # This is an EUFCMA adversary for InnerMAC
):
    def __init__(self, Scheme: Type[MAC.MACScheme[MACK, CT, TAG]], inner_adversary: SymEnc.INDCCA_Adversary[Tuple[SEK, MACK], MSG, Tuple[CT, TAG]]):
        self.Scheme = Scheme
        self.inner_adversary = inner_adversary # this is the EncryptThenMAC adversary
    def run(self, o_gettag: Callable[[CT], TAG], o_checktag: Callable[[CT, TAG], bool]) -> Crypto.Bit:
        self.io_gettag = o_gettag
        self.io_checktag = o_checktag
        self.sek = InnerSymEnc.uniformKey()
        self.challenges = lists.new_empty_list()
        r = self.inner_adversary.run(self.o_eavesdrop, self.o_decrypt)
        return r
    def o_eavesdrop(self, msg_L: MSG, msg_R: MSG) -> Tuple[CT, TAG]:
        ct = InnerSymEnc.Encrypt(self.sek, msg_L)
        tag = self.io_gettag(ct)
        ctxt = (ct, tag)
        self.challenges = lists.append_item(self.challenges, ctxt)
        return ctxt
    def o_decrypt(self, ctxt: Tuple[CT, TAG]) -> Optional[MSG]:
        (ct, tag) = ctxt
        if ctxt in self.challenges: ret = None
        elif not(self.io_checktag(ct, tag)): ret = None
        else: ret = InnerSymEnc.Decrypt(self.sek, ct)
        return ret

proof.add_distinguishing_proof_step(R1, MAC.EUFCMA, InnerMAC, "InnerMAC")

assert proof.check(print_hops=True, print_canonicalizations=True, print_diffs=True, abort_on_failure=True)
print("Theorem:")
print(proof.advantage_bound())

with open(os.path.join('examples', 'EncryptThenMAC', 'EncryptThenMAC_is_INDCCA.tex'), 'w') as fh:
    fh.write(proof.tikz_figure())
