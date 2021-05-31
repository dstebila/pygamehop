from typing import Any, Tuple, Union

from . import Crypto
from .. import proofs

class Message(): pass

class OTPScheme(Crypto.Scheme): pass

class OTIND_adversary(Crypto.Adversary):
    def setup(self, otp: OTPScheme): pass
    def challenge(self) -> Tuple[Message, Message]: pass
    def guess(self, ct: Crypto.ByteString) -> Crypto.Bit: pass

class OTIND(proofs.DistinguishingExperiment):
    def main0(self, scheme: OTPScheme, adversary: OTIND_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (m0, m1) = adversary.challenge()
        k = Crypto.UniformlySample(Crypto.ByteString)
        ct = k ^ m0
        r = adversary.guess(ct)
        return r
    def main1(self, scheme: OTPScheme, adversary: OTIND_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (m0, m1) = adversary.challenge()
        k = Crypto.UniformlySample(Crypto.ByteString)
        ct = k ^ m1
        r = adversary.guess(ct)
        return r
