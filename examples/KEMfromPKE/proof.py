from typing import Tuple
import ast
import sys
import gamehop
from gamehop.primitives import Crypto, KEM, PKE
import KEMfromPKE
from gamehop import gametests

debugging = True

KEMScheme = KEM.KEMScheme[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext, PKE.Message, Crypto.Reject]
KEMINDCPA_adversary = KEM.KEMINDCPA_adversary[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext, PKE.Message, Crypto.Reject]

PKEScheme = PKE.PKEScheme
PKEINDCPA_adversary = PKE.PKEINDCPA_adversary



# Game hop from G0 to G1
# Proven by constructing reduction from distinguishing G0 and G1 to distinguishing PKE.INDCPA0 from PKE.INDCPA1
class R01(PKE.PKEINDCPA_adversary):
    def __init__(self, kem_adversary: KEMINDCPA_adversary) -> None:
        self.kem_adversary = kem_adversary

    def setup(self, pke2: PKEScheme) -> None:
        self.pke = pke2

    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk = pk

        self.ss0 = Crypto.UniformlySample(self.pke.MessageSet)
        self.ct0 = self.pke.Encrypt(pk, self.ss0)
        self.m0 = self.ss0

        self.ss1 = Crypto.UniformlySample(self.pke.MessageSet)
        self.ct1 = self.pke.Encrypt(pk, self.ss1)
        self.m1 = self.ss1

        return (self.m0, self.m1)

    def guess(self, ct: PKE.Ciphertext) -> Crypto.Bit:
        return self.kem_adversary.guess(self.pk, ct, self.m0)


experiment = KEM.INDCPA
steps = [
    (KEM.INDCPA_real, [('kem', KEMfromPKE.Scheme)]),
    (PKE.INDCPA0, 'adversary', R01),
    (gametests.advantage, (PKE.INDCPA, 'pke1')),
    (PKE.INDCPA1, 'adversary', R01),
    (KEM.INDCPA_random, 'kem', KEMfromPKE.Scheme)
]
