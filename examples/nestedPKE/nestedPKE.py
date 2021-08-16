from typing import NewType, Tuple, Union, Generic, Set

from gamehop.primitives import Crypto
from gamehop.primitives.PKE import PKEScheme

class PKE1(PKEScheme): pass
class PKE2(PKEScheme): pass

class NestedPKE(PKEScheme):
    class PublicKey(PKEScheme.PublicKey):
        def __init__(self, pk1: PKE1.PublicKey, pk2: PKE2.PublicKey):
            self.pk1 = pk1
            self.pk2 = pk2
    class SecretKey(PKEScheme.SecretKey):
        def __init__(self, sk1: PKE1.SecretKey, sk2: PKE2.SecretKey):
            self.sk1 = sk1
            self.sk2 = sk2
    @staticmethod
    def KeyGen():
        (pk1, sk1) = PKE1.KeyGen()
        (pk2, sk2) = PKE2.KeyGen()
        return (NestedPKE.PublicKey(pk1, pk2), NestedPKE.SecretKey(sk1, sk2))
    @staticmethod
    def Encrypt(pk, msg):
        ct1 = PKE1.Encrypt(pk.pk1, msg)
        ct2 = PKE2.Encrypt(pk.pk2, ct1)
        return ct2
    @staticmethod
    def Decrypt(sk, ct):
        pt2 = PKE2.Decrypt(sk.sk2, ct)
        if pt2 == Crypto.Reject: r = Crypto.Reject
        else: r = PKE1.Decrypt(sk.sk1, pt2)
        return r
