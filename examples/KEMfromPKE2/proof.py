from typing import Tuple
import ast
import sys
import gamehop
from gamehop.primitives import Crypto, KEM2, PKE
import KEMfromPKE
from gamehop import gametests

debugging = True

KEMScheme = KEM2.KEMScheme[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext, PKE.Message, Crypto.Reject]
KEMINDCPA_adversary = KEM2.KEMINDCPA_adversary[PKE.PublicKey, PKE.SecretKey, PKE.Ciphertext, PKE.Message, Crypto.Reject]

PKEScheme = PKE.PKEScheme
PKEINDCPA_adversary = PKE.PKEINDCPA_adversary



# Game hop from G0 to G1
# Proven by constructing reduction from distinguishing G0 and G1 to distinguishing PKE.INDCPA0 from PKE.INDCPA1
class R01(PKE.PKEINDCPA_adversary):
    def __init__(self, kem_adversary: KEMINDCPA_adversary) -> None:
        self.kem_adversary = kem_adversary

    def setup(self, pke2: PKEScheme) -> None:
        self.pke = pke2
        return None

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

# have to do the gamehopping manually since the driver doesn't support all this yet

import gamehop.verification
import gamehop.inlining

# make game 0 by inlining b==0 and kem
INDCPA_real = gamehop.inlining.inline_argument(KEM2.INDCPA_b, 'b', 0)
game0 = gamehop.inlining.inline_class(INDCPA_real, 'kem', KEMfromPKE.Scheme)

# inline reduction R01 into PKE.INDCPA0
r01_left = gamehop.inlining.inline_class(PKE.INDCPA0, 'adversary', R01)

# game0 and r01_left should be equivalent
# doesn't work yet, but should work once devtests/collapseIfExpr is resolved
can_game0 = gamehop.verification.canonicalize_function(game0)
can_r01_left = gamehop.verification.canonicalize_function(r01_left)
print(can_game0)
print(can_r01_left)
assert(can_game0 == can_r01_left)

# inline reduction R01 into PKE.INDCPA1
r01_right = gamehop.inlining.inline_class(PKE.INDCPA1, 'adversary', R01)

# make game 1 by inlining b==1 and kem
INDCPA_random = gamehop.inlining.inline_argument(KEM2.INDCPA_b, 'b', 1)
game1 = gamehop.inlining.inline_class(INDCPA_random, 'kem', KEMfromPKE.Scheme)

# game1 and r01_right should be equivalent
# doesn't work yet, but should work once devtests/collapseIfExpr is resolved
can_game1 = gamehop.verification.canonicalize_function(game1)
can_r01_right = gamehop.verification.canonicalize_function(r01_right)
print(can_game1)
print(can_r01_right)
assert(can_game1 == can_r01_right)
