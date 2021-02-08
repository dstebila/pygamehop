from typing import Tuple
import ast
import sys
import gamehop
from gamehop.primitives import Crypto, KEM, PKE
import KEMfromPKE

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


G0 = gamehop.inline(KEM.INDCPA_real, KEMfromPKE.Scheme, arg='kem')
H0 = gamehop.inline(PKE.INDCPA0, R01, arg = 'adversary')
gamehop.assertEqual(G0, H0, debugging=debugging)

H1 = gamehop.inline(PKE.INDCPA1, R01, arg = 'adversary')
G1 = gamehop.inline(KEM.INDCPA_random, KEMfromPKE.Scheme, arg='kem')
gamehop.assertEqual(H1, G1, debugging=debugging)

print(gamehop.advantage(H0, H1, PKEScheme, "INDCPA"))
