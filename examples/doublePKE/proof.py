from typing import Tuple
import ast
import sys
import gamehop
from gamehop.primitives import Crypto, KEM, PKE
import doublePKE
from gamehop import gametests
PKEScheme = PKE.PKEScheme
PKEINDCPA_adversary = PKE.PKEINDCPA_adversary

class R01(PKE.PKEINDCPA_adversary):
    def __init__(self, adversary: PKE.PKEINDCPA_adversary, pke2: PKEScheme) -> None:
        self.adversary = adversary      # this is the adversary for pke1
        self.pke2 = pke2
    
    def setup(self, pke1: PKEScheme) -> None:        
        self.pke1 = pke1
        dummy = self.adversary.setup(self.pke1)
        return None
        
    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk1 = pk
        (self.pk2, self.sk2)  = self.pke2.KeyGen()
        pk_double = (self.pk1, self.pk2)
        (self.m0, self.m1) = self.adversary.challenge(pk_double)

        return (self.m0, self.m1)

    def guess(self, ct1: PKE.Ciphertext) -> Crypto.Bit:
        ct2 = self.pke2.Encrypt(self.pk2, self.m0)
        ct = (ct1, ct2)
        return self.adversary.guess(ct)




experiment = PKE.INDCPA
steps = [
    (PKE.INDCPA0, 'pke', doublePKE.Scheme),  
    (PKE.INDCPA0, 'adversary', R01),
    
    (PKE.INDCPA0, 'adversary', R01),
    (PKE.INDCPA1, 'pke', doublePKE.Scheme), 
]


# Advantage is MIN(adv(PKE1), adv(PKE2))
# two separate proofs, each showing an upper bound on the advantage
# Replace one PKE with a random function
