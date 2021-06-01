from typing import Callable, Tuple, Union

from . import Crypto
from .. import proofs

class Key(): pass

class KDFScheme(Crypto.Scheme):
    def KDF(self, k: Key, label: str, len: int) -> Crypto.ByteString: pass

class KDFsec_adversary(Crypto.Adversary):
    def setup(self, kdf: KDFScheme): pass
    def run(self, o_eval: Callable[[str, int], Crypto.ByteString]) -> Crypto.Bit: pass

class KDFsec(proofs.DistinguishingExperiment):
    def main0(self, scheme: KDFScheme, adversary: KDFsec_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        k = Crypto.UniformlySample(Key)
        o_eval = lambda label, length: scheme.KDF(k, label, length)
        r = adversary.run(o_eval)
        return r
    def main1(self, scheme: KDFScheme, adversary: KDFsec_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        # TODO: turn into a lazily sampled random function
        o_eval = lambda label, length: Crypto.UniformlySample(Crypto.ByteString)
        r = adversary.run(o_eval)
        return r
