from typing import Tuple
import ast
import sys
import gamehop
from gamehop.primitives import Crypto, KEM, PKE
import stupiddoublePKE
from gamehop import gametests

PKEScheme = PKE.PKEScheme
PKEINDCPA_adversary = PKE.PKEINDCPA_adversary


#This reduction takes an adversary for stupiddoublepke and creates an adversary for pke1
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

#This reduction takes an adversary for stupiddoublepke and creates an adversary for pke2
class R12(PKE.PKEINDCPA_adversary):
    def __init__(self, adversary: PKE.PKEINDCPA_adversary, pke1: PKEScheme) -> None:
        self.adversary = adversary      # this is the adversary for pke2
        self.pke1 = pke1
    
    def setup(self, pke2: PKEScheme) -> None:        
        self.pke2 = pke2
        dummy = self.adversary.setup(self.pke2)
        return None
        
    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk2 = pk
        (self.pk1, self.sk1)  = self.pke1.KeyGen()
        pk_double = (self.pk1, self.pk2)
        (self.m0, self.m1) = self.adversary.challenge(pk_double)

        return (self.m0, self.m1)

    def guess(self, ct2: PKE.Ciphertext) -> Crypto.Bit:
        ct1 = self.pke1.Encrypt(self.pk1, self.m1)
        ct = (ct1, ct2)
        return self.adversary.guess(ct)

experiment = PKE.INDCPA
steps = [
    (PKE.INDCPA0, 'pke', stupiddoublePKE.Scheme),  
    (PKE.INDCPA0, 'adversary', R01),              
    (gametests.advantage, (PKE.INDCPA, 'pke1')),
    (PKE.INDCPA1, 'adversary', R01),             
    (PKE.INDCPA0, 'adversary', R12),            
    (gametests.advantage, (PKE.INDCPA, 'pke2')),
    (PKE.INDCPA1, 'adversary', R12),             
    (PKE.INDCPA1, 'pke', stupiddoublePKE.Scheme),  
]
