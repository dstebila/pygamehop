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
        ct2 = self.pke2.Encrypt(pk2, msg)
        return (ct1, ct2)
    def Decrypt(self, sk, ct):
        (ct1, ct2) = ct
        (sk1, sk2) = sk
        pt2 = self.pke2.Decrypt(sk2, ct2)
        pt1 = self.pke1.Decrypt(sk1, ct1)
        if pt2 == Crypto.Reject or pt1 == Crypto.Reject or pt1 != pt2:
            r = Crypto.Reject
        else: 
            r = pt1
        return r
