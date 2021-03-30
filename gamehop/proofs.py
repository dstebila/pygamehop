from abc import ABC
from typing import List

from .primitives import Crypto

class Experiment(ABC): pass
class DistinguishingExperiment(Experiment):
    def main0(self, scheme, adversary) -> Crypto.Bit: pass
    def main1(self, scheme, adversary) -> Crypto.Bit: pass
class GuessingExperiment(Experiment):
    def main(self, scheme, adversary, bit: Crypto.Bit) -> Crypto.Bit: pass

class Proof():
    def __init__(self, experiment: Experiment, scheme, adversary):
        self.experiment = experiment
        self.scheme = scheme
        self.adversary = adversary
        self.proofSteps: List[dict] = []
    def addDistinguishingProofStep(self, experiment: DistinguishingExperiment, scheme, reduction, reverseDirection=False):
        self.proofSteps.append({
            'type': 'distinguishingProofStep',
            'experiment': experiment,
            'scheme': scheme,
            'reduction': reduction,
            'reverseDirection': reverseDirection
        })
    def check(self):
        return False
