from typing import Dict, Tuple, Union

from . import Crypto
from .. import proofs

class Key(): pass

class KDFScheme(Crypto.Scheme):
    def KDF(self, k: Key, label: str, len: int) -> Crypto.ByteString: pass

class OTKDFsec_adversary(Crypto.Adversary):
    def setup(self, kdf: KDFScheme): pass
    def phase1(self) -> Tuple[Key, str, int]: pass
    def phase2(self, kk: Crypto.ByteString) -> Crypto.Bit: pass

class OTKDFsec(proofs.DistinguishingExperiment):
    def main0(self, scheme: KDFScheme, adversary: OTKDFsec_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (k, label, len) = adversary.phase1()
        kk = scheme.KDF(k, label, len)
        r = adversary.phase2(kk)
        return r
    def main1(self, scheme: KDFScheme, adversary: OTKDFsec_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (k, label, len) = adversary.phase1()
        kk = Crypto.UniformlySample(Crypto.ByteString)
        r = adversary.phase2(kk)
        return r
