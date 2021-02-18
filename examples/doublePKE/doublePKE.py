from typing import Tuple, Union, Generic, Set

from gamehop.primitives import Crypto, PKE

PKEScheme = PKE.PKEScheme

class Scheme(PKEScheme):
    def __init__(self, pke1: PKEScheme, pke2: PKEScheme) -> None:
        self.pke1 = pke1
        self.pke2 = pke2
    def KeyGen(self) :
        (pk1, sk1) = self.pke1.KeyGen()
        (pk2, sk2) = self.pke2.KeyGen()
        return ((pk1, pk2), (sk1, sk2))
    def Encrypt(self, pk, msg):
        ct1 = self.pke1.Encrypt(pk[0], msg)
        ct2 = self.pke2.Encrypt(pk[1], ct1)
        return ct2
    def Decrypt(self, sk, ct):
        pt2 = self.pke2.Decrypt(sk[1], ct)
        if pt2 == Crypto.Reject:
            return Crypto.Reject
        pt1 = self.pke1.Decrypt(sk[0], pt2)
        return pt1

# Advantage is MIN(adv(PKE1), adv(PKE2))
# two separate proofs, each showing an upper bound on the advantage
# Replace one PKE with a random function
