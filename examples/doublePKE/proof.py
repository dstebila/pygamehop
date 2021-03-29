from typing import Tuple, Any
import ast
import sys
import gamehop
from gamehop.primitives import Crypto, KEM, PKE
import doublePKE
from gamehop import gametests
PKEScheme = PKE.PKEScheme
PKEINDCPA_adversary = PKE.PKEINDCPA_adversary
PublicKey = PKE.PublicKey
SecretKey = PKE.SecretKey
Message = PKE.Message
Ciphertext = PKE.Ciphertext


# Challenger runs pke1, reduction runs pke2, adversary attacks DoublePKE(pke1, pke2)
class R01_1(PKEINDCPA_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, pke2: PKEScheme) -> None:
        self.adversary = adversary      # this is the adversary for doublepke
        self.pke2 = pke2

    def setup(self, pke1: PKEScheme) -> None:
        self.pke1 = pke1
        dummy = self.adversary.setup(PKEScheme(self.pke1, self.pke2))
        return None

    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk1 = pk
        (self.pk2, self.sk2)  = self.pke2.KeyGen()
        pk_double = (self.pk1, self.pk2)
        (m0, m1) = self.adversary.challenge(pk_double)
        return (m0, m1)

    def guess(self, ct: PKE.Ciphertext) -> Crypto.Bit:
        ct2 = self.pke2.Encrypt(self.pk2, ct)
        return self.adversary.guess(ct2)


# Challenger runs pke2, reduction runs pke1, adversary attacks DoublePKE(pke1, pke2)
class R01_2(PKEINDCPA_adversary):
    def __init__(self, adversary: PKEINDCPA_adversary, pke1: PKEScheme) -> None:
        self.adversary = adversary      # this is the adversary for doublepke
        self.pke1 = pke1

    def setup(self, pke2: PKEScheme) -> None:
        self.pke2 = pke2
        dummy = self.adversary.setup(PKEScheme(self.pke1, self.pke2))
        return None

    def challenge(self, pk: PKE.PublicKey) -> Tuple[PKE.Message, PKE.Message]:
        self.pk2 = pk
        (self.pk1, self.sk1)  = self.pke1.KeyGen()
        pk_double = (self.pk1, self.pk2)
        (m0, m1) = self.adversary.challenge(pk_double)
        i0 = self.pke1.Encrypt(self.pk1, m0)
        i1 = self.pke1.Encrypt(self.pk1, m1)
        return (i0, i1)

    def guess(self, ct: PKE.Ciphertext) -> Crypto.Bit:
        return self.adversary.guess(ct)


proofs = [
    (PKE.INDCPA,
    [
        (PKE.INDCPA0, 'pke', doublePKE.Scheme),  # game 0 for the experiment we care about.  Reduction produces pt = Decrypt(Encrypt(m))
        (PKE.INDCPA0, 'adversary', R01_2),               # reduction to INDCPA for pke2.
        (gametests.advantage, (PKE.INDCPA, 'pke2')),
        (PKE.INDCPA1, 'adversary', R01_2),
        (PKE.INDCPA1, 'pke', doublePKE.Scheme)
    ]),
    (PKE.INDCPA,
    [
        (PKE.INDCPA0, 'pke', doublePKE.Scheme),  # game 0 for the experiment we care about.  Reduction produces pt = Decrypt(Encrypt(m))
        (PKE.INDCPA0, 'adversary', R01_1),               # reduction to INDCPA for pke2.
        (gametests.advantage, (PKE.INDCPA, 'pke1')),
        (PKE.INDCPA1, 'adversary', R01_1),
        (PKE.INDCPA1, 'pke', doublePKE.Scheme)
    ])
]
