from typing import Tuple
import ast
import sys
import gamehop
from gamehop.primitives import Crypto, KEM, PKE
import stupiddoublePKE
from gamehop import gametests

PKEScheme = PKE.PKEScheme
PKEINDCPA_adversary = PKE.PKEINDCPA_adversary

class R01(PKE.PKEINDCPA_adversary):
    def __init__(self, adversary: PKE.PKEINDCPA_adversary) -> None:
        self.adversary = adversary      # this is the adversary for pke1
    
    def setup(self, pke1: PKEScheme, pke2: PKEScheme) -> None:
        self.pke1 = pke1
        self.pke2 = pke2

    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk1 = pk[0]
        self.pk2 = pk[1]        
        (self.m0, self.m1) = self.adversary.challenge(self.pk1)

        return (self.m0, self.m1)

    def guess(self, ct: PKE.Ciphertext) -> Crypto.Bit:
        (ct1, ct2) = ct
        return self.kem_adversary.guess(ct1)

experiment = PKE.INDCPA
steps = [
    (PKE.INDCPA0, '', stupiddoublePKE.Scheme)
]
    

#
# G0 : original game b = 0 (PKE.INDCPA for StupidDoublePKE)
#  | P(G0 = 1) - P(G1 = 1) | < Adv(pke1)  (R01 implements PKE2 itself, uses PKE1 challenger)
# G1 : message0 for ct1 replaced with message 1
# | P(G1 = 1) - P(G2 = 1) | < Adv(pke2)
# G2 : message0 for ct2 replaced with constant message 1  =  original game b = 1
#
# R01 simulates the StupidDoublePKE challenger to the StupidDoublePKE adversary, and uses its answers to distinguish in the PKE.INDCPA game for PKE1.
#
# R01 takes PKE2 and SDPKE adversary
