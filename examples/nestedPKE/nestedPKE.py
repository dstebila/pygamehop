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
        pk1, pk2 = pk
        ct1 = self.pke1.Encrypt(pk1, msg)
        ct2 = self.pke2.Encrypt(pk2, ct1)
        return ct2
    def Decrypt(self, sk, ct):
        pt2 = self.pke2.Decrypt(sk[1], ct)
        if pt2 == Crypto.Reject:
            r = Crypto.Reject
        else:
            r = self.pke1.Decrypt(sk[0], pt2)
        return r
