from typing import Any, Sized, Tuple, Union

from . import Crypto
from .. import proofs

class Message(Sized): pass

class OTPScheme(Crypto.Scheme): pass

class OTIND_adversary(Crypto.Adversary):
    def setup(self, otp: OTPScheme): pass
    def challenge(self) -> Tuple[Message, Message]: pass
    def guess(self, ct: Crypto.BitString) -> Crypto.Bit: pass

class OTIND(proofs.DistinguishingExperiment):
    def main0(self, scheme: OTPScheme, adversary: OTIND_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (m0, m1) = adversary.challenge()
        k = Crypto.BitString.uniformly_random(len(m0))
        ct = k ^ m0
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret
    def main1(self, scheme: OTPScheme, adversary: OTIND_adversary) -> Crypto.Bit:
        dummy = adversary.setup(scheme)
        (m0, m1) = adversary.challenge()
        k = Crypto.BitString.uniformly_random(len(m1))
        ct = k ^ m1
        r = adversary.guess(ct)
        ret = r if len(m0) == len(m1) else Crypto.Bit(0)
        return ret
